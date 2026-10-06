"""Shared actual-render interface queries; no cached foam or mesh is moved."""
import argparse
import json
from pathlib import Path
import sys
import time

import bpy
import numpy as np
import openvdb
from mathutils.bvhtree import BVHTree

sys.path.insert(0, str(Path(__file__).resolve().parent))
from water_feature_mesh_interface import MeshInterface, RenderMeshMacField, closest_triangle
from water_feature_geometry import world_coordinates
from water_feature_solid_clip import EDDY_SOLIDS, clipped_surface, remove_surface
from audit_water_feature_surface_mac import digest, quantiles


def nearest_oracle(vertices, triangles, tree):
    # Blender's BVH stores float coordinates. Expand its candidate search by
    # a conservative coordinate-rounding bound, then minimize using unchanged
    # float64 world triangles. This does not certify global exact arithmetic.
    coordinate_error = float(np.linalg.norm(np.max(np.abs(vertices.astype(np.float32).astype(float)-vertices), axis=0)))
    padding = max(4*coordinate_error, 1e-6)

    def nearest(point):
        location, _, index, distance = tree.find_nearest(point)
        if location is None:
            return None
        candidates = {index}
        candidates.update(hit[2] for hit in tree.find_nearest_range(point, distance+padding))
        if len(candidates) > 4096:
            raise ValueError('Unresolved BVH candidate neighborhood')
        points = [(closest_triangle(point, vertices[triangles[face]]), face) for face in sorted(candidates)]
        return min(points, key=lambda item: float(np.sum((point-item[0])**2)))
    return nearest, coordinate_error, padding


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--reference', type=Path, required=True)
    parser.add_argument('--calibration', type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    if args.output.exists():
        raise FileExistsError(args.output)
    started = time.perf_counter()
    source = Path(bpy.data.filepath)
    root = source.parent
    setup, cal, reference = [json.loads(p.read_text()) for p in (root/'setup.json', args.calibration, args.reference)]
    if (not reference['complete'] or not reference['originals_unchanged']
            or Path(reference['source_blend']).resolve() != source.resolve()
            or not cal['passed'] or cal['blender'] != bpy.app.version_string
            or cal['domain_dimensions_m'] != setup['dimensions_m']
            or any(cal[k] != setup[k] for k in ('resolution', 'fps'))
            or setup['case'] != 'eddy' or not setup['grid_aligned_domain']):
        raise ValueError('Preserved aligned native mesh plus matched field audit/calibration required')
    hashes = dict(reference['original_input_sha256'])
    hashes[str(args.reference.resolve())] = digest(args.reference)
    if any(digest(Path(p)) != expected for p, expected in hashes.items()):
        raise ValueError('Prior preserved input changed')
    rows = []
    for prior in reference['frames']:
        frame = prior['frame']
        bpy.context.scene.frame_set(frame)
        native = bpy.data.objects['Feature liquid'].evaluated_get(bpy.context.evaluated_depsgraph_get())
        state = native.modifiers[0].domain_settings
        shape, h = tuple(state.domain_resolution), max(setup['dimensions_m'])/setup['resolution']
        origin = np.asarray(native.matrix_world.translation)-np.asarray(shape)*h/2
        data = root/'cache'/'data'/f'fluid_data_{frame:04d}.vdb'
        arrays = [np.empty(shape, np.float32), np.empty(shape, np.float32), np.empty((*shape, 3), np.float32)]
        for name, array in zip(('phi', 'phi_obstacle', 'velocity'), arrays):
            grid = openvdb.read(str(data), name)
            if tuple(grid.metadata['file_base_resolution']) != shape:
                raise ValueError('Native grid dimensions mismatch')
            grid.copyToArray(array)
        np.testing.assert_array_equal(np.asarray(state.velocity_grid[:]).reshape((*shape[::-1], 3)).transpose(2, 1, 0, 3), arrays[2])
        derived = clipped_surface(native, [bpy.data.objects[name] for name in EDDY_SOLIDS],
            union_solids=True, contact_materials=True, triangulated=True, constrained=True)
        try:
            mesh = derived.data
            mesh.calc_loop_triangles()
            vertices = world_coordinates([v.co[:] for v in mesh.vertices], derived.matrix_world)
            triangles = np.array([t.vertices[:] for t in mesh.loop_triangles], np.int64)
            import hashlib
            geometry_hash = hashlib.sha256(vertices.tobytes()+triangles.tobytes()).hexdigest()
            if geometry_hash != prior['render_geometry_sha256']:
                raise ValueError('Actual rendered geometry changed')
            tree = BVHTree.FromPolygons(vertices.tolist(), triangles.tolist(), all_triangles=True)
            nearest, coordinate_error, padding = nearest_oracle(vertices, triangles, tree)
            water_names = {material.name for material in native.data.materials if material is not None}
            allowed = np.array([mesh.materials[mesh.polygons[t.polygon_index].material_index].name in water_names for t in mesh.loop_triangles])
            interface = MeshInterface(vertices, triangles, nearest, maximum_distance=.001, allowed_faces=allowed)
            scale = cal['inferred_raw_velocity_to_mps']/setup['resolution']
            fields = [RenderMeshMacField(*arrays, origin, (h, h, h), scale, interface=interface, radius_cells=radius) for radius in (2.5, 3.5)]
            samples, missing = [], []
            for old in prior['samples']:
                x, y, _ = old['position_m']
                hit, _, face, _ = tree.ray_cast((x, y, origin[2]+shape[2]*h), (0, 0, -1))
                if hit is None or not allowed[face] or abs(interface.normals[face, 2]) < 1e-8:
                    missing.append(dict(column=old['column'], reason='No supported top free-surface triangle'))
                    continue
                normal = interface.normals[face]
                if normal[2] <= 0:
                    raise ValueError('Top interface winding is not outward')
                # NEW geometric queries from the actual triangle's plane, not
                # projection/lifting of any existing particle or trajectory.
                p = np.array([x, y, (normal @ vertices[triangles[face, 0]]-normal[0]*x-normal[1]*y)/normal[2]])
                if np.linalg.norm(closest_triangle(p, vertices[triangles[face]])-p) > 1e-10:
                    missing.append(dict(column=old['column'], reason='Rounded BVH ray hit extrapolates beyond the actual float64 triangle'))
                    continue
                surface = interface.sample(p)
                if surface is None or surface['gradient'] is None:
                    missing.append(dict(column=old['column'], reason='Undefined/unsupported actual interface normal'))
                    continue
                if abs(surface['phi_m']) > 1e-10:
                    missing.append(dict(column=old['column'], reason='Ray-derived query not on actual interface within0.1nm', residual_m=surface['phi_m']))
                    continue
                normal = surface['gradient']
                deltas = [interface.sample(p+direction*5e-5*normal) for direction in (-1, 1)]
                sign_error = max(abs(value['phi_m']-direction*5e-5) for value, direction in zip(deltas, (-1, 1))) if all(value is not None for value in deltas) else None
                failed_control = None
                if sign_error is not None and sign_error > 1e-8:
                    failed_control = dict(frame=frame, column=old['column'], position_m=p.tolist(),
                        ray_triangle=int(face), nearest_triangle=surface['triangle'],
                        shared_residual_m=surface['phi_m'], ray_normal=normal.tolist(),
                        nearest_gradient=surface['gradient'].tolist(),
                        offset_phi_m=[value['phi_m'] for value in deltas],
                        offset_nearest_triangles=[value['triangle'] for value in deltas],
                        sign_distance_error_m=sign_error)
                # Completeness means every query is reported, not that a failed
                # normal neighborhood is accepted. Do not sample/animate its
                # velocity or adjust the displacement until it passes.
                normal_supported = sign_error is not None and sign_error <= 1e-8
                fits = [field.sample(p) for field in fields] if normal_supported else [None, None]
                samples.append(dict(column=old['column'], position_m=p.tolist(),
                    shared_surface_residual_m=surface['phi_m'], feature=surface['feature'],
                    local_sign_distance_error_m=sign_error,
                    normal_neighborhood_supported=normal_supported, failed_control=failed_control,
                    base_phi_zero_height_minus_mesh_m=float(old['position_m'][2]-p[2]),
                    fits=[dict(velocity_mps=value[0].tolist(), diagnostics=value[1]) if value is not None else None for value in fits],
                    radius_sensitivity_mps=float(np.linalg.norm(fits[0][0]-fits[1][0])) if all(value is not None for value in fits) else None))
            row = dict(frame=frame, render_geometry_sha256=geometry_hash,
                topology='Closed consistently oriented edges and single-cycle vertex links checked; no self-intersection proof',
                total_signed_mesh_volume_m3=interface.volume, free_surface_triangles=int(allowed.sum()),
                bvh_coordinate_rounding_bound_m=coordinate_error, bvh_candidate_padding_m=padding,
                prior_columns=len(prior['samples']), actual_surface_queries=len(samples), missing=missing,
                supported_fit_counts=[sum(s['fits'][index] is not None for s in samples) for index in (0, 1)],
                maximum_shared_surface_residual_m=max((abs(s['shared_surface_residual_m']) for s in samples), default=None),
                maximum_local_sign_distance_error_m=max((s['local_sign_distance_error_m'] for s in samples if s['local_sign_distance_error_m'] is not None), default=None),
                failed_normal_neighborhoods=sum(not s['normal_neighborhood_supported'] for s in samples),
                radius_sensitivity_mps_quantiles=quantiles([s['radius_sensitivity_mps'] for s in samples if s['radius_sensitivity_mps'] is not None]),
                samples=samples)
            rows.append(row)
            print('SHARED_MESH_INTERFACE_FRAME', json.dumps({key: value for key, value in row.items() if key not in ('samples', 'missing')}), flush=True)
        finally:
            remove_surface(derived)
    if any(digest(Path(p)) != expected for p, expected in hashes.items()):
        raise ValueError('Preserved input changed during new audit')
    report = dict(complete=True, accepted=False, originals_unchanged=True, original_input_sha256=hashes,
        frames=rows, elapsed_s=time.perf_counter()-started,
        source_code_sha256={p.name: digest(p) for p in (Path(__file__), Path(__file__).with_name('water_feature_mesh_interface.py'), Path(__file__).with_name('water_feature_surface_mac.py'))},
        limitations='NEW geometric queries, not moved/reclassified cached foam. Frozen actual-render interface with angle-weighted sign, 1mm distance band; no unique normal on true mesh creases at zero distance. Topology and local sign controls are sampled geometric validation, not an exhaustive self-intersection/orientation certificate. Inferred one-sided MAC fit remains unaccepted; no temporal support, liquid correction, foam interaction, native animation, new rendering, game integration or FPS claim. Original rendered geometry and inputs unchanged.')
    with args.output.open('x') as stream:
        json.dump(report, stream, indent=2)


if __name__ == '__main__':
    main()
