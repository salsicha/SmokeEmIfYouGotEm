"""Independent Eulerian modal readback of actual curved top surfaces.

Integrates the physical projected surface area, not nodal least squares or
display triangle chords. Two spatial quadratures. This 0.4 s closed-tank
control is not a through-flow standing wave or a full-period frequency test.
"""
import argparse
import hashlib
import json
from collections import defaultdict
from itertools import combinations, product
from pathlib import Path
import numpy as np


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def top_faces(vertex_cells, cells, initial):
    owners = defaultdict(list)
    for ci, tet in enumerate(vertex_cells):
        for opposite in range(4):
            corners = [j for j in range(4) if j != opposite]
            if opposite % 2:
                corners[1], corners[2] = corners[2], corners[1]
            owners[tuple(sorted(int(tet[j]) for j in corners))].append((ci, corners))
    faces = []
    for entries in owners.values():
        if len(entries) != 1:
            continue
        ci, corners = entries[0]
        ids = cells[ci, corners]; xyz = initial[ids]
        if np.max(np.abs(xyz[:, 2]-(.5+.02*np.cos(np.pi*xyz[:, 0])))) < 1e-12:
            faces.append((ci, corners))
    if not faces:
        raise ValueError('Actual material top-boundary coverage required')
    return faces


def triangle_data(order):
    roots, weights = np.polynomial.legendre.leggauss(order)
    roots = (roots+1)/2; weights = weights/2
    lambdas = []; w = []
    for i, j in product(range(order), repeat=2):
        a, b = roots[i], roots[j]
        lambdas.append([1-a-(1-a)*b, a, (1-a)*b]); w.append(weights[i]*weights[j]*(1-a))
    return np.array(lambdas), np.array(w)


