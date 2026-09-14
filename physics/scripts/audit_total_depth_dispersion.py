"""Analytic wave comparisons, not scene/production acceptance.

Airy waves test the requested finite-depth linear behavior. The finite-amplitude
comparison uses the exact SGN solitary wave in Guermond et al., equation (7.1):
https://people.tamu.edu/~guermond/PUBLICATIONS/GKPT_WaterWaves_2022.pdf
Only the standard SGN closure has that governing-equation reference. The linear
local-depth and rational SGN models differ; their shape discrepancies are not
exact-solution convergence errors. The periodic box truncates small wave tails.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from total_depth_bank_replay import advance


def solitary(x, time, mean_depth=1.5, amplitude=.45, origin=24.):
    c = np.sqrt(9.81*(mean_depth+amplitude))
    width = np.sqrt(3*amplitude/(4*mean_depth**2*(mean_depth+amplitude)))
    eta = amplitude/np.cosh(width*(x-origin-c*time))**2
    return np.stack((mean_depth+eta, c*eta, np.zeros_like(x)), axis=-1), c


def peak_location(values, x, dx):
    i = int(np.argmax(values))
    a, b, c = values[(i-1) % values.size], values[i], values[(i+1) % values.size]
    curvature = a-2*b+c
    offset = .5*(a-c)/curvature if curvature else 0
    return float(x[i]+dx*offset)


def airy(wavelength, dispersive, pressure_model='linear', pressure_interpolation='centered', pressure_formulation='expanded', pressure_bed_slope='weighted'):
    count, depth, amplitude, current = 128, 1.5, 1e-5, .4
    dx = 4*wavelength/count
    x = (np.arange(count)+.5)*dx
    k = 2*np.pi/wavelength
    speed = np.sqrt(9.81*np.tanh(k*depth)/k)
    eta = amplitude*np.cos(k*x)
    h = depth+eta
    initial = np.stack((h, current*h+speed*eta, np.zeros_like(h)), axis=-1)[None]
    seconds = wavelength/(speed+current)
    final, stats = advance(initial, np.zeros((1, count)), dx, seconds,
        second_order=True, periodic=True, dispersive=dispersive, pressure_model=pressure_model,
        pressure_interpolation=pressure_interpolation, pressure_formulation=pressure_formulation, pressure_bed_slope=pressure_bed_slope)
    coefficient = np.exp(-1j*k*x)
    ratio = np.sum((final[0, :, 0]-depth)*coefficient)/np.sum(eta*coefficient)
    phase = float(abs(np.angle(ratio))/(2*np.pi))
    amplitude_ratio = float(abs(ratio))
    return dict(wavelength_m=wavelength, cells_per_wavelength=32,
        mean_depth_m=depth, dispersive=dispersive,
        pressure_model=pressure_model,
        pressure_interpolation=pressure_interpolation,
        pressure_formulation=pressure_formulation,
        pressure_bed_slope=pressure_bed_slope,
        phase_error_cycles=phase, amplitude_ratio=amplitude_ratio,
        linear_check_passed=phase < .03 and .9 < amplitude_ratio < 1.1,
        statistics=stats)


def nonlinear_comparison(dx, dispersive, pressure_model='linear', pressure_interpolation='centered', pressure_formulation='expanded', pressure_bed_slope='weighted'):
    if not np.isfinite(dx) or dx <= 0 or abs(round(96/dx)*dx-96) > 1e-9:
        raise ValueError('Cell spacing must exactly tile the 96 m reference domain')
    x = (np.arange(round(96/dx))+.5)*dx
    initial, speed = solitary(x, 0)
    seconds = 4.
    exact, _ = solitary(x, seconds)
    final, stats = advance(initial[None], np.zeros((1, x.size)), dx, seconds,
        second_order=True, periodic=True, dispersive=dispersive, pressure_model=pressure_model,
        pressure_interpolation=pressure_interpolation, pressure_formulation=pressure_formulation, pressure_bed_slope=pressure_bed_slope)
    final = final[0]
    initial_peak = peak_location(initial[:, 0], x, dx)
    final_peak = peak_location(final[:, 0], x, dx)
    return dict(reference=('SGN solitary wave; same standard SGN equations, truncated tails in periodic box'
        if dispersive and pressure_model == 'sgn' else 'SGN solitary wave, not the candidate governing equations'),
        amplitude_depth_ratio=.3, mean_depth_m=1.5, cell_m=dx,
        dispersive=dispersive, elapsed_s=seconds,
        pressure_model=pressure_model,
        pressure_interpolation=pressure_interpolation,
        pressure_formulation=pressure_formulation,
        pressure_bed_slope=pressure_bed_slope,
        relative_surface_l1_difference=float(np.sum(abs(final[:, 0]-exact[:, 0]))/np.sum(exact[:, 0]-1.5)),
        peak_amplitude_ratio=float((final[:, 0].max()-1.5)/.45),
        relative_peak_speed_difference=float((final_peak-initial_peak)/(speed*seconds)-1),
        momentum_change_m3ps=float(np.sum(final[:, 1]-initial[:, 1])*dx),
        statistics=stats)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--pressure-model', choices=('linear', 'sgn', 'rational_sgn'), default='linear')
    parser.add_argument('--pressure-interpolation', choices=('centered', 'depth_weighted'), default='centered')
    parser.add_argument('--pressure-formulation', choices=('expanded', 'kinematic'), default='expanded')
    parser.add_argument('--pressure-bed-slope', choices=('weighted', 'geometry'), default='weighted')
    parser.add_argument('--nonlinear-only', action='store_true')
    parser.add_argument('--cell-m', type=float, nargs='+', default=[.5, .25])
    args = parser.parse_args()
    if args.report.exists(): raise FileExistsError(args.report)
    files = ('audit_total_depth_dispersion.py', 'total_depth_bank_replay.py',
        'total_depth_pressure.py', 'finite_depth_pressure_reference.py', 'total_depth_nonlinear_pressure.py')
    hashes = {name: hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest() for name in files}
    report = dict(schema='raftsim.total_depth_dispersion_comparison.v1', scope=__doc__,
        implementation_hashes=hashes, pressure_iterations=40, scene_accepted=False,
        pressure_model=args.pressure_model,
        pressure_interpolation=args.pressure_interpolation,
        pressure_formulation=args.pressure_formulation,
        pressure_bed_slope=args.pressure_bed_slope,
        nonlinear_only=args.nonlinear_only,
        airy=[], nonlinear=[])
    for dispersive in (False, True):
        for wavelength in (() if args.nonlinear_only else (2., 4., 12.)):
            result = airy(wavelength, dispersive, args.pressure_model, args.pressure_interpolation, args.pressure_formulation, args.pressure_bed_slope)
            report['airy'].append(result)
            print(json.dumps(result), flush=True)
        for dx in args.cell_m:
            result = nonlinear_comparison(dx, dispersive, args.pressure_model, args.pressure_interpolation, args.pressure_formulation, args.pressure_bed_slope)
            report['nonlinear'].append(result)
            print(json.dumps(result), flush=True)
    with args.report.open('x') as f: json.dump(report, f, indent=2, allow_nan=False)


if __name__ == '__main__': main()
