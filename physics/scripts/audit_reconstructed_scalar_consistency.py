"""Measure scalar-derivative consistency separately from pressure adjoint tests.

A spatially constant scalar has zero Euclidean gradient. The current research
kinematic forcing reuses the reconstructed pressure action for that derivative.
This diagnostic measures its constant-field defect, not the cause of a replay
failure and not acceptance of a replacement discretization.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from reconstructed_pressure_geometry import ReconstructedPressureGeometry
from reconstructed_pressure_rates import PressureGeometryRate, kinematic_forcing


def periodic_case(n, amplitude):
    x = (np.arange(n)+.5)/n
    bed = np.tile(amplitude*np.sin(2*np.pi*x), (2, 1))
    h = 1-bed
    g = ReconstructedPressureGeometry(h, bed, 1/n, periodic=True,
        pressure_trace='integrated_column', bed_quadrature='shared_bottom')
    u = np.zeros((*h.shape, 2)); u[..., 0] = 1.
    tangent = PressureGeometryRate(g, bed, np.zeros_like(h))
    _, _, adv = kinematic_forcing(g, tangent, u)
    gradient = g.scalar_gradient(np.ones_like(h))
    return dict(n=n, bed_amplitude=amplitude, all_cells_wet=bool(np.all(h > 0)),
                constant_scalar_gradient_linf=float(abs(gradient).max()),
                uniform_velocity_advective_linf=float(abs(adv).max()),
                uniform_velocity_divergence_linf=float(abs(g.kinematic_components(u)[0]).max()),
                exact_constant_scalar_preservation=bool(np.all(gradient == 0)),
                physical_or_scene_accepted=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--snapshot', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    if args.report.exists(): raise FileExistsError(args.report)
    raw = args.input.read_bytes(); record = json.loads(raw)
    first = record['observations'][0]
    with np.load(args.snapshot, allow_pickle=False) as arrays:
        state, bed, rate, pressure = (arrays[k].copy() for k in ('state', 'bed', 'rate', 'pressure'))
    expected = np.asarray(first['state']).reshape(first['ny'], first['nx'], 4)[..., :3]
    expected_bed = np.asarray(first['bed']).reshape(first['ny'], first['nx'])
    if state.tobytes() != expected.copy().tobytes() or bed.tobytes() != expected_bed.tobytes():
        raise ValueError('Snapshot is not the unchanged original first source state/bed')
    h = state[..., 0]
    g = ReconstructedPressureGeometry(h, bed, first['cell_meters'],
        exterior_bed=np.asarray(first['exterior_bed']), pressure_trace='integrated_column', bed_quadrature='shared_bottom')
    gradient = g.scalar_gradient(np.ones_like(h))
    pressure_acceleration = np.divide(pressure, h[..., None], out=np.zeros_like(pressure), where=h[..., None] > 0)
    acceleration_norm = np.linalg.norm(pressure_acceleration, axis=-1)
    indices = np.argsort(acceleration_norm.ravel(), kind='stable')[-6:][::-1]
    cells = []
    for flat in indices:
        p = np.unravel_index(flat, h.shape)
        cells.append(dict(yx=[int(i) for i in p], h_m=float(h[p]), mass_rate=float(rate[p][0]),
                          pressure_momentum_rate=pressure[p].tolist(),
                          pressure_acceleration_mps2=pressure_acceleration[p].tolist(),
                          constant_scalar_gradient=gradient[p].tolist(),
                          pressure_over_entering_mass_rate=(pressure[p]/rate[p][0]).tolist() if rate[p][0] > 0 else None))
    report = dict(schema='raftsim.reconstructed_scalar_consistency.v1', source_sha256=hashlib.sha256(raw).hexdigest(),
                  snapshot_sha256=hashlib.sha256(args.snapshot.read_bytes()).hexdigest(),
                  full_rate_sha256=hashlib.sha256(rate.tobytes()).hexdigest(),
                  periodic_controls=[periodic_case(n, amplitude) for amplitude in (0., .2) for n in (16, 32, 64)],
                  captured_constant_extension_gradient_linf=float(abs(gradient).max()),
                  captured_maximum_pressure_acceleration_mps2=float(acceleration_norm.max()),
                  captured_high_pressure_acceleration_cells=cells,
                  limitation='The captured constant scalar extends through dry cells for this operator diagnostic; it is not a physical dry-cell velocity. Large force/depth can coexist with entering mass and does not prove runaway accepted velocity.',
                  replay_growth_cause_established=False, physical_or_scene_accepted=False)
    with args.report.open('x', encoding='utf-8') as stream:
        json.dump(report, stream, indent=2, allow_nan=False)
        stream.write('\n')
    print(json.dumps(report, allow_nan=False))


if __name__ == '__main__': main()
