"""Research current-wave and finite-amplitude qualification histories.

Preserves the existing four-wavelength/0.4m/s Airy benchmark and the existing
96m, four-second, 0.45m-amplitude solitary-wave comparison at 0.5/0.25m.
The SGN solitary wave is exact for standard SGN, not rational SGN, and its
nonzero tails are truncated by the periodic domain. No scene/native acceptance.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import total_depth_bank_replay as bank
from audit_total_depth_dispersion import solitary, peak_location
from audit_reconstructed_wave_motion import metrics
from reconstructed_pressure_adapter import reconstructed_pressure


def setup(kind, scale, model='rational_sgn'):
    if kind == 'current_wave':
        if scale not in (2., 4., 12.) or model != 'rational_sgn':
            raise ValueError('Use the original current-wave wavelengths and rational model')
        count, depth, amplitude, current = 128, 1.5, 1e-5, .4
        dx = 4*scale/count; x = (np.arange(count)+.5)*dx; k = 2*np.pi/scale
        speed = float(np.sqrt(9.81*np.tanh(k*depth)/k))
        eta = amplitude*np.cos(k*x); h = depth+eta
        initial = np.stack((h, current*h+speed*eta, np.zeros_like(h)), axis=-1)[None]
        return initial, dx, float(scale/(speed+current)), dict(kind=kind,
            wavelength_m=scale, cells_per_wavelength=32, wavelengths_in_domain=4,
            mean_depth_m=depth, amplitude_m=amplitude, current_mps=current,
            physical_speed_mps=speed+current, wavenumber_per_m=float(k), pressure_model=model)
    if kind != 'solitary' or scale not in (.5, .25) or model not in ('sgn', 'rational_sgn'):
        raise ValueError('Use the original solitary-wave spacings and named governing model')
    x = (np.arange(round(96/scale))+.5)*scale
    initial, speed = solitary(x, 0.)
    return initial[None], scale, 4., dict(kind=kind, cell_m=scale, domain_length_m=96.,
        mean_depth_m=1.5, amplitude_m=.45, amplitude_depth_ratio=.3, pressure_model=model,
        reference='Guermond et al. equation7.1, SGN solitary wave',
        exact_for_governing_equations=model == 'sgn', periodic_tail_truncation=True,
        reference_speed_mps=float(speed), initial_outer_cell_excess_depth_m=[
            float(initial[0, 0]-1.5), float(initial[-1, 0]-1.5)])


def compare(value, initial, dx, elapsed, specification):
    x = (np.arange(value.shape[1])+.5)*dx
    if specification['kind'] == 'current_wave':
        return metrics(value, specification['wavenumber_per_m']*x,
            specification['amplitude_m'], specification['mean_depth_m'],
            specification['physical_speed_mps'], specification['wavenumber_per_m'], elapsed)
    exact, speed = solitary(x, elapsed)
    return dict(elapsed_s=float(elapsed),
        relative_surface_l1_difference=float(np.sum(abs(value[0, :, 0]-exact[:, 0]))/np.sum(exact[:, 0]-1.5)),
        peak_amplitude_ratio=float((value[0, :, 0].max()-1.5)/.45),
        relative_peak_speed_difference=float((peak_location(value[0, :, 0], x, dx)
            -peak_location(initial[0, :, 0], x, dx))/(speed*elapsed)-1) if elapsed > 0 else None,
        momentum_change_per_width_m3ps=float(np.sum(value[0, :, 1]-initial[0, :, 1])*dx),
        exact_for_governing_equations=specification['exact_for_governing_equations'])


def run(kind, scale, model, emit):
    initial, dx, seconds, specification = setup(kind, scale, model)
    original = initial.copy(); initial.flags.writeable = False
    checkpoints = []
    def checkpoint(value, stats):
        comparison = compare(value, initial, dx, stats['elapsed_s'], specification)
        checkpoints.append(comparison)
        emit(dict(event='physical_history_checkpoint', specification=specification,
            comparison=comparison, statistics=stats))
    result = dict(specification=specification, requested_seconds=seconds, completed=False,
        initial_state_sha256=hashlib.sha256(initial.tobytes()).hexdigest(), checkpoints=checkpoints)
    emit(dict(event='physical_history_start', **result))
    try:
        with reconstructed_pressure():
            final, stats = bank.advance(initial, np.zeros(initial.shape[:2]), dx, seconds,
                max_trials=10000, second_order=True, periodic=True, dispersive=True,
                pressure_model=model, pressure_interpolation='depth_weighted',
                pressure_formulation='kinematic', pressure_bed_slope='geometry',
                shoreline_limiter='unscaled', progress_every_seconds=seconds/4, on_checkpoint=checkpoint)
        result.update(completed=bool(stats['elapsed_s'] == seconds), statistics=stats,
            final=compare(final, initial, dx, stats['elapsed_s'], specification),
            pressure_residual_check_passed=bool(stats['pressure_solver']['worst_relative_residual'] < 2e-5))
        if kind == 'current_wave':
            result['linear_motion_check_passed'] = bool(result['completed']
                and result['pressure_residual_check_passed'] and len(checkpoints) == 4
                and all(c['linear_check_passed'] for c in checkpoints))
    except (ValueError, FloatingPointError, bank.ReplayExhausted, bank.ReplayInvalidRate) as error:
        final = getattr(error, 'state', original)
        result.update(error=str(error), diagnostics=getattr(error, 'diagnostics', {}),
            pressure_residual_check_passed=False)
    if not np.array_equal(initial, original): raise AssertionError('Initial state was modified')
    result['final_state_sha256'] = hashlib.sha256(final.tobytes()).hexdigest()
    emit(dict(event='physical_history_result', **result))
    return final, result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--case', choices=('current_wave', 'solitary'), required=True)
    args = parser.parse_args()
    cases = ([('current_wave', w, 'rational_sgn') for w in (2., 4., 12.)]
        if args.case == 'current_wave' else [('solitary', dx, model)
        for model in ('sgn', 'rational_sgn') for dx in (.5, .25)])
    progress_path = args.report.with_suffix('.progress.jsonl')
    state_paths = [args.report.with_suffix(f'.case-{i}.npy') for i in range(len(cases))]
    if any(p.exists() for p in [args.report, progress_path, *state_paths]): raise FileExistsError(args.report)
    names = ('audit_reconstructed_physical_history.py', 'audit_total_depth_dispersion.py',
        'audit_reconstructed_wave_motion.py', 'reconstructed_pressure_adapter.py',
        'reconstructed_nonlinear_pressure.py', 'reconstructed_acceleration_system.py',
        'directional_pressure_geometry.py', 'reconstructed_pressure_geometry.py',
        'reconstructed_pressure_rates.py', 'pressure_cut_face_reference.py',
        'total_depth_bank_replay.py', 'adaptive_hydrostatic_precision.py',
        'continuous_shoreline_reconstruction.py', 'total_depth_nonlinear_pressure.py',
        'pressure_cg_range_reference.py', 'breaking_front_reference.py',
        'finite_depth_pressure_reference.py', 'total_depth_pressure.py', 'detail_nonlinear_flux.py')
    paths = [Path(__file__).with_name(name) for name in names]
    hashes = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    results = []
    with progress_path.open('x') as output:
        def emit(value):
            row = json.dumps(value, allow_nan=False)
            output.write(row+'\n'); output.flush(); print(row, flush=True)
        for index, case in enumerate(cases):
            state, result = run(*case, emit)
            with state_paths[index].open('xb') as target: np.save(target, state, allow_pickle=False)
            result['retained_state_path'] = str(state_paths[index]); results.append(result)
    unchanged = all(hashlib.sha256(Path(p).read_bytes()).hexdigest() == h for p, h in hashes.items())
    report = dict(schema='raftsim.reconstructed_physical_history.v1', scope=__doc__,
        numpy_version=np.__version__, implementation_hashes=hashes, implementation_unchanged=unchanged,
        scene_accepted=False, native_qualified=False, nonlinear_physics_qualified=False, results=results)
    encoded = json.dumps(report, indent=2, allow_nan=False)
    with args.report.open('x') as output: output.write(encoded)
    if not unchanged or any(not r['completed'] or not r['pressure_residual_check_passed']
            or (args.case == 'current_wave' and not r.get('linear_motion_check_passed')) for r in results):
        raise SystemExit(1)


if __name__ == '__main__': main()
