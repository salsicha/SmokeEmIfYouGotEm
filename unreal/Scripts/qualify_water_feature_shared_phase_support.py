"""Independent all-stencil phase qualification; no construction helper imports.

Uses separately integrated columns and cached-center interpolation. Numeric
roundoff allowances are not permission to accept physical solver accuracy.
"""
import argparse
import hashlib
import itertools
import json
from pathlib import Path
import time
import numpy as np
from qualify_water_feature_geometric_inertia import Reference, field_value, reference_liquid
from qualify_water_feature_subcell_apertures import actual_primitives, pieces_at, interval_union_area


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def half_lattice(phi):
    """Independent tensor-product center/face interpolation on half-cell nodes."""
    result = phi.astype(float)
    for axis in range(3):
        dims = list(result.shape); n = dims[axis]; dims[axis] = 2*n+1; new = np.empty(dims)
        centers = [slice(None)]*3; centers[axis] = slice(1, None, 2); new[tuple(centers)] = result
        lo = [slice(None)]*3; hi = list(lo); dest = list(lo)
        lo[axis] = slice(None, -1); hi[axis] = slice(1, None); dest[axis] = slice(2, -1, 2)
        new[tuple(dest)] = (result[tuple(lo)]+result[tuple(hi)])/2
        for edge, src in ((0, 0), (2*n, n-1)):
            dest = [slice(None)]*3; source = list(dest); dest[axis] = edge; source[axis] = src
            new[tuple(dest)] = result[tuple(source)]
        result = new
    return result


def ranges(half, shape, face_axis=None):
    low = np.full(shape, np.inf); high = -low.copy()
    choices = [(0,) if a == face_axis else (0, 1, 2) for a in range(3)]
    for offset in itertools.product(*choices):
        sl = tuple(slice(o, o+2*n, 2) for o, n in zip(offset, shape)); v = half[sl]
        low = np.minimum(low, v); high = np.maximum(high, v)
    return low, high


