"""Independent analytic extrusion/box reference and actual pressure readbacks.

Does not import polygon-section/area code or execute a solver. Verifies every
face against actual box bounds and the complete measured laboratory bed profile.
The profile is synthetic authoring, NOT captured river measurements.
"""
import argparse
import hashlib
import json
from pathlib import Path
import time
import numpy as np


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def interval_union_area(pieces, lower, upper):
    """Independent interval-envelope integration: (x0,x1,ylo,slope,intercept)."""
    lo, hi = lower, upper; cropped = []
    for a, b, c, m, q in pieces:
        a, b = max(a, lo[0]), min(b, hi[0])
        if b > a and c < hi[1] and max(m*a+q, m*b+q) > lo[1]:
            cropped.append((a, b, max(c, lo[1]), m, q))
    if not cropped:
        return 0.
    events = {lo[0], hi[0]}
    levels = [lo[1], hi[1]]+[p[2] for p in cropped]
    for a, b, _, m, q in cropped:
        events.update((a, b))
        if m:
            for level in levels:
                x = (level-q)/m
                if a < x < b:
                    events.add(x)
    for i, a in enumerate(cropped):
        for b in cropped[i+1:]:
            if a[3] != b[3]:
                x = (b[4]-a[4])/(a[3]-b[3])
                if max(a[0], b[0]) < x < min(a[1], b[1]):
                    events.add(x)
    events = sorted(events); area = 0.
    for a, b in zip(events, events[1:]):
        active = [p for p in cropped if p[0] <= a and p[1] >= b]
        lengths = []
        for x in (a, b):
            intervals = sorted((c, min(hi[1], m*x+q)) for _, _, c, m, q in active if min(hi[1], m*x+q) > c)
            length = 0.; end = lo[1]
            for c, d in intervals:
                length += max(0., d-max(end, c)); end = max(end, d)
            lengths.append(length)
        area += (b-a)*sum(lengths)/2
    return area


def actual_primitives(meshes):
    boxes = []; profile = None
    for mesh in meshes:
        v = np.load(mesh['vertices'], allow_pickle=False); t = np.load(mesh['triangles'], allow_pickle=False)
        lo, hi = v.min(0), v.max(0)
        if mesh['name'] != 'Obstacle approach bed':
            if len(v) != 8 or len(t) != 12 or not np.all((v == lo) | (v == hi)):
                raise ValueError('Analytic reference requires verified actual axis-aligned box')
            boxes.append((lo, hi))
        else:
            xs = np.unique(v[:, 0]); roof = np.array([v[v[:, 0] == x, 2].max() for x in xs])
            if len(v) != 4*len(xs) or not np.all((v[:, 1] == lo[1]) | (v[:, 1] == hi[1])):
                raise ValueError('Actual bed is not the required unchanged rectangular extrusion')
            for x, top in zip(xs, roof):
                expected = {(float(x), float(y), float(z)) for y in (lo[1], hi[1]) for z in (lo[2], top)}
                if set(map(tuple, v[v[:, 0] == x])) != expected:
                    raise ValueError('Bed extrusion vertex mismatch')
            # Prove every triangle lies on the extrusion boundary, including
            # the actual piecewise-linear roof, not a bounding-box substitute.
            for tri in t:
                p = v[tri]
                if (np.all(p[:, 1] == lo[1]) or np.all(p[:, 1] == hi[1]) or np.all(p[:, 2] == lo[2])
                        or np.all(p[:, 0] == lo[0]) or np.all(p[:, 0] == hi[0])):
                    continue
                if not np.all(p[:, 2] == np.interp(p[:, 0], xs, roof)):
                    raise ValueError('Bed has non-extruded/non-profile boundary')
                indices = np.searchsorted(xs, p[:, 0])
                if indices.max()-indices.min() > 1:
                    raise ValueError('Roof triangle crosses an unverified profile breakpoint')
            profile = (xs, roof, lo, hi)
    if len(boxes) != 7 or profile is None:
        raise ValueError('All eight actual solids required')
    return boxes, profile


def pieces_at(axis, plane, boxes, profile):
    other = [a for a in range(3) if a != axis]; pieces = []
    for lo, hi in boxes:
        if lo[axis] <= plane <= hi[axis]:
            pieces.append((lo[other[0]], hi[other[0]], lo[other[1]], 0., hi[other[1]]))
    xs, roof, lo, hi = profile
    if not lo[axis] <= plane <= hi[axis]:
        return pieces
    if axis == 0:
        pieces.append((lo[1], hi[1], lo[2], 0., float(np.interp(plane, xs, roof))))
    else:
        for a, b, c, d in zip(xs, xs[1:], roof, roof[1:]):
            m = (d-c)/(b-a); q = c-m*a
            if axis == 1:
                pieces.append((a, b, lo[2], m, q))
            else:
                if max(c, d) < plane:
                    continue
                if min(c, d) < plane:
                    crossing = a+(plane-c)*(b-a)/(d-c)
                    if c < plane:
                        a = crossing
                    else:
                        b = crossing
                pieces.append((a, b, lo[1], 0., hi[1]))
    return pieces


