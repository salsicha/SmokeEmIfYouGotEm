"""Isolated actual-RHS preconditioner A/B, not history/native qualification."""
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
from reconstructed_symmetric_sweep_reference import SymmetricSweepSystem


def compare(system, rhs, original, original_stats, scheme):
    rhs_before = rhs.copy()
    begin = time.perf_counter(); sweep = SymmetricSweepSystem(system)
    build_seconds = time.perf_counter()-begin
    begin = time.perf_counter(); result, stats = sweep.solve(rhs)
    solve_seconds = time.perf_counter()-begin
    direct = spsolve(assembled_matrix(system), rhs.ravel()).reshape(rhs.shape)
    if not np.array_equal(rhs, rhs_before): raise AssertionError('Original RHS changed')
    return dict(length=system.length, actual_nonlinear_rhs=True, vector_unknowns=rhs.size,
        original_scheme=scheme, original_stats=original_stats, symmetric_sweep_stats=stats,
        original_relative_solution_error=float(np.linalg.norm(original-direct)/np.linalg.norm(direct)),
        sweep_relative_solution_error=float(np.linalg.norm(result-direct)/np.linalg.norm(direct)),
        preconditioner_build_seconds=build_seconds, solve_seconds=solve_seconds,
        stored_triangular_nonzeros=sweep.lower.nnz+sweep.upper.nnz,
        unchanged_pressure_gate_passed=bool(stats['relative_residual'] < 2e-5))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--case', choices=('solitary', 'wet_2d', 'captured'), default='solitary')
    parser.add_argument('--input', type=Path)
    args = parser.parse_args()
    if args.report.exists(): raise FileExistsError(args.report)
    if (args.case == 'captured') != (args.input is not None):
        raise ValueError('Captured case requires its explicit original source; other cases do not')
    names = ('audit_reconstructed_symmetric_sweep.py', 'reconstructed_symmetric_sweep_reference.py',
        'diagnose_reconstructed_pressure_convergence.py', 'audit_total_depth_dispersion.py',
        'reconstructed_pressure_adapter.py', 'reconstructed_nonlinear_pressure.py',
        'reconstructed_acceleration_system.py', 'directional_pressure_geometry.py',
        'reconstructed_pressure_geometry.py', 'reconstructed_pressure_rates.py',
        'pressure_cut_face_reference.py', 'total_depth_bank_replay.py',
        'adaptive_hydrostatic_precision.py', 'continuous_shoreline_reconstruction.py',
        'total_depth_nonlinear_pressure.py', 'pressure_cg_range_reference.py',
        'finite_depth_pressure_reference.py', 'detail_nonlinear_flux.py',
        'total_depth_pressure.py', 'breaking_front_reference.py', 'audit_live_moving_owner.py',
        'audit_live_temporal_evolution.py')
    paths = [Path(__file__).with_name(name) for name in names]
    hashes = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    dx = .125
    source_metadata = {}
    kwargs = dict(periodic=True)
    if args.case == 'solitary':
        x = (np.arange(round(96/dx))+.5)*dx
        initial, _ = solitary(x, 0.); initial = initial[None]
        bed = np.zeros(initial.shape[:2])
    elif args.case == 'wet_2d':
        y, x = np.meshgrid((np.arange(16)+.5)*2*np.pi/16,
            (np.arange(24)+.5)*2*np.pi/24, indexing='ij')
        h = 1.5+.2*np.cos(x)*np.cos(y)
        bed = .3*np.sin(x)+.2*np.cos(y)
        initial = np.stack((h, h*.4*np.sin(y), h*.3*np.cos(x)), axis=-1)
    else:
        from audit_live_moving_owner import source
        from audit_live_temporal_evolution import observations, boundary_provider
        data = args.input.read_bytes(); record = json.loads(data)
        if (record.get('schema') != 'raftsim.live_nonlinear_owner_audit.v1'
                or record.get('shoreline_limiter') != 'unscaled' or record['summary'][3] != 5):
            raise ValueError('Original unscaled captured owner required')
        source(record['observations'][0])  # Full zero-foam/source-state validation.
        a, b = observations(dict(schema='raftsim.live_temporal_boundary_inputs.v1',
            first=record['observations'][0], second=record['observations'][1]))
        initial, bed, dx = a['state'][..., :3].copy(), a['bed'], a['cell_meters']
        duration, boundary = boundary_provider(a, b)
        exterior, exterior_bed, trace = boundary(0., initial)
        kwargs = dict(periodic=False, breaking_model='hybrid_front',
            exterior=(exterior, exterior_bed), pressure_boundary=trace)
        source_metadata = dict(path=str(args.input), sha256=hashlib.sha256(data).hexdigest(),
            native_seconds=a['native_seconds'], next_native_seconds=b['native_seconds'],
            source_origin_meters=[a['origin_x'], a['origin_y']],
            original_boundary_bracket_seconds=duration)
    before = initial.copy(); initial.flags.writeable = bed.flags.writeable = False
    records = []
    with capture_systems(records), reconstructed_pressure():
        bank.rate(initial, bed, dx, second_order=True, **kwargs,
            dispersive=True, pressure_model='rational_sgn', pressure_interpolation='depth_weighted',
            pressure_formulation='kinematic', pressure_bed_slope='geometry', shoreline_limiter='unscaled')
    if not np.array_equal(initial, before): raise AssertionError('Original source changed')
    results = []
    for record in records:
        result = compare(*record); results.append(result)
        print(json.dumps(result, allow_nan=False), flush=True)
    if any(hashlib.sha256(Path(p).read_bytes()).hexdigest() != h for p, h in hashes.items()):
        raise RuntimeError('Implementation changed during audit')
    report = dict(schema='raftsim.reconstructed_symmetric_sweep.v1', scope=__doc__,
        implementation_hashes=hashes, source_case=args.case,
        source_scope=('Original first captured source and boundary bracket; not an evolved history'
            if args.case == 'captured' else 'Manufactured physical FV state, not measured river flow'),
        source_metadata=source_metadata,
        source_state_sha256=hashlib.sha256(initial.tobytes()).hexdigest(),
        source_bed_sha256=hashlib.sha256(bed.tobytes()).hexdigest(),
        scene_accepted=False, history_qualified=False, native_cost_qualified=False,
        all_pressure_checks_passed=all(r['unchanged_pressure_gate_passed'] for r in results), poles=results)
    encoded = json.dumps(report, indent=2, allow_nan=False)
    with args.report.open('x') as output: output.write(encoded)
    if not report['all_pressure_checks_passed']: raise SystemExit(1)


if __name__ == '__main__': main()
