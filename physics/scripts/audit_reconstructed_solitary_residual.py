"""Exact travelling-profile derivative versus actual reconstructed FV rate.

SGN has the Guermond et al. equation7.1 solitary solution; rational SGN does
not. Report both without relabelling rational-model discrepancy as truncation
error. This instantaneous flat-bed check does not qualify evolved river water.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import total_depth_bank_replay as bank
from audit_total_depth_dispersion import solitary
from reconstructed_pressure_adapter import reconstructed_pressure


def exact_time_rate(x, time=0.):
    h0, amplitude, origin = 1.5, .45, 24.
    c = np.sqrt(9.81*(h0+amplitude))
    r = np.sqrt(3*amplitude/(4*h0*h0*(h0+amplitude)))
    z = r*(x-origin-c*time)
    eta = amplitude/np.cosh(z)**2
    derivative = -2*r*eta*np.tanh(z)
    return np.stack((-c*derivative, -c*c*derivative, np.zeros_like(x)), axis=-1)


def measure(dx, model):
    if dx not in (.5, .25, .125) or model not in ('sgn', 'rational_sgn'):
        raise ValueError('Explicit solitary profile spacings and governing model required')
    x = (np.arange(round(96/dx))+.5)*dx
    state, _ = solitary(x, 0.)
    state = state[None]; original = state.copy(); state.flags.writeable = False
    stages = []
    with reconstructed_pressure(stages.append):
        actual, cfl = bank.rate(state, np.zeros(state.shape[:2]), dx,
            second_order=True, periodic=True, dispersive=True, pressure_model=model,
            pressure_interpolation='depth_weighted', pressure_formulation='kinematic',
            pressure_bed_slope='geometry', shoreline_limiter='unscaled')
    expected = exact_time_rate(x)[None]
    if not np.array_equal(state, original): raise AssertionError('Original solitary state changed')
    errors = abs(actual-expected).sum((0, 1))[:2]/abs(expected).sum((0, 1))[:2]
    return dict(cell_m=dx, model=model, exact_for_governing_equations=model == 'sgn',
        periodic_tail_truncation=True, relative_mass_rate_l1_difference=float(errors[0]),
        relative_momentum_rate_l1_difference=float(errors[1]),
        net_mass_rate_per_width_m2ps=float(actual[..., 0].sum()*dx),
        net_momentum_rate_per_width_m3ps2=(actual[..., 1:].sum((0, 1))*dx).tolist(),
        transverse_rate_max=float(abs(actual[..., 2]).max()),
        cfl_seconds=float(cfl), pressure_stages=stages,
        pressure_residual_check_passed=bool(all(p['relative_residual'] < 2e-5
            for stage in stages for p in stage['pressure_stats'])),
        initial_state_sha256=hashlib.sha256(state.tobytes()).hexdigest())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    if args.report.exists(): raise FileExistsError(args.report)
    files = ('audit_reconstructed_solitary_residual.py', 'audit_total_depth_dispersion.py',
        'reconstructed_pressure_adapter.py', 'reconstructed_nonlinear_pressure.py',
        'reconstructed_acceleration_system.py', 'directional_pressure_geometry.py',
        'reconstructed_pressure_geometry.py', 'reconstructed_pressure_rates.py',
        'pressure_cut_face_reference.py', 'total_depth_bank_replay.py',
        'adaptive_hydrostatic_precision.py', 'continuous_shoreline_reconstruction.py',
        'total_depth_nonlinear_pressure.py', 'pressure_cg_range_reference.py',
        'finite_depth_pressure_reference.py', 'detail_nonlinear_flux.py',
        'total_depth_pressure.py', 'breaking_front_reference.py')
    paths = [Path(__file__).with_name(name) for name in files]
    hashes = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    results = []
    for model in ('sgn', 'rational_sgn'):
        for dx in (.5, .25, .125):
            result = measure(dx, model); results.append(result)
            print(json.dumps(result, allow_nan=False), flush=True)
    if any(hashlib.sha256(Path(p).read_bytes()).hexdigest() != h for p, h in hashes.items()):
        raise RuntimeError('Implementation changed during audit')
    report = dict(schema='raftsim.reconstructed_solitary_residual.v1', scope=__doc__,
        scene_accepted=False, nonlinear_history_qualified=False,
        implementation_hashes=hashes, results=results,
        all_pressure_checks_passed=all(r['pressure_residual_check_passed'] for r in results))
    encoded = json.dumps(report, indent=2, allow_nan=False)
    with args.report.open('x') as output: output.write(encoded)
    if not report['all_pressure_checks_passed']: raise SystemExit(1)


if __name__ == '__main__': main()
