"""Independent every-step cubic material readback by monomial interpolation.

No construction imports: Vandermonde basis, nine-point Gauss, direct inverse,
two-point time Gauss, separately assembled material mass and determinant bounds.
"""
import argparse
import hashlib
from itertools import combinations, product
import json
import math
from pathlib import Path
import time
import numpy as np


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def nodes(degree):
    corners = [tuple(degree if i == j else 0 for i in range(4)) for j in range(4)]
    return np.array(corners+[a for a in product(range(degree+1), repeat=4) if sum(a) == degree and a not in corners], float)/degree


def reference_data():
    roots, w = np.polynomial.legendre.leggauss(9); roots = (roots+1)/2; w = w/2
    bary = []; weights = []
    for i, j, k in product(range(9), repeat=3):
        a = roots[i]; b = (1-a)*roots[j]; c = (1-a)*(1-roots[j])*roots[k]
        bary.append([1-a-b-c, a, b, c]); weights.append(w[i]*w[j]*w[k]*(1-a)**2*(1-roots[j]))
    return np.array(bary), np.array(weights)


def polynomial_basis(bary, interpolation_nodes, degree):
    powers = [a for a in product(range(degree+1), repeat=3) if sum(a) <= degree]
    xi = interpolation_nodes[:, 1:]; x = bary[:, 1:]
    V = np.column_stack([np.prod(xi**a, axis=1) for a in powers])
    coefficients = np.linalg.solve(V, np.eye(len(powers)))
    values = np.column_stack([np.prod(x**a, axis=1) for a in powers])
    derivative = np.zeros((len(x), len(powers), 3))
    for ni, alpha in enumerate(powers):
        for axis in range(3):
            if alpha[axis]:
                exponent = list(alpha); exponent[axis] -= 1
                derivative[:, ni, axis] = alpha[axis]*np.prod(x**exponent, axis=1)
    return values@coefficients, np.einsum('qia,ij->qja', derivative, coefficients)


def metric(x, cells, d):
    J = np.einsum('qib,tia->tqab', d, x[cells]); determinant = np.linalg.det(J)
    if np.any(determinant <= 0):
        raise ValueError('Independent cubic map has nonpositive sampled Jacobian')
    grad = np.einsum('qib,tqba->tqia', d, np.linalg.inv(J))
    return determinant, grad


def divergence(x, cells, pressure_cells, q, d, weights, pressure_nodes):
    det, grad = metric(x, cells, d)
    local = np.einsum('q,tq,qi,tqja->tija', weights, det, q, grad, optimize=True)
    result = np.zeros((pressure_nodes, x.size))
    for ci, ids in enumerate(cells):
        dofs = (3*ids[:, None]+np.arange(3)).ravel()
        result[np.ix_(pressure_cells[ci], dofs)] += local[ci].reshape(pressure_cells.shape[1], -1)
    return result


def bernstein_certificate():
    bary = nodes(6); alpha = np.rint(bary*6).astype(int)
    matrix = np.array([[math.factorial(6)/math.prod(math.factorial(int(p)) for p in a)
                       *math.prod(float(l[i])**int(a[i]) for i in range(4)) for a in alpha] for l in bary])
    return bary, matrix