def divergence(v, f):
    weighted = v.astype(float)*f.astype(float)
    return 2.5*(weighted[1:, :-1, :-1, 0]-weighted[:-1, :-1, :-1, 0]
        +weighted[:-1, 1:, :-1, 1]-weighted[:-1, :-1, :-1, 1]
        +weighted[:-1, :-1, 1:, 2]-weighted[:-1, :-1, :-1, 2])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inputs', type=Path, required=True)
    parser.add_argument('--apertures', type=Path, required=True)
    parser.add_argument('--pressure', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    inputs = json.loads(args.inputs.read_text()); apertures = json.loads(args.apertures.read_text())
    pressure = json.loads(args.pressure.read_text()); hashes = {}
    for receipt, path in ((inputs, args.inputs), (apertures, args.apertures), (pressure, args.pressure)):
        for p, sha in {**receipt['dependency_sha256'], **receipt['outputs_sha256']}.items():
            if p in hashes and sha != hashes[p]:
                raise ValueError('Conflicting pinned versions')
            hashes[p] = sha
        hashes[str(path.resolve())] = digest(path)
    hashes[str(Path(__file__).resolve())] = digest(__file__)
    if any(digest(p) != sha for p, sha in hashes.items()):
        raise ValueError('Pinned evidence changed')
    boxes, profile = actual_primitives(inputs['meshes'])
    shape = tuple(inputs['shape']); origin = np.array(inputs['origin_m']); h = inputs['cell_m']
    started = time.perf_counter(); rows = []; geometry = np.empty((*shape, 3), np.float32)
    for axis, path in enumerate(apertures['arrays']):
        area = np.load(path, allow_pickle=False)
        if not np.isfinite(area).all() or area.min() < 0 or area.max() > h*h:
            raise ValueError('Invalid geometric open area')
        other = [a for a in range(3) if a != axis]; max_error = 0.; worst = None
        for i in range(shape[axis]+1):
            pieces = pieces_at(axis, origin[axis]+i*h, boxes, profile)
            for j in range(shape[other[0]]):
                for k in range(shape[other[1]]):
                    lo = origin[other]+np.array([j, k])*h; hi = lo+h
                    blocked = interval_union_area(pieces, lo, hi)
                    expected = h*h*(1.-blocked/float(np.prod(hi-lo)))
                    coordinate = [0]*3; coordinate[axis] = i; coordinate[other[0]] = j; coordinate[other[1]] = k
                    error = abs(float(area[tuple(coordinate)])-expected)
                    if error > max_error:
                        max_error = error; worst = dict(index=coordinate, reference_m2=expected, actual_m2=float(area[tuple(coordinate)]))
            if i % 20 == 0:
                print('INDEPENDENT_APERTURE_REFERENCE', axis, i, time.perf_counter()-started, flush=True)
        if max_error > 2e-12:
            raise ValueError('Actual triangle apertures disagree with independent full extrusion/box area')
        rows.append(dict(axis=axis, faces=area.size, maximum_area_error_m2=max_error,
                         fixed_roundoff_allowance_m2=2e-12, worst=worst))
        slices = [slice(None)]*3; slices[axis] = slice(0, shape[axis]); geometry[..., axis] = area[tuple(slices)]/(h*h)
    pressure_checks = []; closed = np.ones(tuple(n-1 for n in shape), bool)
    for axis in range(3):
        slices = [slice(0, -1)]*3; slices[axis] = slice(1, None)
        closed &= (geometry[:-1, :-1, :-1, axis] == 0) & (geometry[tuple(slices)+(axis,)] == 0)
    for row in pressure['rows']:
        if not row['complete']:
            if row['label'] != 'geometry-fixed-native-flags' or 'CG solver diverged' not in row['error']:
                raise ValueError('Unexpected pressure experiment failure')
            pressure_checks.append(dict(label=row['label'], expected_retained_failure=row['error']))
            continue
        flags = np.load(row['arrays']['flags'], allow_pickle=False)
        mask = (flags[:-1, :-1, :-1] & pressure['native_settings']['FlagFluid']) != 0
        mask[0] = False; mask[:, 0] = False; mask[:, :, 0] = False
        isolated = int(np.count_nonzero(mask & closed))
        if isolated != row['before_pressure']['geometric_closed_fluid_cells']:
            raise ValueError('Closed-fluid-cell recount mismatch')
        stages = []
        for key, name in (('velocity-before', 'before_pressure'), ('velocity-projected', 'after_pressure'),
                          ('velocity-final-wall', 'after_final_wall')):
            velocity = np.load(row['arrays'][key], allow_pickle=False)
            values = divergence(velocity, geometry)[mask]
            rms = float(np.sqrt(np.mean(values**2))); maximum = float(np.max(np.abs(values)))
            reported = row[name]['geometric_weighted_divergence_per_second']
            # Probe multiplied float32 grids before summation; this independent
            # reference multiplies in float64, so retain a fixed ABI roundoff allowance.
            if max(abs(rms-reported['rms']), abs(maximum-reported['maximum_absolute'])) > 2e-5:
                raise ValueError('Independent geometric flux readback mismatch')
            stages.append(dict(stage=name, cells=len(values), independent_rms_per_second=rms,
                independent_maximum_per_second=maximum, fixed_float32_allowance_per_second=2e-5))
        pressure_checks.append(dict(label=row['label'], closed_fluid_cells=isolated, stages=stages))
    if any(digest(p) != sha for p, sha in hashes.items()):
        raise ValueError('Independent qualification changed inputs')
    report = dict(complete=True, accepted=False, originals_unchanged=True, geometry_reference=rows,
        independently_checked_faces=sum(r['faces'] for r in rows), pressure_checks=pressure_checks,
        seconds=time.perf_counter()-started, dependency_sha256=hashes,
        scope='All actual geometric areas independently verified; retained singular fixed-flags failure and finite rebuilt-flags flux independently checked. Not a coupled pressure/contact/surface repair or acceptance.')
    with args.output.open('x') as stream:
        json.dump(report, stream, indent=2); stream.write('\n')
    print('SUBCELL_QUALIFICATION_COMPLETE', report['independently_checked_faces'], rows, flush=True)


if __name__ == '__main__':
    main()
