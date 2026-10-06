"""Independent ALL-step moving-tetrahedral geometry/momentum/volume readback.

No constructor imports. Different spatial quadrature, direct Jacobian inverse,
two-point time Gauss instead of producer Simpson, separately assembled mass.
Failed/preliminary controls remain rejected; low global error is not acceptance.
"""
from itertools import combinations, product
import argparse
import hashlib
import json
import math
from pathlib import Path
import time
import numpy as np


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def reference_data():
    roots, weights = np.polynomial.legendre.leggauss(6); roots = (roots+1)/2; weights = weights/2
    points = []; w = []
    for i, j, k in product(range(6), repeat=3):
        a, b, c = roots[i], roots[j], roots[k]
        y = (1-a)*b; z = (1-a)*(1-b)*c
        points.append([1-a-y-z, a, y, z]); w.append(weights[i]*weights[j]*weights[k]*(1-a)**2*(1-b))
    return np.array(points), np.array(w)


def reference_basis(bary):
    gradients = np.array([[-1, -1, -1], [1, 0, 0], [0, 1, 0], [0, 0, 1]], float)
    n = np.zeros((len(bary), 10)); d = np.zeros((len(bary), 10, 3))
    for i in range(4):
        n[:, i] = 2*bary[:, i]**2-bary[:, i]
        d[:, i] = np.outer(4*bary[:, i]-1, gradients[i])
    for index, (i, j) in enumerate(combinations(range(4), 2), 4):
        n[:, index] = 4*bary[:, i]*bary[:, j]
        d[:, index] = 4*(np.outer(bary[:, i], gradients[j])+np.outer(bary[:, j], gradients[i]))
    return n, d


def metric(positions, cells, d):
    jac = np.einsum('qib,tia->tqab', d, positions[cells])
    det = np.linalg.det(jac)
    if np.any(det <= 0):
        raise ValueError('Independent curved map inverted at quadrature')
    inverse = np.linalg.inv(jac)
    physical_grad = np.einsum('qib,tqba->tqia', d, inverse)
    return det, physical_grad


def assemble_B(x, cells, pressure_cells, bary, d, weights, pressure_nodes):
    det, grad = metric(x, cells, d)
    local = np.einsum('q,tq,qi,tqja->tija', weights, det, bary, grad, optimize=True)
    result = np.zeros((pressure_nodes, x.size))
    for ci, ids in enumerate(cells):
        velocity_ids = (3*ids[:, None]+np.arange(3)).ravel()
        result[np.ix_(pressure_cells[ci], velocity_ids)] += local[ci].reshape(4, 30)
    return result


def bernstein_data():
    alpha = [p for p in product(range(4), repeat=4) if sum(p) == 3]; lattice = np.array(alpha, float)/3
    matrix = np.zeros((20, 20))
    for i, l in enumerate(lattice):
        for j, powers in enumerate(alpha):
            matrix[i, j] = math.factorial(3)/math.prod(math.factorial(k) for k in powers)*math.prod(l[k]**powers[k] for k in range(4))
    return lattice, matrix


