"""One-period Airy motion checks for the reconstructed research pressure model.

Independent linear physical reference, not native/scene/wetting acceptance.
Retains actual SSP-RK2, original unscaled FV, 120Hz maximum timestep and CFL.
No state resets, damping, adjusted forcing or shortened checkpoint timesteps.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import total_depth_bank_replay as bank
from reconstructed_pressure_adapter import reconstructed_pressure


def metrics(state, phase, amplitude, depth, speed, k, elapsed):
    carrier = np.exp(-1j*phase)
    initial_coefficient = np.sum(amplitude*np.cos(phase)*carrier)
    ratio = np.sum((state[0, :, 0]-depth)*carrier)/initial_coefficient
    reference = np.exp(-1j*k*speed*elapsed)
    relative = ratio/reference
    phase_error = float(abs(np.angle(relative))/(2*np.pi))
    amplitude_ratio = float(abs(ratio))
    return dict(elapsed_s=float(elapsed), phase_error_cycles=phase_error,
        amplitude_ratio=amplitude_ratio,
        # Retain the prior independent Airy audit's acceptance thresholds.
        linear_check_passed=phase_error < .03 and .9 < amplitude_ratio < 1.1)


def run(wavelength, cells, emit):
    depth, amplitude = 1.5, 1e-5
    dx = wavelength/cells; k = 2*np.pi/wavelength
    phase = k*(np.arange(cells)+.5)*dx
    speed = np.sqrt(9.81*np.tanh(k*depth)/k)
    seconds = float(wavelength/speed)
    eta = amplitude*np.cos(phase)
    initial = np.stack((depth+eta, speed*eta, np.zeros_like(eta)), axis=-1)[None]
    checkpoints = []
    def checkpoint(value, stats):
        result = metrics(value, phase, amplitude, depth, speed, k, stats['elapsed_s'])
        checkpoints.append(result)
        emit(dict(wavelength_m=wavelength, cells_per_wavelength=cells, **result, statistics=stats))
    result = dict(wavelength_m=wavelength, cells_per_wavelength=cells, mean_depth_m=depth,
        amplitude_m=amplitude, requested_seconds=float(seconds), completed=False, checkpoints=checkpoints)
    try:
        with reconstructed_pressure():
            final, stats = bank.advance(initial, np.zeros((1, cells)), dx, seconds,
                max_trials=10000, second_order=True, periodic=True, dispersive=True,
                pressure_model='rational_sgn', pressure_interpolation='depth_weighted',
                pressure_formulation='kinematic', pressure_bed_slope='geometry',
                shoreline_limiter='unscaled', progress_every_seconds=seconds/4, on_checkpoint=checkpoint)
        result.update(completed=bool(stats['elapsed_s'] == seconds), statistics=stats,
            final=metrics(final, phase, amplitude, depth, speed, k, stats['elapsed_s']))
        result['linear_check_passed'] = bool(result['completed'] and len(checkpoints) == 4
            and all(c['linear_check_passed'] for c in checkpoints)
            and stats['pressure_solver']['worst_relative_residual'] < 2e-5)
    except (ValueError, FloatingPointError, bank.ReplayExhausted, bank.ReplayInvalidRate) as error:
        result.update(error=str(error), diagnostics=getattr(error, 'diagnostics', {}), linear_check_passed=False)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    progress_path = args.report.with_suffix('.progress.jsonl')
    if args.report.exists() or progress_path.exists(): raise FileExistsError(args.report)
    names = ('audit_reconstructed_wave_motion.py', 'reconstructed_pressure_adapter.py',
        'reconstructed_nonlinear_pressure.py', 'reconstructed_acceleration_system.py',
        'directional_pressure_geometry.py', 'reconstructed_pressure_geometry.py',
        'reconstructed_pressure_rates.py', 'pressure_cut_face_reference.py',
        'total_depth_bank_replay.py', 'adaptive_hydrostatic_precision.py',
        'continuous_shoreline_reconstruction.py', 'total_depth_nonlinear_pressure.py',
        'pressure_cg_range_reference.py', 'breaking_front_reference.py',
        'finite_depth_pressure_reference.py', 'total_depth_pressure.py')
    paths = [Path(__file__).with_name(name) for name in names]
    hashes = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    with progress_path.open('x') as output:
        def emit(value):
            row = json.dumps(value, allow_nan=False)
            output.write(row+'\n'); output.flush(); print(row, flush=True)
        results = [run(w, 32, emit) for w in (2., 4., 12.)]
    unchanged = all(hashlib.sha256(Path(p).read_bytes()).hexdigest() == h for p, h in hashes.items())
    report = dict(schema='raftsim.reconstructed_wave_motion.v1', scope=__doc__,
        physical_reference='omega^2=g*k*tanh(k*h); MIT 2.20 lecture 20',
        scene_accepted=False, native_qualified=False, implementation_hashes=hashes,
        implementation_unchanged=unchanged, results=results,
        linear_motion_checks_passed=unchanged and all(r['linear_check_passed'] for r in results))
    encoded = json.dumps(report, indent=2, allow_nan=False)
    with args.report.open('x') as output: output.write(encoded)
    if not report['linear_motion_checks_passed']: raise SystemExit(1)


if __name__ == '__main__': main()
