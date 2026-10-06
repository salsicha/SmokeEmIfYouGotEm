"""Actual moving captured-mesh/field kinematic check; no foam/cache writes."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import time

import bpy
import numpy as np
import openvdb

sys.path.insert(0, str(Path(__file__).resolve().parent))
from water_feature_geometry import world_coordinates
from water_feature_solid_clip import EDDY_SOLIDS, clipped_surface, remove_surface
from water_feature_mesh_interface import MeshInterface, RenderMeshMacField
from water_feature_triangle_nearest import TriangleNearest
from water_feature_surface_kinematics import kinematic_condition
from water_feature_dense_mac import BITS, trilinear
from audit_water_feature_surface_mac import digest, quantiles


def raw_staggered_probe(field, point):
    """Unqualified cache comparison ONLY; ghost/extrapolation validity unknown.

    Expose every component's strict-source corner count. This MUST NOT become
    a replacement surface sampler just because its residual looks smaller.
    """
    cell = (point-field.interior.origin)/field.h
    values, support_counts = [], []
    for axis in range(3):
        offset = np.full(3, .5); offset[axis] = 0.
        coordinate = cell-offset
        value = trilinear(field.interior.velocity[..., axis], coordinate)
        base = np.floor(coordinate).astype(int)
        ids = base+BITS
        if (value is None or np.any(ids < 0)
                or np.any(ids >= np.asarray(field.interior.phi.shape))):
            return None
        support_counts.append(int(field.interior.face_support[axis][tuple(ids.T)].sum()))
        values.append(float(value)*field.interior.scale)
    return dict(velocity_mps=values, strict_liquid_liquid_corner_counts=support_counts,
                accepted=False, extrapolated_air_face_validity_proven=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--reference', type=Path, required=True)
    parser.add_argument('--calibration', type=Path, required=True)
    parser.add_argument('--frame', type=int, default=192)
    args = parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    if args.output.exists():
        raise FileExistsError(args.output)
    started = time.perf_counter()
    source, root = Path(bpy.data.filepath), Path(bpy.data.filepath).parent
    setup, cal, reference = [json.loads(p.read_text()) for p in (root/'setup.json', args.calibration, args.reference)]
    if (not reference['complete'] or not reference['originals_unchanged']
            or not cal['passed'] or cal['blender'] != bpy.app.version_string
            or setup['case'] != 'eddy' or not setup['grid_aligned_domain']
            or cal['domain_dimensions_m'] != setup['dimensions_m']
            or any(cal[k] != setup[k] for k in ('fps', 'resolution'))
            or not 3 <= args.frame <= setup['frames']-2
            or bpy.context.scene.render.fps != setup['fps']
            or bpy.context.scene.render.fps_base != 1.):
        raise ValueError('Matched captured eddy fields, actual mesh reference and calibrated playback clock required')
    dt = 1/setup['fps']
    prior = next(row for row in reference['frames'] if row['frame'] == args.frame)
    hashes = dict(reference['original_input_sha256'])
    for path in (source, root/'setup.json', args.calibration, args.reference):
        hashes[str(path.resolve())] = digest(path)
    if any(digest(Path(path)) != sha for path, sha in hashes.items()):
        raise ValueError('Preserved input changed')
    interfaces, geometries, fields, rows = {}, [], None, []
    h = max(setup['dimensions_m'])/setup['resolution']
    for frame in range(args.frame-2, args.frame+3):
        bpy.context.scene.frame_set(frame)
        native = bpy.data.objects['Feature liquid'].evaluated_get(bpy.context.evaluated_depsgraph_get())
        state = native.modifiers[0].domain_settings
        if state.time_scale != 1. or state.simulation_method != cal.get('simulation_method', 'FLIP'):
            raise ValueError('Default calibrated time scale and solver required; no artificial retiming')
        data = root/'cache'/'data'/f'fluid_data_{frame:04d}.vdb'
        mesh_path = root/'cache'/'mesh'/f'fluid_mesh_{frame:04d}.bobj.gz'
        for path in (data, mesh_path):
            hashes[str(path.resolve())] = digest(path)
        derived = clipped_surface(native, [bpy.data.objects[name] for name in EDDY_SOLIDS],
            union_solids=True, contact_materials=True, triangulated=True, constrained=True)
        try:
            mesh = derived.data
            mesh.calc_loop_triangles()
            vertices = world_coordinates([v.co[:] for v in mesh.vertices], derived.matrix_world)
            triangles = np.array([t.vertices[:] for t in mesh.loop_triangles], np.int64)
            geometry_hash = hashlib.sha256(vertices.tobytes()+triangles.tobytes()).hexdigest()
            if frame == args.frame and geometry_hash != prior['render_geometry_sha256']:
                raise ValueError('Central captured geometry changed')
            water_names = {m.name for m in native.data.materials if m is not None}
            allowed = np.array([mesh.materials[mesh.polygons[t.polygon_index].material_index].name in water_names for t in mesh.loop_triangles])
            nearest = TriangleNearest(vertices, triangles)
            # Neighboring signed-distance probes are Eulerian locations, not
            # surface particles. Declare their finite search band explicitly.
            interface = MeshInterface(vertices, triangles, nearest,
                                      maximum_distance=3*h, allowed_faces=allowed)
            interfaces[frame] = interface
            geometries.append(dict(frame=frame, render_geometry_sha256=geometry_hash,
                triangle_count=len(triangles), signed_mesh_volume_m3=interface.volume,
                free_surface_triangles=int(allowed.sum())))
            if frame == args.frame:
                shape = tuple(state.domain_resolution)
                np.testing.assert_allclose(state.cell_size, [h]*3, atol=1e-7, rtol=0)
                origin = np.asarray(native.matrix_world.translation)-np.asarray(shape)*h/2
                arrays = [np.empty(shape, np.float32), np.empty(shape, np.float32), np.empty((*shape, 3), np.float32)]
                for name, array in zip(('phi', 'phi_obstacle', 'velocity'), arrays):
                    grid = openvdb.read(str(data), name)
                    if tuple(grid.metadata['file_base_resolution']) != shape:
                        raise ValueError('Captured field dimensions mismatch')
                    if name == 'velocity' and grid.metadata['class'] != 'staggered':
                        raise ValueError('Native staggered MAC velocity required')
                    grid.copyToArray(array)
                np.testing.assert_array_equal(np.asarray(state.velocity_grid[:]).reshape((*shape[::-1], 3)).transpose(2, 1, 0, 3), arrays[2])
                scale = cal['inferred_raw_velocity_to_mps']/setup['resolution']
                fields = [RenderMeshMacField(*arrays, origin, (h, h, h), scale,
                    interface=interface, radius_cells=radius) for radius in (2.5, 3.5)]
        finally:
            remove_surface(derived)
        print('KINEMATIC_MESH', json.dumps(geometries[-1]), flush=True)
    for index, old in enumerate(prior['samples']):
        p = np.asarray(old['position_m'])
        samples = [interfaces[frame].sample(p) for frame in range(args.frame-2, args.frame+3)]
        row = dict(index=index, column=old['column'], position_m=p.tolist(),
            prior_normal_neighborhood_supported=old['normal_neighborhood_supported'],
            signed_mesh_distance_m=[s['phi_m'] if s else None for s in samples],
            missing_frames=[frame for frame, s in zip(range(args.frame-2, args.frame+3), samples) if s is None],
            fits=[], conditions=[])
        current = samples[2]
        if current is None or current['gradient'] is None:
            row['status'] = 'Unsupported central interface/normal'
        elif any(s is None for s in samples):
            row['status'] = 'Missing temporal free-surface distance support'
        else:
            if abs(current['phi_m']) > 1e-10:
                raise ValueError('Prespecified central query not on unchanged actual surface')
            fitted = [field.sample(p) for field in fields]
            for fit in fitted:
                row['fits'].append(dict(velocity_mps=fit[0].tolist(), diagnostics=fit[1]) if fit else None)
                row['conditions'].append(kinematic_condition(*row['signed_mesh_distance_m'], dt,
                    current['gradient'], fit[0]) if fit else None)
            row['status'] = 'measured' if all(fit is not None for fit in fitted) else 'Missing one-sided velocity fit'
            row['radius_sensitivity_mps'] = float(np.linalg.norm(fitted[0][0]-fitted[1][0])) if all(fit is not None for fit in fitted) else None
            raw = raw_staggered_probe(fields[0], p)
            row['unqualified_raw_mac_comparison'] = raw
            row['unqualified_raw_mac_condition'] = kinematic_condition(*row['signed_mesh_distance_m'], dt,
                current['gradient'], raw['velocity_mps']) if raw else None
        rows.append(row)
    if any(digest(Path(path)) != sha for path, sha in hashes.items()):
        raise ValueError('Preserved input changed during kinematic audit')
    summaries = []
    for radius_index in (0, 1):
        values = [row['conditions'][radius_index] for row in rows if len(row['conditions']) == 2 and row['conditions'][radius_index] is not None]
        summaries.append(dict(radius_cells=(2.5, 3.5)[radius_index], measured_queries=len(values),
            absolute_normal_mismatch_mps_quantiles=quantiles([abs(v['signed_normal_mismatch_mps']) for v in values]),
            temporal_stencil_disagreement_mps_quantiles=quantiles([v['temporal_stencil_disagreement_mps'] for v in values]),
            required_normal_velocity_mps_quantiles=quantiles([v['required_surface_normal_velocity_mps'] for v in values]),
            fitted_normal_velocity_mps_quantiles=quantiles([v['velocity_normal_mps'] for v in values])))
    raw_conditions = [row['unqualified_raw_mac_condition'] for row in rows
                      if row.get('unqualified_raw_mac_condition') is not None]
    raw_summary = dict(measured_queries=len(raw_conditions), accepted=False,
        absolute_normal_mismatch_mps_quantiles=quantiles([abs(c['signed_normal_mismatch_mps']) for c in raw_conditions]),
        scope='Raw staggered cache comparison only; air/extrapolated-face validity unproven. Not an enabled surface sampler.')
    report = dict(complete=True, accepted=False, originals_unchanged=True, frame=args.frame,
        calibrated_dt_seconds=dt, playback_fps=setup['fps'], domain_time_scale=1.,
        raw_grid_velocity_to_mps=scale, nearest_distance_search_band_m=3*h,
        prior_columns=prior['prior_columns'], prior_missing=prior['missing'], source_queries=len(rows),
        original_input_sha256=hashes, geometries=geometries, rows=rows, radius_summaries=summaries,
        unqualified_raw_mac_summary=raw_summary,
        elapsed_s=time.perf_counter()-started,
        source_code_sha256={path.name: digest(path) for path in (Path(__file__),
            Path(__file__).with_name('water_feature_surface_kinematics.py'), Path(__file__).with_name('water_feature_triangle_nearest.py'))},
        limitations='Actual five captured meshes and calibrated central native velocity; Eulerian signed-distance finite-time kinematic diagnostics only. No retiming, forced velocity correction, temporal interpolation, marker/foam simulation, cache/geometry modification or physical/visual acceptance. One-sided velocity reconstruction remains inferred/radius-sensitive. Closed topology/positive total volume do not prove global self-intersection absence. Missing and previously failed-normal controls are retained, not qualified for transport.')
    with args.output.open('x') as stream:
        json.dump(report, stream, indent=2)
    print('KINEMATIC_RESULT', json.dumps({k: v for k, v in report.items() if k not in ('rows', 'geometries', 'original_input_sha256', 'source_code_sha256', 'prior_missing')}), flush=True)


if __name__ == '__main__':
    main()
