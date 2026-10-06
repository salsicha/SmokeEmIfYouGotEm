"""Actual laboratory cut-cell volumes, moments and local liquid/inertia bounds.

Read-only saved native inputs; no solver step, pressure replacement or bake.
The open dual box is geometry, not a validated liquid face mass matrix.
"""
import argparse
import hashlib
import json
from pathlib import Path
import time
import numpy as np
from qualify_water_feature_subcell_apertures import actual_primitives
from water_feature_extruded_volume import ExtrudedSolidVolume, liquid_volume_bounds, sample_phi


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inputs', type=Path, required=True)
    parser.add_argument('--apertures', type=Path, required=True)
    parser.add_argument('--pressure', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    reports = [json.loads(p.read_text()) for p in (args.inputs, args.apertures, args.pressure)]
    inputs, apertures, pressure = reports; hashes = {}
    for r, path in zip(reports, (args.inputs, args.apertures, args.pressure)):
        for p, sha in {**r['dependency_sha256'], **r['outputs_sha256']}.items():
            if p in hashes and sha != hashes[p]:
                raise ValueError('Conflicting pinned evidence versions')
            hashes[p] = sha
        hashes[str(path.resolve())] = digest(path)
    for name in (Path(__file__).name, 'water_feature_extruded_volume.py', 'qualify_water_feature_subcell_apertures.py'):
        path = Path(__file__).with_name(name); hashes[str(path.resolve())] = digest(path)
    if any(digest(p) != sha for p, sha in hashes.items()):
        raise ValueError('Pinned original evidence changed')
    boxes, profile = actual_primitives(inputs['meshes']); geometry = ExtrudedSolidVolume(boxes, profile)
    shape = tuple(inputs['shape']); origin = np.array(inputs['origin_m']); h = inputs['cell_m']
    phi = np.load(inputs['fields']['phi'], allow_pickle=False)
    flags = np.load(pressure['native']['arrays']['flags'], allow_pickle=False); fluid = (flags & 1) != 0
    velocity = np.load(pressure['arrays']['velocity-consistent-native'], allow_pickle=False)
    response = np.load(pressure['arrays']['response-coefficient'], allow_pickle=False)
    fractions = np.empty((*shape, 3), float)
    for axis, path in enumerate(apertures['arrays']):
        sl = [slice(None)]*3; sl[axis] = slice(0, shape[axis])
        fractions[..., axis] = np.load(path, allow_pickle=False)[tuple(sl)]/(h*h)
    started = time.perf_counter(); volumes = np.empty(shape); moments = np.empty((*shape, 3))
    buried = np.empty(shape, bool)
    for i in range(shape[0]):
        for j in range(shape[1]):
            for k in range(shape[2]):
                index = (i, j, k); lo = origin+np.array(index)*h; hi = lo+h
                volumes[index], moments[index] = geometry.integrate(lo, hi)
                buried[index] = geometry.contains((lo+hi)/2)
        if i % 10 == 0:
            print('EXACT_OPEN_VOLUMES', i, time.perf_counter()-started, flush=True)
    if not np.isfinite([volumes, moments[..., 0]]).all() or volumes.min() < 0 or volumes.max() > h**3+1e-15:
        raise ValueError('Invalid exact represented open-cell volume')
    volume_seconds = time.perf_counter()-started
    active = response > 0
    # Fixed predeclared count; retain highest speeds rather than cherry-picking
    # a convenient cell or masking the previously rejected corner peak.
    selected = np.argsort(np.where(active, np.abs(velocity), -1).ravel())[-8:][::-1]
    face_rows = []
    for flat in selected:
        idx = [int(x) for x in np.unravel_index(flat, velocity.shape)]; axis = idx[3]
        hi_index = np.array(idx[:3]); lo_index = hi_index.copy(); lo_index[axis] -= 1
        if lo_index[axis] < 0:
            raise ValueError('Active face outside explicit native cage')
        center = origin+(hi_index+.5)*h; center[axis] -= .5*h
        lower = center-.5*h; upper = lower+h
        dual_volume, dual_moment = geometry.integrate(lower, upper)
        if dual_volume <= 0:
            raise ValueError('Active positive aperture has no geometric dual support')
        neighbors = []
        for index in (lo_index, hi_index):
            key = tuple(index); lower_cell = origin+index*h; upper_cell = lower_cell+h
            centroid = moments[key]/volumes[key] if volumes[key] > 0 else None
            bounds = []
            for depth in (1, 2, 3):
                bounds.append(liquid_volume_bounds(geometry, phi, origin, h, lower_cell, upper_cell, depth))
            if any(b['lower_m3'] < a['lower_m3']-1e-14 or b['upper_m3'] > a['upper_m3']+1e-14
                   for a, b in zip(bounds, bounds[1:])):
                raise ValueError('Local represented liquid bounds did not nest')
            neighbors.append(dict(index=index.tolist(), native_flag=int(flags[key]),
                cached_center_phi=float(phi[key]), center_in_actual_solid=bool(buried[key]),
                geometric_open_volume_m3=float(volumes[key]), geometric_open_fraction=float(volumes[key]/h**3),
                open_centroid_m=centroid.tolist() if centroid is not None else None,
                cached_phi_at_open_centroid=float(sample_phi(phi, centroid, origin, h)) if centroid is not None else None,
                liquid_bounds=bounds))
        dual_bounds = [liquid_volume_bounds(geometry, phi, origin, h, lower, upper, depth) for depth in (1, 2, 3)]
        face_rows.append(dict(index=idx, face_world_m=center.tolist(), area_fraction=float(fractions[tuple(idx)]),
            velocity_m_per_second=float(velocity[tuple(idx)])*h*2.5, response_coefficient=float(response[tuple(idx)]),
            open_dual_volume_m3=dual_volume, open_dual_fraction=dual_volume/h**3,
            open_dual_centroid_m=(dual_moment/dual_volume).tolist(), liquid_dual_bounds=dual_bounds, neighbors=neighbors))
        print('LOCAL_LIQUID_BOUNDS', idx, face_rows[-1]['velocity_m_per_second'], flush=True)
    # Check decomposition of the complete original domain against the union
    # integrated as one region. This is geometry additivity, not mass balance.
    whole_volume, whole_moment = geometry.integrate(origin, origin+np.array(shape)*h)
    difference = abs(float(volumes.sum())-whole_volume)
    moment_error = float(np.max(np.abs(moments.sum(axis=(0, 1, 2))-whole_moment)))
    if difference > 1e-11 or moment_error > 1e-10:
        raise ValueError('Complete grid/whole-domain geometric union mismatch')
    values = volumes[fluid]; zero_fluid = np.argwhere(fluid & (volumes == 0))
    minimum_index = np.unravel_index(np.argmin(np.where(fluid & (volumes > 0), volumes, np.inf)), shape)
    report = dict(complete=True, accepted=False, originals_unchanged=True, frame=inputs['frame'], shape=shape,
        cell_m=h, origin_m=origin.tolist(), geometric_cells=int(volumes.size),
        whole_open_volume_m3=whole_volume, grid_whole_volume_error_m3=difference,
        grid_whole_moment_error_m4=moment_error, volume_seconds=volume_seconds,
        geometric_fluid_cohort=dict(cells=int(fluid.sum()), zero_open_cells=len(zero_fluid),
            zero_open_indices=zero_fluid.tolist(), center_in_solid_cells=int(np.count_nonzero(fluid & buried)),
            minimum_positive_open_fraction=float(volumes[minimum_index]/h**3),
            minimum_positive_index=[int(x) for x in minimum_index],
            geometric_open_cohort_volume_m3=float(values.sum()), not_conserved_liquid=True),
        face_selection='Eight highest absolute active corrected face velocities, fixed before evaluation',
        face_rows=face_rows, arrays={}, outputs_sha256={}, dependency_sha256=hashes,
        native_particles_advanced=False, surface_changed=False, pressure_changed=False,
        scope='Exact actual extrusion/box UNION volumes and moments, local cached-liquid sign-guard bounds; not accepted inertia/transport, conserved mass or CFD/animation')
    if any(digest(p) != sha for p, sha in hashes.items()):
        raise ValueError('Read-only geometry/liquid audit changed inputs')
    args.output.mkdir()
    for name, array in (('open-cell-volume-m3', volumes), ('open-cell-first-moment-m4', moments), ('center-in-actual-solid', buried)):
        path = args.output/(name+'.npy')
        with path.open('xb') as stream:
            np.save(stream, array, allow_pickle=False)
        report['arrays'][name] = str(path.resolve()); report['outputs_sha256'][str(path.resolve())] = digest(path)
    with (args.output/'report.json').open('x') as stream:
        json.dump(report, stream, indent=2); stream.write('\n')
    print('GEOMETRIC_INERTIA_AUDIT', report['geometric_fluid_cohort'], difference, moment_error, flush=True)


if __name__ == '__main__':
    main()