class FaceReference:
    def __init__(self, boxes, profile):
        self.boxes, self.profile = boxes, profile; self.cache = {}

    def area(self, axis, plane, lo, hi):
        key = (axis, float(plane))
        if key not in self.cache:
            self.cache[key] = pieces_at(axis, plane, self.boxes, self.profile)
        # Preserve the independently computed subtraction roundoff in error
        # comparisons; only negative unphysical reference area becomes zero.
        return max(0., float(np.prod(hi-lo))-interval_union_area(self.cache[key], lo, hi))

    def liquid(self, phi, origin, h, axis, plane, lo, hi, depth, guard):
        other = [a for a in range(3) if a != axis]; events = []
        for a, world_axis in enumerate(other):
            centers = origin[world_axis]+(np.arange(phi.shape[world_axis])+.5)*h
            events.append(sorted({lo[a], hi[a], *centers[(centers > lo[a]) & (centers < hi[a])]}))
        pending = [(np.array([a, c]), np.array([b, d]), 0)
                   for a, b in zip(events[0], events[0][1:]) for c, d in zip(events[1], events[1][1:])]
        lower = upper = 0.
        while pending:
            a, b, n = pending.pop(); area = self.area(axis, plane, a, b)
            if area == 0:
                continue
            values = []
            for bits in itertools.product((0, 1), repeat=2):
                point = np.empty(3); point[axis] = plane; point[other] = np.where(bits, b, a)
                values.append(field_value(phi, point, origin, h))
            if max(values) < -guard:
                lower += area; upper += area
            elif min(values) > guard:
                continue
            elif n == depth:
                upper += area
            else:
                mid = a+(b-a)/2
                if np.any((mid == a) | (mid == b)):
                    upper += area
                else:
                    pending.extend((np.where(bits, mid, a), np.where(bits, b, mid), n+1)
                                   for bits in itertools.product((0, 1), repeat=2))
        return lower, upper


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('audit', 'inputs', 'volume', 'pressure', 'output'):
        parser.add_argument('--'+name, type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    paths = (args.audit, args.inputs, args.volume, args.pressure); reports = [json.loads(p.read_text()) for p in paths]
    audit, inp, old_volume, old_pressure = reports; hashes = {}
    for report, path in zip(reports, paths):
        for p, sha in {**report['dependency_sha256'], **report['outputs_sha256']}.items():
            if p in hashes and hashes[p] != sha:
                raise ValueError('Conflicting preserved evidence versions')
            hashes[p] = sha
        hashes[str(path.resolve())] = digest(path)
    for name in (Path(__file__).name, 'qualify_water_feature_geometric_inertia.py', 'qualify_water_feature_subcell_apertures.py'):
        p = Path(__file__).with_name(name); hashes[str(p.resolve())] = digest(p)
    if any(digest(p) != sha for p, sha in hashes.items()):
        raise ValueError('Pinned source/evidence changed')
    shape = tuple(inp['shape']); origin = np.array(inp['origin_m']); h = inp['cell_m']; end = origin+np.array(shape)*h
    phi = np.load(inp['fields']['phi'], allow_pickle=False).astype(float); half = half_lattice(phi)
    volumes = np.load(old_volume['arrays']['open-cell-volume-m3'], allow_pickle=False)
    geometry = Reference(inp['meshes']); boxes, profile = actual_primitives(inp['meshes']); faces = FaceReference(boxes, profile)
    arrays = {key: np.load(path, allow_pickle=False) for key, path in audit['arrays'].items()}; guard = audit['sign_guard']
    if any(not np.isfinite(a).all() for a in arrays.values()):
        raise ValueError('Nonfinite shared phase array')
    if audit['phase_refinement_depths'] != [1, 2] or guard != 1e-12:
        raise ValueError('Unplanned bound refinement or sign threshold')
    low, high = ranges(half, shape); full = (high < -guard) & (volumes > 0)
    cut = np.argwhere((low <= guard) & ~full & (volumes > 0)); cell_error = area_error = dual_error = 0.
    started = time.perf_counter(); checked_cell_bounds = checked_face_bounds = checked_dual_bounds = 0
    for depth in (1, 2):
        expected_lo = np.where(full, volumes, 0.); expected_hi = expected_lo.copy()
        for n, idx in enumerate(cut):
            lo = origin+idx*h; hi = lo+h
            expected_lo[tuple(idx)], expected_hi[tuple(idx)] = reference_liquid(geometry, phi, origin, h, lo, hi, depth, guard)
            if n % 1000 == 0:
                print('INDEPENDENT_SHARED_CELL', depth, n, len(cut), time.perf_counter()-started, flush=True)
        for prefix, expected in (('lower', expected_lo), ('upper', expected_hi)):
            actual = arrays[f'cell-liquid-{prefix}-depth-{depth}']
            if actual.shape != shape:
                raise ValueError('Cell field coverage incomplete')
            cell_error = max(cell_error, float(np.max(np.abs(actual-expected))))
        checked_cell_bounds += int(volumes.size)
    face_arrays = []; geometry_area_error = 0.
    for axis in range(3):
        dims = list(shape); dims[axis] += 1; dims = tuple(dims); other = [a for a in range(3) if a != axis]
        actual_area = arrays[f'open-face-area-axis-{axis}']; reference_area = np.empty(dims)
        if actual_area.shape != dims:
            raise ValueError('N+1 physical face coverage missing')
        for i in range(dims[axis]):
            for j in range(shape[other[0]]):
                for k in range(shape[other[1]]):
                    idx = [0, 0, 0]; idx[axis] = i; idx[other[0]] = j; idx[other[1]] = k
                    lo = origin[other]+np.array([j, k])*h
                    reference_area[tuple(idx)] = faces.area(axis, origin[axis]+i*h, lo, lo+h)
            if i % 30 == 0:
                print('INDEPENDENT_SHARED_AREA', axis, i, time.perf_counter()-started, flush=True)
        geometry_area_error = max(geometry_area_error, float(np.max(np.abs(actual_area-reference_area))))
        amin, amax = ranges(half, dims, axis); afull = (amax < -guard) & (actual_area > 0)
        acut = np.argwhere((amin <= guard) & ~afull & (actual_area > 0))
        for depth in (1, 2):
            expected_lo = np.where(afull, reference_area, 0.); expected_hi = expected_lo.copy()
            for n, idx in enumerate(acut):
                lo = origin[other]+idx[other]*h; plane = origin[axis]+idx[axis]*h
                expected_lo[tuple(idx)], expected_hi[tuple(idx)] = faces.liquid(phi, origin, h, axis, plane, lo, lo+h, depth, guard)
                if n % 2500 == 0:
                    print('INDEPENDENT_SHARED_FACE', axis, depth, n, len(acut), time.perf_counter()-started, flush=True)
            for prefix, expected in (('lower', expected_lo), ('upper', expected_hi)):
                actual = arrays[f'face-liquid-{prefix}-axis-{axis}-depth-{depth}']
                if actual.shape != dims:
                    raise ValueError('Face phase coverage incomplete')
                area_error = max(area_error, float(np.max(np.abs(actual-expected))))
            checked_face_bounds += int(actual_area.size)
        face_arrays.append(actual_area)
    for axis in range(3):
        selected = arrays[f'face-liquid-upper-axis-{axis}-depth-2'] > 0; candidates = np.argwhere(selected)
        total = arrays[f'open-dual-volume-axis-{axis}']; lower = [arrays[f'dual-liquid-lower-axis-{axis}-depth-{d}'] for d in (1, 2)]
        upper = [arrays[f'dual-liquid-upper-axis-{axis}-depth-{d}'] for d in (1, 2)]
        if total.shape != face_arrays[axis].shape or any(x.shape != total.shape for x in lower+upper):
            raise ValueError('Candidate dual field coverage missing')
        if any(np.any(x[~selected] != 0) for x in [total, *lower, *upper]):
            raise ValueError('Omitted proved-dry-face dual scope misrepresented')
        for n, idx in enumerate(candidates):
            key = tuple(idx); center = origin+(idx+.5)*h; center[axis] -= .5*h
            lo, hi = np.maximum(origin, center-.5*h), np.minimum(end, center+.5*h)
            vol, _ = geometry.integrate(lo, hi); dual_error = max(dual_error, abs(vol-total[key]))
            # Evaluate all cached-center extrema independently; same aligned
            # dual bounds contain at most one center-plane split per axis.
            points = itertools.product(*[(lo[a], (lo[a]+hi[a])/2, hi[a]) for a in range(3)])
            values = [field_value(phi, p, origin, h) for p in points]
            for d, depth in enumerate((1, 2)):
                if max(values) < -guard:
                    a = b = vol
                elif min(values) > guard:
                    a = b = 0.
                else:
                    a, b = reference_liquid(geometry, phi, origin, h, lo, hi, depth, guard)
                dual_error = max(dual_error, abs(a-lower[d][key]), abs(b-upper[d][key]))
                checked_dual_bounds += 1
            if n % 5000 == 0:
                print('INDEPENDENT_SHARED_DUAL', axis, n, len(candidates), time.perf_counter()-started, flush=True)
    if max(cell_error, dual_error) > 2e-14 or max(area_error, geometry_area_error) > 2e-13:
        raise ValueError('Independent shared-phase fields exceed fixed numeric allowances')
    old_v = np.load(old_pressure['arrays']['velocity-consistent-native'], allow_pickle=False)
    old_r = np.load(old_pressure['arrays']['response-coefficient'], allow_pickle=False)
    expected = [[int(x) for x in np.unravel_index(i, old_v.shape)]
                for i in np.argsort(np.where(old_r > 0, np.abs(old_v), -1).ravel())[-8:][::-1]]
    if expected != [r['index'] for r in audit['retained_fast_faces']]:
        raise ValueError('Highest-speed counterexample selection changed')
    for row in audit['retained_fast_faces']:
        idx = row['index']; key = tuple(idx[:3]); axis = idx[3]
        if row['old_velocity_m_per_second'] != float(old_v[tuple(idx)])*h*2.5:
            raise ValueError('Retained speed does not match actual native readback')
        for d, depth in enumerate((1, 2)):
            pair = [float(arrays[f'face-liquid-{prefix}-axis-{axis}-depth-{depth}'][key]) for prefix in ('lower', 'upper')]
            if pair != row['wet_area_bounds_m2'][d]:
                raise ValueError('Retained face measure does not match full fields')
    result = dict(complete=True, accepted=False, originals_unchanged=True,
        independently_checked_cell_bounds=checked_cell_bounds, independently_checked_face_bounds=checked_face_bounds,
        independently_checked_dual_bounds=checked_dual_bounds, maximum_cell_volume_error_m3=cell_error,
        maximum_dual_volume_error_m3=dual_error, maximum_phase_area_error_m2=area_error,
        maximum_geometric_area_error_m2=geometry_area_error, seconds=time.perf_counter()-started,
        dependency_sha256=hashes, complete_n_plus_one_face_coverage=True,
        scope='Independent full stored-cell/face and all declared possibly-wet dual phase bounds. Reference geometric-area subtraction has roundoff. No physical inertia, pressure/transport step, conservation, animation or game acceptance.')
    if any(digest(p) != sha for p, sha in hashes.items()):
        raise ValueError('Qualification changed preserved evidence')
    with args.output.open('x') as stream:
        json.dump(result, stream, indent=2); stream.write('\n')
    print('SHARED_PHASE_QUALIFIED', {k: v for k, v in result.items() if k != 'dependency_sha256'}, flush=True)


if __name__ == '__main__':
    main()
