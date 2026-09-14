"""Manufactured face-velocity boundary fixtures, NOT a river or FV coupling claim.

All uploaded inputs are rounded to float32 before the double reference is solved.
The supplied rate is manufactured forcing, not a ghost-centre-to-face conversion.
The binary extends pressure fixture v1 with an explicit face trace per case.
"""
import argparse
import hashlib
import json
import struct
from pathlib import Path
import numpy as np
from total_depth_pressure import wet_pairs
from total_depth_nonlinear_pressure import nonlinear_pressure_force, geometric_bed_slope


def fixture(state, bed, rate, boundary, dx=.5, fraction=None):
    state, bed, rate, boundary = [np.asarray(a, dtype=np.float32).astype(float)
                                  for a in (state, bed, rate, boundary)]
    h = state[..., 0]
    fraction = np.ones_like(h) if fraction is None else np.asarray(fraction, dtype=np.float32).astype(float)
    pairs = wet_pairs(h, bed)
    slope = geometric_bed_slope(bed, dx).astype(np.float32).astype(float)
    velocity = np.divide(state[..., 1:], h[..., None], out=np.zeros_like(state[..., 1:]), where=h[..., None] > 0)
    poles = []
    force, stats = nonlinear_pressure_force(h, bed, velocity, velocity*0, pairs, dx,
        interpolation='depth_weighted', formulation='kinematic', mass_rate=rate[..., 0],
        momentum_rate=rate[..., 1:], bed_slope=slope, dispersion_fraction=fraction,
        boundary_velocity=boundary, on_pressure=poles.extend)
    fields = [np.stack((h, bed), axis=-1), np.concatenate((state, h[..., None]*0), axis=-1),
        np.concatenate((rate, h[..., None]*0), axis=-1), slope, fraction,
        pairs[0].astype(np.uint32)+2*pairs[1].astype(np.uint32),
        np.concatenate([p['rhs'] for p in poles], axis=-1),
        np.concatenate([p['correction'] for p in poles], axis=-1),
        np.stack([v for p in poles for v in (p['pressure'], p['bottom_pressure'])], axis=-1), force, boundary]
    return fields, dict(shape=list(h.shape), cell_m=dx, periodic=False, reference_solver=stats,
                        force_max=float(abs(force).max()))


def cases():
    records = []
    for shape in ((9, 13), (1, 17), (19, 1), (1, 1)):
        for ux, uy in ((1., 0.), (-1., 0.), (0., 1.), (0., -1.)):
            ny, nx = shape; h = np.ones(shape)
            trace = np.array([[ux, 0.]]*(2*ny)+[[uy, 0.]]*(2*nx))
            state = np.stack((h, h*ux, h*uy), axis=-1)
            records.append((f'uniform_{ny}x{nx}_{ux}_{uy}', *fixture(state, h*0, state*0, trace)))
    h = np.ones((9, 13)); state = np.stack((h, .75*h, -.25*h), axis=-1)
    # Binary-exact symmetric acceleration has an exactly zero double oracle;
    # the asymmetric case remains covered by the time-differentiation CPU test.
    rate = np.stack((h*0, .25*h, .25*h), axis=-1)
    trace = np.array([[.75, .25]]*18+[[-.25, .25]]*26)
    records.append(('uniform_acceleration', *fixture(state, h*0, rate, trace)))
    y, x = np.indices((13, 17)); bed = .03*np.sin(x*.2)*np.cos(y*.3)
    h = .9+.12*np.sin(x*.23)+.08*np.cos(y*.31)
    state = np.stack((h, h*(.4+.1*np.sin(x*.3)), h*.2*np.cos(y*.2)), axis=-1)
    rate = np.stack((.02*np.cos(x*.2), .04*np.sin(x*.3), -.03*np.cos(y*.2)), axis=-1)
    j = np.arange(60); trace = np.stack((.35+.12*np.sin(j*.2), .015*np.cos(j*.3)), axis=-1)
    for kind in ('variable', 'mixed_dry', 'zero_trace'):
        current = state.copy(); fraction = np.ones_like(h); boundary = trace.copy()
        if kind == 'mixed_dry':
            current[0, 0] = 0; current[6, 7] = (1e-20, 2e-21, -1e-21)
            fraction = np.array([0., .35, 1.])[(x//4+y//3) % 3]
        if kind == 'zero_trace': boundary[:] = 0
        records.append((kind, *fixture(current, bed, rate, boundary, fraction=fraction)))
    # Last case intentionally has more boundary entries than cell threads.
    # Native invalid-input checks mutate its LAST trace entry.
    h = np.ones((1, 1)); state = np.stack((h, h*0, h*0), axis=-1)
    records.append(('single_cell_rest', *fixture(state, h*0, state*0, np.zeros((4, 2)))))
    return records


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(); manifest = args.output.with_suffix('.json')
    if args.output.exists() or manifest.exists(): raise FileExistsError(args.output)
    records = cases()
    for _, fields, meta in records:
        if not all(np.isfinite(f).all() and np.isfinite(np.asarray(f, dtype=np.float32)).all() for f in fields):
            raise ValueError('Nonfinite manufactured fixture')
        if any(s['relative_residual'] > 2e-5 for s in meta['reference_solver']):
            raise ValueError('Reference residual gate failed')
    with args.output.open('xb') as out:
        out.write(struct.pack('<III', 0x52535046, 2, len(records)))
        for _, fields, meta in records:
            ny, nx = meta['shape']; out.write(struct.pack('<IIIf', nx, ny, 0, meta['cell_m']))
            for index, field in enumerate(fields):
                out.write(np.asarray(field, dtype='<u4' if index == 5 else '<f4').tobytes(order='C'))
    result = dict(schema='raftsim.prescribed_pressure_fixtures.v1', scope=__doc__, scene_accepted=False,
        fixture_sha256=hashlib.sha256(args.output.read_bytes()).hexdigest(),
        cases=[dict(name=name, **meta) for name, _, meta in records],
        implementation_hashes={name: hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
            for name in ('export_prescribed_pressure_fixtures.py', 'total_depth_nonlinear_pressure.py', 'total_depth_pressure.py')})
    with manifest.open('x') as out: json.dump(result, out, indent=2, allow_nan=False)
    print(json.dumps(result, indent=2))


if __name__ == '__main__': main()