def mode_readback(poses, cells, faces, order):
    triangle, weights = triangle_data(order); out = []; areas = []; min_orientation = np.inf
    for pose in poses:
        gram = np.zeros((4, 4)); rhs = np.zeros(4); area = 0.
        for ci, corners in faces:
            bary = np.zeros((len(weights), 4)); gradients = np.zeros((4, 2))
            bary[:, corners] = triangle
            gradients[corners] = [[-1., -1.], [1., 0.], [0., 1.]]
            N = np.zeros((len(weights), 10)); d = np.zeros((len(weights), 10, 2))
            for j in range(4):
                N[:, j] = bary[:, j]*(2*bary[:, j]-1)
                d[:, j] = (4*bary[:, j]-1)[:, None]*gradients[j]
            for j, (a, b) in enumerate(combinations(range(4), 2), 4):
                N[:, j] = 4*bary[:, a]*bary[:, b]
                d[:, j] = 4*(bary[:, a, None]*gradients[b]+bary[:, b, None]*gradients[a])
            xyz = N@pose[cells[ci]]
            tangent = np.einsum('qib,ia->qab', d, pose[cells[ci]])
            orientation = tangent[:, 0, 0]*tangent[:, 1, 1]-tangent[:, 1, 0]*tangent[:, 0, 1]
            min_orientation = min(min_orientation, float(orientation.min()))
            if np.any(orientation <= 0):
                raise ValueError('Curved free surface overturns: modal height readback no longer applicable')
            measure = weights*orientation
            basis = np.column_stack([np.ones(len(weights)), *[np.cos(k*np.pi*xyz[:, 0]) for k in (1, 2, 3)]])
            gram += np.einsum('q,qi,qj->ij', measure, basis, basis)
            rhs += np.einsum('q,qi,q->i', measure, basis, xyz[:, 2]-.5)
            area += measure.sum()
        if abs(area-.6) > 2e-12:
            raise ValueError('Projected top domain differs from the actual 1 x .6 m tank')
        out.append(np.linalg.solve(gram, rhs)); areas.append(area)
    return np.array(out), areas, min_orientation


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ('audit', 'qualified', 'output'):
        parser.add_argument('--'+key, type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    audit, qualified = (json.loads(p.read_text()) for p in (args.audit, args.qualified))
    pins = {str(args.audit.resolve()): digest(args.audit), str(args.qualified.resolve()): digest(args.qualified),
            str(Path(__file__).resolve()): digest(__file__), **qualified['dependency_sha256']}
    if any(digest(p) != sha for p, sha in pins.items()):
        raise ValueError('Independent trajectory qualification changed')
    requested_times = np.arange(21)*.02; rows = []
    omega = float(np.sqrt(9.80665*np.pi*np.tanh(np.pi*.5)))
    for run in audit['runs']:
        if run['pressure_mode'] != 'discontinuous_p1':
            continue
        proof = next(r for r in qualified['runs'] if r['label'] == run['label'])
        if not proof['preliminary_motion_gate_passed'] or proof['all_completed_steps_checked'] != run['requested_steps']:
            raise ValueError('Every local refinement must be independently checked')
        arrays = {key: np.load(run['arrays'][key], allow_pickle=False) for key in ('positions', 'times', 'vertex_cells', 'cells')}
        indices = [int(np.argmin(np.abs(arrays['times']-t))) for t in requested_times]
        if np.max(np.abs(arrays['times'][indices]-requested_times)) > 1e-12:
            raise ValueError('Actual matching saved times required')
        faces = top_faces(arrays['vertex_cells'], arrays['cells'], arrays['positions'][0])
        lower, _, _ = mode_readback(arrays['positions'][indices], arrays['cells'], faces, 8)
        higher, areas, orientation = mode_readback(arrays['positions'][indices], arrays['cells'], faces, 12)
        difference = float(np.max(np.abs(higher-lower)))
        if difference > 1e-10:
            raise ValueError('Eulerian modal spatial quadrature not verified')
        reference = .02*np.cos(omega*requested_times)
        rows.append(dict(label=run['label'], actual_physical_times_s=requested_times.tolist(),
            height_cosine_modes_m=higher.tolist(), top_boundary_curved_faces=len(faces),
            maximum_modal_quadrature_difference_m=difference, projected_top_area_m2=areas,
            minimum_sampled_positive_projected_jacobian=orientation,
            linear_small_amplitude_20mm_reference_m=reference.tolist(),
            maximum_mode1_linear_comparison_error_m=float(np.max(np.abs(higher[:, 1]-reference))), accepted=False))
    coarse_fast, coarse_slow, finer = (next(r for r in rows if r['label'] == label)
        for label in ('local-n2-dt004', 'local-n2-dt002', 'local-n3-dt002'))
    time_difference = float(np.max(np.abs(np.array(coarse_fast['height_cosine_modes_m'])-coarse_slow['height_cosine_modes_m'])))
    space_difference = float(np.max(np.abs(np.array(coarse_slow['height_cosine_modes_m'])-finer['height_cosine_modes_m'])))
    if any(digest(p) != sha for p, sha in pins.items()):
        raise ValueError('Observable analysis changed actual trajectories')
    result = dict(complete=True, accepted=False, dependency_sha256=pins, runs=rows,
        maximum_matching_time_refinement_modal_difference_m=time_difference,
        maximum_matching_spatial_refinement_modal_difference_m=space_difference,
        linear_reference_omega_rad_s=omega,
        linear_reference_source='https://web.mit.edu/fluids-modules/www/potential_flows/LecturesHTML/lec19bu/node4.html',
        linear_reference_assumptions='Small-amplitude inviscid gravity motion, flat .5 m depth, fundamental k=pi over 1 m. Finite amplitude and interpolated initial shapes are NOT exact analytic matches.',
        scope='Independent actual curved Eulerian surface observable and time/space differences. Short closed-tank slosh, not full-period frequency/pressure stability/convergence or through-flow feature acceptance.')
    with args.output.open('x') as stream:
        json.dump(result, stream, indent=2); stream.write('\n')
    print('MOVING_SURFACE_OBSERVABLES', time_difference, space_difference, flush=True)


if __name__ == '__main__':
    main()
