"""Actual-RHS fixed-degree preconditioner comparison, no native promotion."""
import argparse
import hashlib
import json
from pathlib import Path
import time
import numpy as np
from scipy.sparse.linalg import spsolve
import total_depth_bank_replay as bank
from audit_total_depth_dispersion import solitary
from reconstructed_pressure_adapter import reconstructed_pressure
from diagnose_reconstructed_pressure_convergence import capture_systems, assembled_matrix
from reconstructed_polynomial_sweep_reference import PolynomialSweepSystem
from reconstructed_damped_polynomial_reference import DampedPolynomialSystem


def source_fields(case, path):
    if case == 'captured':
        from audit_live_moving_owner import source
        from audit_live_temporal_evolution import observations, boundary_provider
        data = path.read_bytes(); record = json.loads(data)
        if (record.get('schema') != 'raftsim.live_nonlinear_owner_audit.v1'
                or record.get('shoreline_limiter') != 'unscaled' or record['summary'][3] != 5):
            raise ValueError('Original unscaled captured owner required')
        source(record['observations'][0])
        a, b = observations(dict(schema='raftsim.live_temporal_boundary_inputs.v1',
            first=record['observations'][0], second=record['observations'][1]))
        state = a['state'][..., :3].copy(); duration, boundary = boundary_provider(a, b)
        exterior, exterior_bed, trace = boundary(0., state)
        return state, a['bed'], a['cell_meters'], dict(periodic=False,
            breaking_model='hybrid_front', exterior=(exterior, exterior_bed), pressure_boundary=trace), dict(
            path=str(path), sha256=hashlib.sha256(data).hexdigest(), native_seconds=a['native_seconds'],
            next_native_seconds=b['native_seconds'], original_boundary_bracket_seconds=duration,
            origin_meters=[a['origin_x'], a['origin_y']])
    if case == 'solitary':
        dx = .125; x = (np.arange(round(96/dx))+.5)*dx; state, _ = solitary(x, 0.)
        return state[None], np.zeros((1, len(x))), dx, dict(periodic=True), {}
    if case != 'wet_2d': raise ValueError('Unknown physical source')
    y, x = np.meshgrid((np.arange(16)+.5)*2*np.pi/16,
        (np.arange(24)+.5)*2*np.pi/24, indexing='ij')
    h = 1.5+.2*np.cos(x)*np.cos(y); bed = .3*np.sin(x)+.2*np.cos(y)
    return np.stack((h, h*.4*np.sin(y), h*.3*np.cos(x)), axis=-1), bed, .125, dict(periodic=True), {}


def compare(system, rhs, original, stats, scheme, *, family='triangular'):
    exact = spsolve(assembled_matrix(system), rhs.ravel()).reshape(rhs.shape)
    values = []
    for degree in (0, 1, 2, 4, 8):
        constructor = PolynomialSweepSystem if family == 'triangular' else DampedPolynomialSystem
        begin = time.perf_counter(); polynomial = constructor(system, degree)
        build_seconds = time.perf_counter()-begin
        begin = time.perf_counter(); solution, result = polynomial.solve(rhs)
        solve_seconds = time.perf_counter()-begin
        values.append(dict(degree=degree, stats=result, build_seconds=build_seconds,
            solve_seconds=solve_seconds, sparse_actions_per_preconditioner=(2 if family == 'triangular' else 1)*degree,
            stored_operator_nonzeros=(polynomial.lower if family == 'triangular' else polynomial.scaled).nnz,
            relative_solution_error=float(np.linalg.norm(solution-exact)/np.linalg.norm(exact)),
            unchanged_pressure_gate_passed=bool(result['relative_residual'] < 2e-5)))
    return dict(length=system.length, vector_unknowns=rhs.size, actual_nonlinear_rhs=True,
        original_scheme=scheme, original_stats=stats, candidates=values)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--case', choices=('solitary', 'wet_2d', 'captured'), required=True)
    parser.add_argument('--input', type=Path)
    parser.add_argument('--family', choices=('triangular', 'damped'), default='triangular')
    args = parser.parse_args()
    if args.report.exists(): raise FileExistsError(args.report)
    if (args.case == 'captured') != (args.input is not None): raise ValueError('Captured source path required only for captured case')
    names = ('audit_reconstructed_polynomial_sweep.py', 'reconstructed_polynomial_sweep_reference.py',
        'reconstructed_damped_polynomial_reference.py',
        'diagnose_reconstructed_pressure_convergence.py', 'audit_total_depth_dispersion.py',
        'reconstructed_pressure_adapter.py', 'reconstructed_nonlinear_pressure.py',
        'reconstructed_acceleration_system.py', 'directional_pressure_geometry.py',
        'reconstructed_pressure_geometry.py', 'reconstructed_pressure_rates.py',
        'pressure_cut_face_reference.py', 'total_depth_bank_replay.py',
        'adaptive_hydrostatic_precision.py', 'continuous_shoreline_reconstruction.py',
        'total_depth_nonlinear_pressure.py', 'pressure_cg_range_reference.py',
        'finite_depth_pressure_reference.py', 'detail_nonlinear_flux.py', 'total_depth_pressure.py',
        'breaking_front_reference.py', 'audit_live_moving_owner.py', 'audit_live_temporal_evolution.py')
    paths = [Path(__file__).with_name(name) for name in names]
    hashes = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    initial, bed, dx, kwargs, metadata = source_fields(args.case, args.input)
    before = initial.copy(); initial.flags.writeable = bed.flags.writeable = False
    records = []
    with capture_systems(records), reconstructed_pressure():
        bank.rate(initial, bed, dx, second_order=True, **kwargs, dispersive=True,
            pressure_model='rational_sgn', pressure_interpolation='depth_weighted',
            pressure_formulation='kinematic', pressure_bed_slope='geometry', shoreline_limiter='unscaled')
    if not np.array_equal(initial, before): raise AssertionError('Original input changed')
    results = []
    for record in records:
        result = compare(*record, family=args.family); results.append(result)
        print(json.dumps(result, allow_nan=False), flush=True)
    if any(hashlib.sha256(Path(p).read_bytes()).hexdigest() != h for p, h in hashes.items()):
        raise RuntimeError('Implementation changed during audit')
    report = dict(schema='raftsim.reconstructed_polynomial_sweep.v1', scope=__doc__,
        source_case=args.case, source_metadata=metadata, family=args.family,
        source_state_sha256=hashlib.sha256(initial.tobytes()).hexdigest(),
        source_bed_sha256=hashlib.sha256(bed.tobytes()).hexdigest(),
        implementation_hashes=hashes, scene_accepted=False, history_qualified=False,
        native_cost_qualified=False, poles=results)
    encoded = json.dumps(report, indent=2, allow_nan=False)
    with args.report.open('x') as output: output.write(encoded)
    if any(not c['unchanged_pressure_gate_passed'] for p in results for c in p['candidates'] if c['degree'] > 0):
        raise SystemExit(1)


if __name__ == '__main__': main()