def check(error, tolerance, name):
    if not np.isfinite(error) or error > tolerance:
        raise ValueError(f'Independent {name} failed: {error}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--audit', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    audit = json.loads(args.audit.read_text()); pins = {str(args.audit.resolve()): digest(args.audit),
        str(Path(__file__).resolve()): digest(__file__), **audit['dependency_sha256'], **audit['outputs_sha256']}
    if any(digest(p) != sha for p, sha in pins.items()):
        raise ValueError('Pinned moving trajectory changed')
    bary, weights = reference_data(); N, d = reference_basis(bary); cert_lattice, cert_matrix = bernstein_data(); _, dc = reference_basis(cert_lattice)
    time_nodes = [.5-.5/np.sqrt(3), .5+.5/np.sqrt(3)]; results = []; started = time.perf_counter()
    for row in audit['runs']:
        arrays = {k: np.load(p, allow_pickle=False) for k, p in row['arrays'].items()}
        poses, us, ps, times = (arrays[k] for k in ('positions', 'velocities', 'pressures', 'times'))
        cells = arrays['cells']; pcells = arrays['pressure_cells']; fixed = arrays['fixed']; free = ~fixed.ravel()
        if len(poses) != row['completed_steps']+1 or len(us) != len(poses) or len(ps) != len(poses):
            raise ValueError('Declared ALL-step trajectory coverage changed')
        det0, _ = metric(poses[0], cells, d); scalar_mass = np.zeros((poses.shape[1], poses.shape[1]))
        local_mass = 1000*np.einsum('q,tq,qi,qj->tij', weights, det0, N, N)
        for ci, ids in enumerate(cells):
            scalar_mass[np.ix_(ids, ids)] += local_mass[ci]
        mass_error = float(np.max(np.abs(scalar_mass-arrays['scalar_material_mass'])))
        check(mass_error, 1e-10, 'initial material quadrature mass')
        force = scalar_mass.sum(axis=1)[:, None]*[0., 0., -9.80665]
        initial_volume = float(np.sum(weights*det0)); initial_cell_volumes = np.sum(weights*det0, axis=1)
        energy0 = float(np.sum(us[0]*(scalar_mass@us[0]))/2-np.sum(poses[0]*force))
        cert0, _ = metric(poses[0], cells, dc); coeff0 = np.linalg.solve(cert_matrix, cert0.T).T
        maximum = dict(mass_matrix_error=mass_error, kinematic_error_m=0., weak_flux_error_m3_s=0.,
            momentum_error=0., volume_error_m3=0., cell_volume_error_m3=0., energy_error_j=0.,
            density_bound_difference=0., minimum_bernstein_jacobian=float(coeff0.min()), density_error_bound=0.)
        for step in range(1, len(poses)):
            old, x, old_u, u, p = poses[step-1], poses[step], us[step-1], us[step], ps[step]
            dt = float(times[step]-times[step-1]); midpoint = (old_u+u)/2
            check(abs(dt-row['dt_s']), 1e-16, 'physical time step')
            error = float(np.max(np.abs(x-old-dt*midpoint))); check(error, 2e-12, 'material kinematics')
            maximum['kinematic_error_m'] = max(maximum['kinematic_error_m'], error)
            Bbar = sum(assemble_B(old+tau*(x-old), cells, pcells, bary, d, weights, len(p)) for tau in time_nodes)/2
            residual = Bbar@midpoint.ravel(); error = float(np.max(np.abs(residual))); check(error, 2e-11, 'original pressure rows')
            maximum['weak_flux_error_m3_s'] = max(maximum['weak_flux_error_m3_s'], error)
            momentum = scalar_mass@(u-old_u)-dt*force-dt*(Bbar.T@p).reshape(u.shape)
            error = float(np.max(np.abs(momentum.ravel()[free]))); check(error, 4e-8, 'gravity pressure momentum')
            maximum['momentum_error'] = max(maximum['momentum_error'], error)
            if not np.array_equal(x[fixed], poses[0][fixed]) or not np.array_equal(u[fixed], np.zeros_like(u[fixed])):
                raise ValueError('Exact stationary planar wall contact changed')
            det, physical_grad = metric(x, cells, d); volume = float(np.sum(weights*det)); cellvol = np.sum(weights*det, axis=1)
            error = abs(volume-initial_volume); check(error, 1e-10, 'global swept volume')
            maximum['volume_error_m3'] = max(maximum['volume_error_m3'], error)
            cell_error = float(np.max(np.abs(cellvol-initial_cell_volumes)))
            maximum['cell_volume_error_m3'] = max(maximum['cell_volume_error_m3'], cell_error)
            if row['pressure_mode'] == 'discontinuous_p1':
                check(cell_error, 1e-10, 'local material volume')
            energy = float(np.sum(u*(scalar_mass@u))/2-np.sum(x*force)); error = abs(energy-energy0)
            check(error, 1e-8, 'mechanical energy'); maximum['energy_error_j'] = max(maximum['energy_error_j'], error)
            cert, _ = metric(x, cells, dc); coeff = np.linalg.solve(cert_matrix, cert.T).T
            minimum = float(coeff.min()); check(max(0., -minimum), 0., 'Bernstein map positivity')
            maximum['minimum_bernstein_jacobian'] = min(maximum['minimum_bernstein_jacobian'], minimum)
            ratio = coeff0/coeff; lower, upper = float(ratio.min()), float(ratio.max())
            maximum['density_error_bound'] = max(maximum['density_error_bound'], abs(lower-1), abs(upper-1))
            proof = row['proofs'][step-1]
            bound_error = max(abs(lower-proof['bernstein_density_ratio_lower']), abs(upper-proof['bernstein_density_ratio_upper']))
            check(bound_error, 2e-10, 'whole-cell density coefficient bounds')
            maximum['density_bound_difference'] = max(maximum['density_bound_difference'], bound_error)
            if step % 20 == 0:
                print('INDEPENDENT_MOVING', row['label'], step, row['completed_steps'], maximum, flush=True)
        passed = row['failure'] is None and maximum['density_error_bound'] <= audit['fixed_preliminary_density_allowance']
        if passed != row['preliminary_motion_gate_passed']:
            raise ValueError('Independent preliminary/rejection classification disagrees')
        results.append(dict(label=row['label'], all_completed_steps_checked=row['completed_steps'],
            tetrahedra=len(cells), maximum=maximum, preliminary_motion_gate_passed=passed,
            producer_failure_preserved=row['failure'], accepted=False))
    if any(digest(p) != sha for p, sha in pins.items()):
        raise ValueError('Independent moving qualifier changed data')
    result = dict(complete=True, accepted=False, dependency_sha256=pins, runs=results,
        construction_helpers_imported=False, total_seconds=time.perf_counter()-started,
        scope='Independent EVERY saved step / whole tetrahedral stencil kinematics, mass, momentum, space-time pressure, volume, energy, planar contact and bounded density. Preliminary motion gates only, not pressure stability/flow convergence/feature/animation acceptance.')
    with args.output.open('x') as stream:
        json.dump(result, stream, indent=2); stream.write('\n')


if __name__ == '__main__':
    main()