def check(error, allowance, label):
    if not np.isfinite(error) or error > allowance:
        raise ValueError(f'Independent cubic {label}: {error} > {allowance}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--audit', type=Path, required=True); parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    audit = json.loads(args.audit.read_text())
    pins = {str(args.audit.resolve()): digest(args.audit), str(Path(__file__).resolve()): digest(__file__),
            **audit['dependency_sha256'], **audit['outputs_sha256']}
    if any(digest(p) != sha for p, sha in pins.items()):
        raise ValueError('Cubic candidate inputs changed')
    bary, weights = reference_data(); N, d = polynomial_basis(bary, nodes(3), 3)
    cert_points, cert_matrix = bernstein_certificate(); _, dc = polynomial_basis(cert_points, nodes(3), 3)
    p2_nodes = np.array([*np.eye(4), *[(np.eye(4)[a]+np.eye(4)[b])/2 for a, b in combinations(range(4), 2)]])
    q2, _ = polynomial_basis(bary, p2_nodes, 2)
    time_nodes = [.5-.5/np.sqrt(3), .5+.5/np.sqrt(3)]; runs = []; started = time.perf_counter()
    for row in audit['runs']:
        arrays = {k: np.load(p, allow_pickle=False) for k, p in row['arrays'].items()}
        poses, us, ps, times = (arrays[k] for k in ('positions', 'velocities', 'pressures', 'times'))
        cells = arrays['cells']; pcells = arrays['pressure_cells']; fixed = arrays['fixed']; free = ~fixed.ravel()
        q = bary if row['pressure_degree'] == 1 else q2
        if len(poses) != row['completed_steps']+1 or len(us) != len(poses) or len(ps) != len(poses):
            raise ValueError('Cubic ALL-step declared coverage differs')
        det0, _ = metric(poses[0], cells, d); mass = np.zeros((poses.shape[1], poses.shape[1]))
        local = 1000*np.einsum('q,tq,qi,qj->tij', weights, det0, N, N)
        for ci, ids in enumerate(cells):
            mass[np.ix_(ids, ids)] += local[ci]
        mass_error = float(np.max(np.abs(mass-arrays['scalar_material_mass']))); check(mass_error, 1e-10, 'material mass')
        force = mass.sum(axis=1)[:, None]*[0., 0., -9.80665]
        volume0 = float(np.sum(weights*det0)); cellvol0 = np.sum(weights*det0, axis=1)
        energy0 = float(np.sum(us[0]*(mass@us[0]))/2-np.sum(poses[0]*force))
        cert0, _ = metric(poses[0], cells, dc); coeff0 = np.linalg.solve(cert_matrix, cert0.T).T
        maximum = dict(mass_matrix_error=mass_error, kinematic_error_m=0., weak_flux_error_m3_s=0.,
            free_momentum_error=0., volume_error_m3=0., cell_volume_error_m3=0., energy_error_j=0.,
            density_bound_difference=0., bounded_density_error=0., minimum_bernstein_jacobian=float(coeff0.min()),
            maximum_absolute_pressure_coefficient_pa=0., maximum_absolute_sampled_pressure_pa=0.)
        for step in range(1, len(poses)):
            old, x, old_u, u, p = poses[step-1], poses[step], us[step-1], us[step], ps[step]
            dt = float(times[step]-times[step-1]); mid_u = (old_u+u)/2
            check(abs(dt-row['dt_s']), 2e-16, 'step time')
            e = float(np.max(np.abs(x-old-dt*mid_u))); check(e, 2e-12, 'kinematics'); maximum['kinematic_error_m'] = max(maximum['kinematic_error_m'], e)
            B = sum(divergence(old+tau*(x-old), cells, pcells, q, d, weights, len(p)) for tau in time_nodes)/2
            e = float(np.max(np.abs(B@mid_u.ravel()))); check(e, 2e-11, 'original pressure moments'); maximum['weak_flux_error_m3_s'] = max(maximum['weak_flux_error_m3_s'], e)
            momentum = mass@(u-old_u)-dt*force-dt*(B.T@p).reshape(u.shape)
            e = float(np.max(np.abs(momentum.ravel()[free]))); check(e, 4e-8, 'gravity/pressure momentum'); maximum['free_momentum_error'] = max(maximum['free_momentum_error'], e)
            if not np.array_equal(x[fixed], poses[0][fixed]) or not np.array_equal(u[fixed], np.zeros_like(u[fixed])):
                raise ValueError('Cubic normal wall contact changed')
            det, _ = metric(x, cells, d); volume = float(np.sum(weights*det)); cellvol = np.sum(weights*det, axis=1)
            e = abs(volume-volume0); check(e, 1e-10, 'global volume'); maximum['volume_error_m3'] = max(maximum['volume_error_m3'], e)
            e = float(np.max(np.abs(cellvol-cellvol0))); check(e, 1e-10, 'ALL material-cell volumes'); maximum['cell_volume_error_m3'] = max(maximum['cell_volume_error_m3'], e)
            energy = float(np.sum(u*(mass@u))/2-np.sum(x*force)); e = abs(energy-energy0); check(e, 1e-8, 'energy'); maximum['energy_error_j'] = max(maximum['energy_error_j'], e)
            cert, _ = metric(x, cells, dc); coeff = np.linalg.solve(cert_matrix, cert.T).T
            if np.min(coeff) <= 0:
                raise ValueError('Independent whole-cell cubic certificate is not positive')
            maximum['minimum_bernstein_jacobian'] = min(maximum['minimum_bernstein_jacobian'], float(coeff.min()))
            ratio = coeff0/coeff; lower, upper = float(ratio.min()), float(ratio.max())
            maximum['bounded_density_error'] = max(maximum['bounded_density_error'], abs(lower-1), abs(upper-1))
            proof = row['proofs'][step-1]; e = max(abs(lower-proof['bernstein_density_ratio_lower']), abs(upper-proof['bernstein_density_ratio_upper']))
            check(e, 2e-10, 'degree-six density bounds'); maximum['density_bound_difference'] = max(maximum['density_bound_difference'], e)
            maximum['maximum_absolute_pressure_coefficient_pa'] = max(maximum['maximum_absolute_pressure_coefficient_pa'], float(np.max(np.abs(p))))
            maximum['maximum_absolute_sampled_pressure_pa'] = max(maximum['maximum_absolute_sampled_pressure_pa'], float(np.max(np.abs(q@p[pcells].T))))
            if step % 10 == 0:
                print('INDEPENDENT_CUBIC', row['label'], step, row['completed_steps'], maximum, flush=True)
        passed = row['failure'] is None and row['completed_steps'] == row['requested_steps'] and maximum['bounded_density_error'] <= audit['fixed_preliminary_density_allowance']
        if passed != row['preliminary_motion_gate_passed']:
            raise ValueError('Independent cubic rejection/preliminary classification differs')
        runs.append(dict(label=row['label'], all_completed_steps_checked=row['completed_steps'],
            maximum=maximum, preliminary_motion_gate_passed=passed, producer_failure_preserved=row['failure'], accepted=False))
    if any(digest(p) != sha for p, sha in pins.items()):
        raise ValueError('Independent cubic readback changed evidence')
    with args.output.open('x') as stream:
        json.dump(dict(complete=True, accepted=False, dependency_sha256=pins, runs=runs,
            construction_helpers_imported=False, total_seconds=time.perf_counter()-started,
            scope='Independent EVERY saved cubic step, full stencil material/pressure/geometry readback. No full feature/pressure stability/refinement/animation acceptance.'), stream, indent=2)
        stream.write('\n')


if __name__ == '__main__':
    main()
