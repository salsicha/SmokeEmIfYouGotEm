"""Stop a diagnostic continuation at its first accepted-state speed event.

The threshold only ends observation and saves the before/after states; it does
not cap or repair velocity, and the result is never a completed/accepted scene.
Reconstructed RK rates expose transport versus pressure at the event cell.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import total_depth_bank_replay as bank
from audit_detail_wave_regime import read_snapshot
from total_depth_bank_replay import advance, rate
from total_depth_nonlinear_pressure import depth_weights, depth_weight_rates, gradient, geometric_bed_slope, kinematic_terms


class SpeedEvent(RuntimeError):
    def __init__(self, previous, current, progress):
        self.previous, self.current, self.progress = previous, current, progress


def bed_slope_diagnostic(state, bed, dx, cell):
    original = bank.nonlinear_pressure_force
    captured = []
    def capture(*args, **kwargs):
        captured.append((args[4], kwargs['mass_rate'].copy()))
        return original(*args, **kwargs)
    options = dict(second_order=True, dispersive=True, pressure_model='rational_sgn',
        pressure_interpolation='depth_weighted', pressure_formulation='kinematic')
    try:
        bank.nonlinear_pressure_force = capture
        weighted_rate, _ = rate(state, bed, dx, **options)
    finally:
        bank.nonlinear_pressure_force = original
    fixed_rate, _ = rate(state, bed, dx, **options, pressure_bed_slope='geometry')
    hydro, _ = rate(state, bed, dx, second_order=True)
    pairs, ht = captured[0]; h = state[..., 0]
    u = np.divide(state[..., 1:], h[..., None], out=np.zeros_like(state[..., 1:]), where=h[..., None]>0)
    weights = depth_weights(h); slope = geometric_bed_slope(bed, dx)
    weighted_slope = gradient(bed, pairs, dx, weights)
    slope_rate = gradient(bed, pairs, dx, depth_weight_rates(h, ht))
    q, old_c, _ = kinematic_terms(h, bed, u, ht, pairs, dx, weights)
    _, fixed_c, _ = kinematic_terms(h, bed, u, ht, pairs, dx, weights, slope)
    return dict(weighted_bed_slope=weighted_slope[cell].tolist(), fixed_bed_slope=slope[cell].tolist(),
        weighted_bed_slope_time_derivative=slope_rate[cell].tolist(),
        fictitious_bottom_acceleration=float(np.dot(u[cell],slope_rate[cell])),
        quadratic=float(q[cell]), weighted_bottom_curvature=float(old_c[cell]), fixed_bottom_curvature=float(fixed_c[cell]),
        weighted_pressure_rate=(weighted_rate-hydro)[cell].tolist(), fixed_pressure_rate=(fixed_rate-hydro)[cell].tolist())


def dissect(previous, current, progress, bed, dx, bed_slope='weighted'):
    h = current[..., 0]
    velocity = np.divide(current[..., 1:], h[..., None], out=np.zeros_like(current[..., 1:]), where=h[..., None] > 0)
    yx = np.unravel_index(np.linalg.norm(velocity, axis=-1).argmax(), h.shape)
    options = dict(second_order=True, dispersive=True, pressure_model='rational_sgn',
        pressure_interpolation='depth_weighted', pressure_formulation='kinematic', pressure_bed_slope=bed_slope)
    first, _ = rate(previous, bed, dx, **options)
    stage = previous+progress['step_s']*first
    second, _ = rate(stage, bed, dx, **options)
    entries = []
    for name, state, derivative in [('previous', previous, first), ('stage', stage, second), ('accepted', current, None)]:
        cell = state[yx]
        value = dict(name=name, state=cell.tolist(), velocity=(cell[1:]/cell[0]).tolist() if cell[0]>0 else [0, 0])
        if derivative is not None:
            hydro, _ = rate(state, bed, dx, second_order=True)
            value.update(total_rate=derivative[yx].tolist(), hydrostatic_rate=hydro[yx].tolist(),
                pressure_rate=(derivative[yx]-hydro[yx]).tolist())
        entries.append(value)
    expected = .5*(previous+stage+progress['step_s']*second)
    return dict(cell_yx=list(map(int, yx)), bed_m=float(bed[yx]), stages=entries,
        reconstructed_update_max_error=float(abs(expected-current).max()),
        same_stage_bed_slope_comparison=bed_slope_diagnostic(stage, bed, dx, yx),
        local_bed=bed[max(0,yx[0]-1):yx[0]+2,max(0,yx[1]-1):yx[1]+2].tolist())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('snapshot', type=Path)
    parser.add_argument('checkpoint', type=Path)
    parser.add_argument('--seconds', type=float, default=1.)
    parser.add_argument('--speed-event', type=float, default=30.)
    parser.add_argument('--pressure-bed-slope', choices=('weighted', 'geometry'), default='weighted')
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    if args.report.exists(): raise FileExistsError(args.report)
    if not np.isfinite(args.speed_event) or args.speed_event<=0: raise ValueError('Invalid event threshold')
    meta, arrays, hashes = read_snapshot(args.snapshot)
    state = np.load(args.checkpoint, allow_pickle=False)
    hashes[str(args.checkpoint)] = hashlib.sha256(args.checkpoint.read_bytes()).hexdigest()
    bed = arrays['mean_geometry'][..., 0].astype(float)
    report = dict(schema='raftsim.velocity_spike_probe.v1', scope=__doc__, source_hashes=hashes,
        scene_accepted=False, requested_seconds=args.seconds, threshold_mps=args.speed_event, pressure_bed_slope=args.pressure_bed_slope,
        implementation_hashes={name:hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
            for name in ('probe_nonlinear_velocity_spike.py','total_depth_bank_replay.py','total_depth_nonlinear_pressure.py')})
    def observe(previous, current, progress):
        if progress['maximum_speed_mps'] > args.speed_event: raise SpeedEvent(previous, current, progress)
    try:
        _, stats = advance(state, bed, meta['cell_m'], args.seconds, second_order=True, dispersive=True,
            pressure_model='rational_sgn', pressure_interpolation='depth_weighted', pressure_formulation='kinematic', on_step=observe,
            pressure_bed_slope=args.pressure_bed_slope)
        report.update(event_found=False, statistics=stats)
    except SpeedEvent as event:
        report.update(event_found=True, progress=event.progress,
            analysis=dissect(event.previous, event.current, event.progress, bed, meta['cell_m'], args.pressure_bed_slope))
        for name, value in [('previous',event.previous),('event',event.current)]:
            output = args.report.with_suffix(f'.{name}.npy')
            with output.open('xb') as f: np.save(f,value)
            report[name+'_state'] = dict(path=str(output.resolve()),sha256=hashlib.sha256(output.read_bytes()).hexdigest())
    with args.report.open('x') as f: json.dump(report,f,indent=2,allow_nan=False)
    print(json.dumps(report,indent=2))


if __name__ == '__main__': main()
