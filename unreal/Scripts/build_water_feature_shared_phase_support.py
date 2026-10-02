"""All-cell/all-face solid-liquid support and full possibly-wet dual stencil.

Read-only native checkpoint. Carries uncertainty, not fitted binary flags.
Produces geometric/phase fields for later coupled pressure and transport;
does not execute either a pressure projection or a physical time step.
"""
import argparse
import hashlib
import json
from pathlib import Path
import time
import numpy as np
from qualify_water_feature_subcell_apertures import actual_primitives
from water_feature_extruded_volume import ExtrudedSolidVolume, liquid_volume_bounds, sample_phi
from water_feature_phase_faces import PhaseFaces, liquid_face_bounds


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def field_range(phi, origin, h, shape, face_axis=None):
    coordinates = np.moveaxis(np.indices(shape), 0, -1); low = np.full(shape, np.inf); high = -low.copy()
    choices = [(0,) if axis == face_axis else (0, .5, 1) for axis in range(3)]
    for x in choices[0]:
        for y in choices[1]:
            for z in choices[2]:
                value = sample_phi(phi, origin+(coordinates+np.array([x, y, z]))*h, origin, h)
                low = np.minimum(low, value); high = np.maximum(high, value)
    return low, high


def assert_bounds(lower, upper, total, tolerance, previous=None):
    if (not np.isfinite([lower, upper, total]).all() or np.any(lower < -tolerance)
            or np.any(upper < lower-tolerance) or np.any(upper > total+tolerance)):
        raise ValueError('Phase bounds violate physical geometric measure')
    if previous is not None:
        if np.any(lower < previous[0]-tolerance) or np.any(upper > previous[1]+tolerance):
            raise ValueError('Refined phase bounds do not nest')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inputs', type=Path, required=True)
    parser.add_argument('--apertures', type=Path, required=True)
    parser.add_argument('--pressure', type=Path, required=True)
    parser.add_argument('--volume', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    paths = (args.inputs, args.apertures, args.pressure, args.volume)
    reports = [json.loads(p.read_text()) for p in paths]; inp, old_areas, old_pressure, old_volume = reports; hashes = {}
    for r, path in zip(reports, paths):
        for p, sha in {**r['dependency_sha256'], **r['outputs_sha256']}.items():
            if p in hashes and hashes[p] != sha:
                raise ValueError('Conflicting preserved evidence versions')
            hashes[p] = sha
        hashes[str(path.resolve())] = digest(path)
    for name in (Path(__file__).name, 'water_feature_extruded_volume.py', 'water_feature_phase_faces.py',
                 'qualify_water_feature_subcell_apertures.py'):
        p = Path(__file__).with_name(name); hashes[str(p.resolve())] = digest(p)
    if any(digest(p) != sha for p, sha in hashes.items()):
        raise ValueError('Pinned original inputs changed')
    boxes, profile = actual_primitives(inp['meshes']); geometry = ExtrudedSolidVolume(boxes, profile); faces = PhaseFaces(geometry)
    shape = tuple(inp['shape']); origin = np.array(inp['origin_m']); h = inp['cell_m']; end = origin+np.array(shape)*h
    phi = np.load(inp['fields']['phi'], allow_pickle=False).astype(float)
    volume = np.load(old_volume['arrays']['open-cell-volume-m3'], allow_pickle=False)
    flags = np.load(old_pressure['native']['arrays']['flags'], allow_pickle=False)
    native_response = np.load(old_pressure['arrays']['response-coefficient'], allow_pickle=False)
    velocity = np.load(old_pressure['arrays']['velocity-consistent-native'], allow_pickle=False)
    if phi.shape != shape or volume.shape != shape:
        raise ValueError('Native checkpoint dimensions mismatch')
    args.output.mkdir(); arrays = {}; outputs = {}; started = time.perf_counter(); timings = {}

    def save(name, array):
        path = args.output/(name+'.npy')
        with path.open('xb') as stream:
            np.save(stream, array, allow_pickle=False)
        arrays[name] = str(path.resolve()); outputs[str(path.resolve())] = digest(path)

    cmin, cmax = field_range(phi, origin, h, shape); guard = 1e-12
    full = (cmax < -guard) & (volume > 0); possible = (cmin <= guard) & (volume > 0)
    cut = np.argwhere(possible & ~full); cell_bounds = []
    for depth in (1, 2):
        lower = np.where(full, volume, 0.); upper = lower.copy()
        for n, idx in enumerate(cut):
            key = tuple(idx); lo = origin+idx*h; hi = lo+h
            bound = liquid_volume_bounds(geometry, phi, origin, h, lo, hi, depth, guard)
            lower[key], upper[key] = bound['lower_m3'], bound['upper_m3']
            if n % 500 == 0:
                print('SHARED_CELL_PHASE', depth, n, len(cut), time.perf_counter()-started, flush=True)
        assert_bounds(lower, upper, volume, 1e-14, cell_bounds[-1] if cell_bounds else None)
        cell_bounds.append((lower, upper)); save(f'cell-liquid-lower-depth-{depth}', lower); save(f'cell-liquid-upper-depth-{depth}', upper)
    timings['cells_seconds'] = time.perf_counter()-started; face_fields = []; geometric_changes = []
    for axis in range(3):
        dims = list(shape); dims[axis] += 1; dims = tuple(dims); others = [a for a in range(3) if a != axis]
        areas = np.empty(dims); original = np.load(old_areas['arrays'][axis], allow_pickle=False)
        for i in range(dims[axis]):
            plane = origin[axis]+i*h
            for j in range(shape[others[0]]):
                for k in range(shape[others[1]]):
                    idx = [0, 0, 0]; idx[axis] = i; idx[others[0]] = j; idx[others[1]] = k
                    lo = origin[others]+np.array([j, k])*h
                    areas[tuple(idx)] = faces.area(axis, plane, lo, lo+h)
            if i % 20 == 0:
                print('SHARED_OPEN_FACE', axis, i, time.perf_counter()-started, flush=True)
        error = float(np.max(np.abs(areas-original)))
        if error > 2e-12:
            raise ValueError('Direct open-union faces disagree with original certified geometric areas')
        geometric_changes.append(dict(axis=axis, maximum_area_difference_m2=error,
            previously_positive_now_closed=int(np.count_nonzero((original > 0) & (areas == 0)))))
        save(f'open-face-area-axis-{axis}', areas)
        amin, amax = field_range(phi, origin, h, dims, axis)
        afull = (amax < -guard) & (areas > 0); acut = np.argwhere((amin <= guard) & ~afull & (areas > 0)); bounds = []
        for depth in (1, 2):
            lower = np.where(afull, areas, 0.); upper = lower.copy()
            for n, idx in enumerate(acut):
                key = tuple(idx); plane = origin[axis]+idx[axis]*h; lo = origin[others]+idx[others]*h
                b = liquid_face_bounds(faces, phi, origin, h, axis, plane, lo, lo+h, depth, guard)
                lower[key], upper[key] = b['lower_m2'], b['upper_m2']
                if n % 1500 == 0:
                    print('SHARED_FACE_PHASE', axis, depth, n, len(acut), time.perf_counter()-started, flush=True)
            assert_bounds(lower, upper, areas, 1e-13, bounds[-1] if bounds else None)
            bounds.append((lower, upper)); save(f'face-liquid-lower-axis-{axis}-depth-{depth}', lower); save(f'face-liquid-upper-axis-{axis}-depth-{depth}', upper)
        face_fields.append((areas, bounds))
    timings['cells_and_faces_seconds'] = time.perf_counter()-started
    dual_fields = []; dual_rows = []
    for axis, (areas, bounds) in enumerate(face_fields):
        # Include every possibly wet face, not just faces allowed by old flags.
        candidates = np.argwhere(bounds[-1][1] > 0); dual_total = np.zeros(areas.shape)
        lower_arrays = [np.zeros(areas.shape), np.zeros(areas.shape)]; upper_arrays = [np.zeros(areas.shape), np.zeros(areas.shape)]
        for n, idx in enumerate(candidates):
            key = tuple(idx); center = origin+(idx+.5)*h; center[axis] -= .5*h
            lo, hi = np.maximum(origin, center-.5*h), np.minimum(end, center+.5*h)
            dual_total[key], _ = geometry.integrate(lo, hi)
            # Coarse sign test must include every center plane of this dual.
            choices = [np.array([lo[a], (lo[a]+hi[a])/2, hi[a]]) for a in range(3)]
            points = np.stack(np.meshgrid(*choices, indexing='ij'), -1).reshape(-1, 3)
            values = sample_phi(phi, points, origin, h)
            if values.max() < -guard:
                for d in range(2):
                    lower_arrays[d][key] = upper_arrays[d][key] = dual_total[key]
            elif values.min() > guard:
                pass
            else:
                for d, depth in enumerate((1, 2)):
                    b = liquid_volume_bounds(geometry, phi, origin, h, lo, hi, depth, guard)
                    lower_arrays[d][key], upper_arrays[d][key] = b['lower_m3'], b['upper_m3']
            if n % 1500 == 0:
                print('SHARED_DUAL_PHASE', axis, n, len(candidates), time.perf_counter()-started, flush=True)
        save(f'open-dual-volume-axis-{axis}', dual_total)
        for d, depth in enumerate((1, 2)):
            assert_bounds(lower_arrays[d], upper_arrays[d], dual_total, 1e-14,
                          (lower_arrays[d-1], upper_arrays[d-1]) if d else None)
            save(f'dual-liquid-lower-axis-{axis}-depth-{depth}', lower_arrays[d]); save(f'dual-liquid-upper-axis-{axis}-depth-{depth}', upper_arrays[d])
        dual_fields.append((dual_total, lower_arrays, upper_arrays))
        dual_rows.append(dict(axis=axis, possibly_wet_faces=len(candidates),
            definitely_wet_faces=int(np.count_nonzero(bounds[-1][0] > 0)),
            face_wet_dual_unresolved=int(np.count_nonzero((bounds[-1][0] > 0) & (lower_arrays[-1] == 0))),
            face_possible_but_dual_dry=int(np.count_nonzero((bounds[-1][1] > 0) & (upper_arrays[-1] == 0)))))
    timings['total_seconds'] = time.perf_counter()-started
    summaries = []
    active_flat = np.argsort(np.where(native_response > 0, np.abs(velocity), -1).ravel())[-8:][::-1]
    for flat in active_flat:
        idx = [int(x) for x in np.unravel_index(flat, velocity.shape)]; key = tuple(idx[:3]); axis = idx[3]
        area, bounds = face_fields[axis]; total, lows, highs = dual_fields[axis]
        summaries.append(dict(index=idx, old_velocity_m_per_second=float(velocity[tuple(idx)])*h*2.5,
            old_response_coefficient=float(native_response[tuple(idx)]), open_area_m2=float(area[key]),
            wet_area_bounds_m2=[[float(l[key]), float(u[key])] for l, u in bounds],
            open_dual_volume_m3=float(total[key]), wet_dual_bounds_m3=[[float(l[key]), float(u[key])] for l, u in zip(lows, highs)],
            dual_omitted_because_face_proved_dry=bool(bounds[-1][1][key] == 0)))
    lower, upper = cell_bounds[-1]; oldfluid = (flags & 1) != 0
    report = dict(complete=True, accepted=False, originals_unchanged=True, frame=inp['frame'], shape=shape,
        origin_m=origin.tolist(), cell_m=h, phase_refinement_depths=[1, 2], sign_guard=guard,
        cells_checked=int(volume.size), physical_faces_checked=sum(a.size for a, _ in face_fields),
        cell_summary=dict(definitely_wet=int(np.count_nonzero(lower > 0)), possibly_wet=int(np.count_nonzero(upper > 0)),
            unresolved_wet_support=int(np.count_nonzero((lower == 0) & (upper > 0))),
            old_empty_cells_definitely_wet=int(np.count_nonzero((flags & 4 != 0) & (lower > 0))),
            old_fluid_cells_proved_dry=int(np.count_nonzero(oldfluid & (upper == 0))),
            reconstructed_liquid_volume_bounds_m3=[[float(l.sum()), float(u.sum())] for l, u in cell_bounds],
            not_conserved_mass=True), geometric_changes=geometric_changes, dual_summary=dual_rows,
        retained_fast_faces=summaries, timings=timings, arrays=arrays, outputs_sha256=outputs, dependency_sha256=hashes,
        pressure_changed=False, primary_particles_advanced=False, surface_changed=False,
        scope='All cell/physical face and every possibly wet dual support share actual solid union and cached-liquid bounds. Uncertainty retained; no pressure/inertia coefficients imposed, transport, bake or physical acceptance.')
    if any(digest(p) != sha for p, sha in hashes.items()):
        raise ValueError('Shared phase construction changed preserved inputs')
    with (args.output/'report.json').open('x') as stream:
        json.dump(report, stream, indent=2); stream.write('\n')
    print('SHARED_PHASE_SUPPORT', report['cell_summary'], dual_rows, timings, flush=True)


if __name__ == '__main__':
    main()
