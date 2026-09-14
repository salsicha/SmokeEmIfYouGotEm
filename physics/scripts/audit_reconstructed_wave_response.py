"""Independent small-amplitude standing-wave acceleration audit.

Uses actual unscaled FV rates plus the research reconstructed pressure adapter.
The physical reference is omega^2=g*k*tanh(k*h), e.g. MIT 2.20 lecture 20:
https://ocw.mit.edu/courses/2-20-marine-hydrodynamics-13-021-spring-2005/5d48a5937971d973fd8ca90c051a83f8_lecture20.pdf
This is an instantaneous spatial/closure check, NOT evolved phase, boundary,
wetting, breaking, native, performance or playable qualification.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import total_depth_bank_replay as bank
from reconstructed_pressure_adapter import reconstructed_pressure


def measure(wavelength, cells, *, axis=1, amplitude=1e-5, model='rational_sgn'):
    if (not np.isfinite(wavelength) or wavelength <= 0 or cells < 8
            or int(cells) != cells or axis not in (0, 1)
            or not np.isfinite(amplitude) or not 0 < amplitude <= 1e-3
            or model not in ('sgn', 'rational_sgn')):
        raise ValueError('Invalid wave-response experiment')
    depth, gravity = 1.5, 9.81
    dx = wavelength/cells
    k = 2*np.pi/wavelength
    phase = k*(np.arange(cells)+.5)*dx
    shape = (1, cells) if axis == 1 else (cells, 1)
    h = (depth+amplitude*np.cos(phase)).reshape(shape)
    initial = np.zeros((*shape, 3)); initial[..., 0] = h
    before = initial.copy(); initial.flags.writeable = False
    bed = np.zeros(shape); bed.flags.writeable = False
    stages = []
    with reconstructed_pressure(stages.append):
        rate, cfl = bank.rate(initial, bed, dx, second_order=True, periodic=True,
            dispersive=True, pressure_model=model, pressure_interpolation='depth_weighted',
            pressure_formulation='kinematic', pressure_bed_slope='geometry',
            shoreline_limiter='unscaled')
    if not np.array_equal(initial, before):
        raise AssertionError('Source state mutated')
    component = 1 if axis == 1 else 2
    scale = gravity*depth*amplitude*k
    normalized = rate[..., component].ravel()/scale
    sine, cosine = np.sin(phase), np.cos(phase)
    measured = float(np.dot(normalized, sine)/np.dot(sine, sine))
    airy = float(np.tanh(k*depth)/(k*depth))
    # Independently evaluate the rational closure's continued fraction rather
    # than importing its pole weights. The SGN control has only denominator 3.
    z = (k*depth)**2
    closure = 1/(1+z/3) if model == 'sgn' else 1/(1+z/(3+z/(5+z/(7+z/9))))
    residual = normalized-measured*sine
    return dict(wavelength_m=wavelength, cells_per_wavelength=cells, axis=axis,
        amplitude_m=amplitude, mean_depth_m=depth, pressure_model=model,
        measured_restoring_response=measured, airy_response=airy,
        continuum_closure_response=closure,
        relative_airy_response_error=measured/airy-1,
        relative_closure_response_error=measured/closure-1,
        quadrature_response=float(np.dot(normalized, cosine)/np.dot(cosine, cosine)),
        nonfundamental_relative_l2=float(np.linalg.norm(residual)/np.linalg.norm(measured*sine)),
        mass_rate_integral_m3ps=float(rate[..., 0].sum()*dx*dx),
        momentum_rate_integral_m4ps2=(rate[..., 1:].sum((0, 1))*dx*dx).tolist(),
        transverse_rate_max=float(abs(rate[..., 3-component]).max()),
        cfl_seconds=float(cfl), pressure_stages=stages)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    if args.report.exists(): raise FileExistsError(args.report)
    files = ('audit_reconstructed_wave_response.py', 'reconstructed_pressure_adapter.py',
        'reconstructed_nonlinear_pressure.py', 'reconstructed_acceleration_system.py',
        'directional_pressure_geometry.py', 'reconstructed_pressure_geometry.py',
        'reconstructed_pressure_rates.py', 'pressure_cut_face_reference.py',
        'total_depth_bank_replay.py', 'adaptive_hydrostatic_precision.py',
        'continuous_shoreline_reconstruction.py', 'total_depth_nonlinear_pressure.py',
        'pressure_cg_range_reference.py', 'breaking_front_reference.py',
        'finite_depth_pressure_reference.py')
    paths = [Path(__file__).with_name(name) for name in files]
    hashes = {str(p): hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in paths}
    results = []
    for wavelength in (2., 4., 12.):
        for cells in (32, 64, 128):
            result = measure(wavelength, cells)
            results.append(result)
            print(json.dumps(result, allow_nan=False), flush=True)
    for model in ('rational_sgn', 'sgn'):
        for axis in (0, 1):
            results.append(measure(4., 64, axis=axis, amplitude=1e-6, model=model))
    if any(hashlib.sha256(Path(p).read_bytes()).hexdigest() != h for p, h in hashes.items()):
        raise RuntimeError('Implementation changed during audit')
    report = dict(schema='raftsim.reconstructed_wave_response.v1', scope=__doc__,
        scene_accepted=False, evolved_history_qualified=False,
        implementation_hashes=hashes, results=results)
    with args.report.open('x') as output: json.dump(report, output, indent=2, allow_nan=False)


if __name__ == '__main__': main()
