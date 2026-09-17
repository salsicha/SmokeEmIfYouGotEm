"""Compare optical departures in a captured, frozen current (not river truth).

No foam density, velocity, geometry or capture is edited. Unknown/dry trajectory
samples remain unsupported, not clamped to an edge or filled with zero current.
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np


class FrozenCurrent:
    def __init__(self, flow, origin, cell):
        self.flow = np.asarray(flow, dtype=np.float64)
        self.origin = np.asarray(origin, dtype=np.float64)
        self.cell = float(cell)
        if (self.flow.ndim != 3 or self.flow.shape[2] != 4 or
                min(self.flow.shape[:2]) < 2 or self.origin.shape != (2,) or
                not np.isfinite(self.flow).all() or not np.isfinite(self.origin).all() or
                not np.isfinite(self.cell) or self.cell <= 0 or
                np.any(self.flow[..., 0] < 0)):
            raise ValueError('Finite nonnegative-depth complete lattice required')

    def sample(self, points):
        points = np.asarray(points, dtype=np.float64)
        if points.ndim != 2 or points.shape[1] != 2:
            raise ValueError('Nx2 points required')
        q = (points-self.origin)/self.cell
        h, w = self.flow.shape[:2]
        valid = np.isfinite(q).all(axis=1) & (q >= 0).all(axis=1) & (q <= (w-1, h-1)).all(axis=1)
        # Safe indexing only; the validity mask still rejects every outside row.
        safe = np.where(valid[:, None], q, 0)
        i = np.minimum(np.floor(safe).astype(int), (w-2, h-2))
        f = safe-i
        x, y = i.T
        a = self.flow[y, x]*(1-f[:, :1])+self.flow[y, x+1]*f[:, :1]
        b = self.flow[y+1, x]*(1-f[:, :1])+self.flow[y+1, x+1]*f[:, :1]
        value = a*(1-f[:, 1:])+b*f[:, 1:]
        valid &= value[:, 0] > .01
        return np.where(valid[:, None], value[:, 1:3], np.nan), valid

    def depart(self, points, seconds, steps, order):
        if (not np.isfinite(seconds) or seconds < 0 or type(steps) is not int or
                steps <= 0 or order not in (1, 2, 4)):
            raise ValueError('Nonnegative duration, positive steps and supported order required')
        x = np.array(points, dtype=np.float64, copy=True)
        if x.ndim != 2 or x.shape[1] != 2:
            raise ValueError('Nx2 points required')
        dt = seconds/steps
        valid = np.ones(len(x), dtype=bool)
        for _ in range(steps):
            k1, ok = self.sample(x); valid &= ok
            if order == 1:
                velocity = k1
            else:
                k2, ok = self.sample(x-.5*dt*k1); valid &= ok
                if order == 2:
                    velocity = k2
                else:
                    k3, ok = self.sample(x-.5*dt*k2); valid &= ok
                    k4, ok = self.sample(x-dt*k3); valid &= ok
                    velocity = (k1+2*k2+2*k3+k4)/6
            x -= dt*velocity
        _, ok = self.sample(x); valid &= ok
        return np.where(valid[:, None], x, np.nan), valid


def error_summary(values):
    if not len(values):
        return dict(count=0, rms_m=None, p95_m=None, maximum_m=None)
    return dict(count=len(values), rms_m=float(np.sqrt(np.mean(values**2))),
                p95_m=float(np.quantile(values, .95)), maximum_m=float(values.max()))


def analyze(prefix):
    metadata_path = Path(str(prefix)+'.json')
    metadata = json.loads(metadata_path.read_text())
    if (metadata.get('schema') != 'raftsim.detail.snapshot.v2' or
            metadata.get('arrays_complete') is not True or
            metadata.get('dtype') != 'little-endian float32'):
        raise ValueError('Complete original v2 native snapshot required')
    clock = metadata.get('simulation_s')
    if type(clock) not in (int, float) or not np.isfinite(clock) or clock < 0:
        raise ValueError('Finite nonnegative original simulation clock required')
    shape = metadata['shape']
    if (not isinstance(shape, list) or len(shape) != 3 or shape[2] != 4 or
            any(type(v) is not int or v < 2 for v in shape)):
        raise ValueError('Original four-channel lattice shape required')
    files = [metadata_path]
    arrays = {}
    for name in ('flow', 'surface'):
        path = Path(str(prefix)+'.'+name+'.f32')
        arrays[name] = np.fromfile(path, dtype='<f4').reshape(shape)
        files.append(path)
        if not np.isfinite(arrays[name]).all():
            raise ValueError('Nonfinite source data')
    coverage = arrays['surface'][..., 3]
    if (coverage < 0).any() or (coverage > 1).any():
        raise ValueError('Bounded original resolved coverage required')
    field = FrozenCurrent(arrays['flow'], metadata['origin_m'], metadata['cell_m'])
    y, x = np.indices(shape[:2])
    xy = np.stack((x, y), axis=-1)*field.cell+field.origin
    edge = np.minimum.reduce((x, y, shape[1]-1-x, shape[0]-1-y))*field.cell
    mask = (arrays['flow'][..., 0] > .01) & (edge >= 4)
    points = xy[mask]; foam = coverage[mask]
    if not len(points):
        raise ValueError('No wet fully-owned original samples')
    records = []
    for duration in (.25, .5, .75):
        previous, previous_ok = field.depart(points, duration, 64, 4)
        refinement = []
        for reference_steps in (128, 256, 512, 1024):
            ref, ok = field.depart(points, duration, reference_steps, 4)
            supported = ok & previous_ok
            convergence = np.linalg.norm(ref[supported]-previous[supported], axis=1)
            refinement.append(dict(steps=reference_steps, error=error_summary(convergence),
                                   changed_support=int((ok != previous_ok).sum())))
            if supported.any() and convergence.max() <= 1.e-4 and np.array_equal(ok, previous_ok):
                break
            previous, previous_ok = ref, ok
        else:
            raise ValueError('Frozen-field reference did not converge to 0.1 mm: '+str(refinement))
        methods = {}
        departures = {}
        for name, steps, order in [('straight', 1, 1), ('midpoint2', 2, 2),
                                   ('midpoint4', 4, 2), ('midpoint8', 8, 2)]:
            departure, valid = field.depart(points, duration, steps, order)
            compared = supported & valid
            error = np.linalg.norm(departure[compared]-ref[compared], axis=1)
            foamy = foam[compared] > .1
            methods[name] = dict(supported_rows=int(compared.sum()),
                                 unsupported_rows=int((~compared).sum()),
                                 all_wet=error_summary(error), foamy=error_summary(error[foamy]))
            departures[name] = (departure, compared)
        # Paired comparisons additionally retain exactly the same cohort for
        # EVERY method, so different dry/outside rejection counts cannot bias
        # the quoted improvement. Individual-method populations stay above.
        common = np.logical_and.reduce([valid for _, valid in departures.values()])
        for name, (departure, _) in departures.items():
            common_error = np.linalg.norm(departure[common]-ref[common], axis=1)
            methods[name]['common_wet'] = error_summary(common_error)
            methods[name]['common_foamy'] = error_summary(common_error[foam[common] > .1])
        rows = []
        for i, point in enumerate(points):
            row = dict(x_m=float(point[0]), y_m=float(point[1]), coverage=float(foam[i]),
                       reference=ref[i].tolist() if supported[i] else None)
            for name, (departure, compared) in departures.items():
                row[name] = departure[i].tolist() if compared[i] else None
            rows.append(row)
        records.append(dict(seconds=duration, reference_refinement=refinement,
                            reference_convergence=error_summary(convergence),
                            common_supported_rows=int(common.sum()),
                            reference_unsupported=int((~supported).sum()), methods=methods, rows=rows))
    return dict(schema='raftsim.frozen_froth_characteristics.v1',
                scope='Frozen captured mean current only; not historical current, material pixels, calibrated river velocity or physical foam transport.',
                simulation_s=metadata['simulation_s'], original_wet_interior_cells=len(points),
                input_sha256={str(p.resolve()): hashlib.sha256(p.read_bytes()).hexdigest() for p in files},
                records=records, visual_accepted=False, physical_accepted=False, release_accepted=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('prefix', type=Path)
    parser.add_argument('--report', required=True, type=Path)
    args = parser.parse_args()
    if args.report.exists():
        raise FileExistsError(args.report)
    report = analyze(args.prefix)
    with args.report.open('x', encoding='utf-8') as stream:
        json.dump(report, stream, indent=2, allow_nan=False)
    for record in report['records']:
        print(json.dumps({k:v for k,v in record.items() if k != 'rows'}))


if __name__ == '__main__':
    main()
