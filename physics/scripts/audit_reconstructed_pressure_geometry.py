"""Manufactured refinement audit of the research cut-column pressure transfer.

No evolution or captured geometry is changed. Reports errors, including failures
of exact constant-integrated-pressure response; it does not turn a passing static
adjoint/momentum check into full accuracy or gameplay acceptance.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from reconstructed_pressure_geometry import ReconstructedPressureGeometry
from total_depth_nonlinear_pressure import gradient, depth_weights, geometric_bed_slope


def norms(value):
    return dict(l1=float(np.mean(abs(value))), l2=float(np.sqrt(np.mean(value*value))),
                linf=float(abs(value).max()))


def refinement(counts=(32, 64, 128, 256, 512, 1024), *, pressure_trace='mean_column', bed_quadrature='polynomial'):
    rows = []
    for n in counts:
        if type(n) is not int or n < 8:
            raise ValueError('Refinement requires integer grids of at least eight cells')
        dx = 2*np.pi/n; x = (np.arange(n)+.5)*dx
        h = (1+.2*np.sin(x))[None, :]; bed = (.1*np.cos(x))[None, :]
        p = (.7*np.sin(2*x+.3))[None, :]; b = np.cos(3*x)[None, :]
        exact = 1.4*np.cos(2*x+.3)-.1*np.cos(3*x)*np.sin(x)
        g = ReconstructedPressureGeometry(h, bed, dx, periodic=True, pressure_trace=pressure_trace,
                                          bed_quadrature=bed_quadrature)
        pairs = [np.ones_like(h, dtype=bool), np.zeros_like(h, dtype=bool)]
        old = gradient(p, pairs, dx, depth_weights(h))+b[..., None]*geometric_bed_slope(bed, dx, True)
        current = g.gradient_traction(p, b)
        constant = g.gradient_traction(np.ones_like(h), np.zeros_like(h))
        flat = ReconstructedPressureGeometry(h, np.zeros_like(h), dx, periodic=True, pressure_trace=pressure_trace,
                                             bed_quadrature=bed_quadrature)
        flat_constant = flat.gradient_traction(np.ones_like(h), np.zeros_like(h))
        velocity = np.zeros((*h.shape, 2)); velocity[0, :, 0] = .6+.1*np.cos(2*x)
        divergence, bed_velocity = g.kinematic_components(velocity)
        rows.append(dict(cells=n, dx=dx, candidate_error=norms(current[0, :, 0]-exact),
            original_error=norms(old[0, :, 0]-exact),
            constant_integrated_pressure_error=norms(constant[0, :, 0]),
            flat_constant_integrated_pressure_error=norms(flat_constant[0, :, 0]),
            kinematic_divergence_error=norms(divergence[0]+.2*np.sin(2*x)),
            kinematic_bed_error=norms(bed_velocity[0]+.1*velocity[0, :, 0]*np.sin(x)),
            constant_error_peak_cell=int(np.argmax(abs(constant[0, :, 0])))))
    for previous, row in zip(rows, rows[1:]):
        ratio = np.log(row['cells']/previous['cells'])
        row['observed_orders'] = {name: {norm: float(np.log(previous[name][norm]/row[name][norm])/ratio)
            if previous[name][norm] > 0 and row[name][norm] > 0 else None
            for norm in ('l1', 'l2', 'linf')} for name in
            ('candidate_error', 'original_error', 'constant_integrated_pressure_error',
             'flat_constant_integrated_pressure_error', 'kinematic_divergence_error', 'kinematic_bed_error')}
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--pressure-trace', choices=('mean_column', 'integrated_column'), default='mean_column')
    parser.add_argument('--bed-quadrature', choices=('polynomial', 'shared_bottom'), default='polynomial')
    args = parser.parse_args()
    if args.report.exists():
        raise FileExistsError(args.report)
    result = dict(schema='raftsim.reconstructed_pressure_geometry_refinement.v1', scope=__doc__,
        fields='x in [0,2pi), h=1+0.2sin(x), bed=0.1cos(x), P=0.7sin(2x+0.3), B=cos(3x)',
        pressure_trace=args.pressure_trace, bed_quadrature=args.bed_quadrature,
        expected_operator='dP/dx+B*d(bed)/dx', rows=refinement(pressure_trace=args.pressure_trace,
                                                            bed_quadrature=args.bed_quadrature),
        qualification='Static research operator only. No pressure solve, time derivative, trajectory or gameplay qualification.',
        implementation_hashes={name: hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
            for name in ('audit_reconstructed_pressure_geometry.py', 'reconstructed_pressure_geometry.py',
                'pressure_cut_face_reference.py', 'total_depth_bank_replay.py', 'adaptive_hydrostatic_precision.py',
                'total_depth_nonlinear_pressure.py')})
    with args.report.open('x') as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
    print(json.dumps(dict(report=str(args.report), rows=result['rows']), indent=2))


if __name__ == '__main__':
    main()
