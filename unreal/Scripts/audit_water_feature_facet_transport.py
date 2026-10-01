"""Fresh static-mesh kinematic paths and native event-key playback checks.

Not cached foam identities, prescribed physical water velocity or liquid time
evolution. No original geometry/cache is moved or overwritten.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import time

import bpy
import numpy as np
from mathutils.bvhtree import BVHTree

sys.path.insert(0, str(Path(__file__).resolve().parent))
from water_feature_geometry import world_coordinates
from water_feature_solid_clip import EDDY_SOLIDS, clipped_surface, remove_surface
from water_feature_mesh_interface import MeshInterface
from water_feature_facet_transport import FacetTransport
from water_feature_triangle_nearest import TriangleNearest
from audit_water_feature_mesh_interface import nearest_oracle
from audit_water_feature_surface_mac import digest


def path_at(path, seconds):
    for a, b in zip(path, path[1:]):
        if a['seconds'] <= seconds <= b['seconds'] and b['seconds'] > a['seconds']:
            fraction = (seconds-a['seconds'])/(b['seconds']-a['seconds'])
            return (1-fraction)*np.array(a['position_m'])+fraction*np.array(b['position_m'])
    if seconds == path[-1]['seconds']:
        return np.array(path[-1]['position_m'])
    raise ValueError('No supported recorded path segment at requested time')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--reference', type=Path, required=True)
    parser.add_argument('--frame', type=int, default=192)
    args = parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    if args.output.exists():
        raise FileExistsError(args.output)
    started = time.perf_counter()
    reference = json.loads(args.reference.read_text())
    if not reference['complete'] or not reference['originals_unchanged']:
        raise ValueError('Complete preserved shared-interface audit required')
    hashes = dict(reference['original_input_sha256'])
    hashes[str(args.reference.resolve())] = digest(args.reference)
    if any(digest(Path(path)) != sha for path, sha in hashes.items()):
        raise ValueError('Preserved original or receipt changed')
    prior = next(row for row in reference['frames'] if row['frame'] == args.frame)
    bpy.context.scene.frame_set(args.frame)
    native = bpy.data.objects['Feature liquid'].evaluated_get(bpy.context.evaluated_depsgraph_get())
    derived = clipped_surface(native, [bpy.data.objects[name] for name in EDDY_SOLIDS],
        union_solids=True, contact_materials=True, triangulated=True, constrained=True)
    created, rows = [], []
    fps, duration, speed = 24, 2., .05
    try:
        mesh = derived.data
        mesh.calc_loop_triangles()
        vertices = world_coordinates([v.co[:] for v in mesh.vertices], derived.matrix_world)
        triangles = np.array([t.vertices[:] for t in mesh.loop_triangles], np.int64)
        geometry_hash = hashlib.sha256(vertices.tobytes()+triangles.tobytes()).hexdigest()
        if geometry_hash != prior['render_geometry_sha256']:
            raise ValueError('Preserved rendered geometry changed')
        tree = BVHTree.FromPolygons(vertices.tolist(), triangles.tolist(), all_triangles=True)
        legacy_nearest, rounding, padding = nearest_oracle(vertices, triangles, tree)
        nearest = TriangleNearest(vertices, triangles)
        water_names = {material.name for material in native.data.materials if material is not None}
        allowed = np.array([mesh.materials[mesh.polygons[t.polygon_index].material_index].name in water_names for t in mesh.loop_triangles])
        interface = MeshInterface(vertices, triangles, nearest, allowed_faces=allowed)
        walker = FacetTransport(interface)
        for index, sample in enumerate(prior['samples']):
            p = np.array(sample['position_m'])
            hit = interface.sample(p)
            if hit is None or hit['gradient'] is None:
                rows.append(dict(index=index, column=sample['column'], status='unsupported initial facet', complete=False))
                continue
            face = hit['triangle']
            normal = interface.normals[face]
            direction = np.array([1., .371, 0.])
            direction -= (direction @ normal)*normal
            v = speed*direction/np.linalg.norm(direction)
            try:
                whole = walker.walk(p, v, face, duration)
                fine_p, fine_v, fine_face, fine_status = p.copy(), v.copy(), face, 'complete'
                for _ in range(20):
                    fine = walker.walk(fine_p, fine_v, fine_face, duration/20)
                    if not fine['complete']:
                        fine_status = fine['status']
                        break
                    fine_p, fine_v, fine_face = np.array(fine['position_m']), np.array(fine['velocity_mps']), fine['face']
                signed, split, worst_segment = 0., None, None
                for segment, (a, b) in enumerate(zip(whole['path'], whole['path'][1:])):
                    for fraction in (.25, .5, .75):
                        q = (1-fraction)*np.array(a['position_m'])+fraction*np.array(b['position_m'])
                        nearest_q, nearest_face = nearest(q)
                        distance = float(np.linalg.norm(q-nearest_q))
                        if distance > signed:
                            signed = distance
                            worst_segment = dict(segment=segment, fraction=fraction,
                                point_m=q.tolist(), nearest_point_m=nearest_q.tolist(),
                                nearest_face=int(nearest_face), segment_face=b['face'],
                                nearest_distance_m=distance)
                if whole['complete'] and fine_status == 'complete':
                    split = float(np.linalg.norm(fine_p-np.array(whole['position_m'])))
                failures = []
                if split is not None and split > 1e-8:
                    failures.append('Static geodesic partition check exceeds10nm')
                if signed > 1e-8:
                    failures.append('Recorded segment distance exceeds10nm')
                if whole['maximum_speed_error_mps'] > 1e-10:
                    failures.append('Recorded speed error exceeds0.1nm/s')
                if whole['complete'] and fine_status != 'complete':
                    failures.append('Partitioned trace did not complete')
                row = dict(index=index, column=sample['column'], prior_normal_neighborhood_supported=sample['normal_neighborhood_supported'],
                    complete=whole['complete'] and not failures,
                    status=whole['status'] if not failures else 'explicit geometric qualification failure',
                    qualification_failures=failures, fine_status=fine_status,
                    maximum_segment_nearest_distance_m=signed, split_step_endpoint_error_m=split,
                    worst_segment=worst_segment, trace=whole, native_animation=None)
                if row['complete']:
                    marker = bpy.data.objects.new(f'Fresh facet-transport numerical marker {index}', None)
                    bpy.context.collection.objects.link(marker)
                    created.append(marker)
                    frames = np.array([1+fps*key['seconds'] for key in whole['path']])
                    locations = np.array([key['position_m'] for key in whole['path']])
                    if np.any(np.diff(frames.astype(np.float32)) <= 0):
                        raise ValueError('Event timestamps are unresolved in native float frame coordinates')
                    # One insert creates the action and its location channels.
                    # Individual insertion coalesces nearby event keys (native
                    # row4 lost one of11 at0.00257frame separation). Populate
                    # the complete ordered arrays instead, without deduplication.
                    marker.location = locations[0]
                    marker.keyframe_insert(data_path='location', frame=frames[0])
                    action = marker.animation_data.action
                    native_key_counts = []
                    for layer in action.layers:
                        for strip in layer.strips:
                            for bag in strip.channelbags:
                                for curve in bag.fcurves:
                                    curve.keyframe_points.clear()
                                    curve.keyframe_points.add(len(frames))
                                    curve.keyframe_points.foreach_set('co', np.column_stack((frames, locations[:, curve.array_index])).ravel())
                                    curve.keyframe_points.sort()
                                    curve.keyframe_points.handles_recalc()
                                    native_key_counts.append(len(curve.keyframe_points))
                                    for key in curve.keyframe_points:
                                        key.interpolation = 'LINEAR'
                                    if len(curve.keyframe_points) != len(frames):
                                        raise ValueError('Native animation lost event keys')
                    action.update_tag()
                    row['native_animation'] = dict(object_name=marker.name, key_events=len(whole['path']),
                        actual_key_counts=native_key_counts,
                        requested_key_frames=frames.tolist(),
                        maximum_readback_error_m=0., maximum_mesh_distance_m=0.)
                rows.append(row)
            except ValueError as error:
                rows.append(dict(index=index, column=sample['column'], complete=False, status=f'explicit geometric failure: {error}'))
        successful = [row for row in rows if row.get('native_animation')]
        max_native_error, max_native_distance, worst_native_pose = 0., 0., None
        for half_frame in range(1, int(duration*fps*2)+2):
            native_frame = (half_frame+1)/2
            seconds = (native_frame-1)/fps
            bpy.context.scene.frame_set(int(native_frame), subframe=native_frame-int(native_frame))
            depsgraph = bpy.context.evaluated_depsgraph_get()
            for row in successful:
                marker = bpy.data.objects[row['native_animation']['object_name']].evaluated_get(depsgraph)
                actual = np.array(marker.matrix_world.translation)
                expected = path_at(row['trace']['path'], seconds)
                error = float(np.linalg.norm(actual-expected))
                if error > max_native_error:
                    max_native_error = error
                    worst_native_pose = dict(row_index=row['index'], native_frame=native_frame,
                        seconds=seconds, actual_position_m=actual.tolist(), expected_position_m=expected.tolist(),
                        path_readback_error_m=error)
                nearest_q, _ = nearest(actual)
                distance = float(np.linalg.norm(actual-nearest_q))
                max_native_distance = max(max_native_distance, distance)
                row['native_animation']['maximum_readback_error_m'] = max(error, row['native_animation']['maximum_readback_error_m'])
                row['native_animation']['maximum_mesh_distance_m'] = max(distance, row['native_animation']['maximum_mesh_distance_m'])
        native_passed = max_native_error <= 2e-6 and max_native_distance <= 2e-6
        if any(digest(Path(path)) != sha for path, sha in hashes.items()):
            raise ValueError('Preserved original changed during audit')
        thin_control = None
        if args.frame == 192:
            control_p = np.array([.9937521765512243, .4039704384100914, .46860976625479833])
            old_q, old_face = legacy_nearest(control_p)
            new_q, new_face = nearest(control_p)
            thin_control = dict(frame=192, point_m=control_p.tolist(),
                old_float_bvh_distance_m=float(np.linalg.norm(control_p-old_q)),
                old_float_bvh_face=int(old_face),
                float64_distance_m=float(np.linalg.norm(control_p-new_q)),
                float64_face=int(new_face))
        report = dict(complete=True, accepted=False, originals_unchanged=True, frame=args.frame,
            render_geometry_sha256=geometry_hash, original_input_sha256=hashes, rows=rows,
            prescribed_speed_mps=speed, prescribed_direction=[1., .371, 0.], duration_seconds=duration,
            source_queries=len(prior['samples']), complete_path_count=sum(row['complete'] for row in rows),
            complete_paths_from_prior_failed_normals=sum(row['complete'] and not row.get('prior_normal_neighborhood_supported', True) for row in rows),
            native_checked_objects=len(successful), native_full_half_poses=int(duration*fps*2)+1,
            maximum_native_path_readback_error_m=max_native_error, maximum_native_mesh_distance_m=max_native_distance,
            native_playback_passed=native_passed, native_coordinate_contact_allowance_m=2e-6,
            worst_native_pose=worst_native_pose,
            nearest_query_model='Float64 all-triangle AABB candidate completion, not float BVH',
            nearest_query_count=nearest.queries, maximum_nearest_candidates=nearest.maximum_candidates,
            captured_thin_triangle_control=thin_control,
            elapsed_s=time.perf_counter()-started, bvh_rounding_bound_m=rounding, bvh_candidate_padding_m=padding,
            source_code_sha256={path.name: digest(path) for path in (Path(__file__), Path(__file__).with_name('water_feature_facet_transport.py'), Path(__file__).with_name('water_feature_triangle_nearest.py'))},
            limitations='Fresh prescribed-speed kinematic markers on a STATIC captured mesh, not native liquid velocity, tracked foam, time-evolving water or SPH forces. Independent geometric event paths and native in-memory full/half key playback only; no render or delivered animation. Vertex/contact/limit failures remain explicit. No old marker lifting, native cache/mesh writes, phase changes or physical-feature acceptance.')
        with args.output.open('x') as stream:
            json.dump(report, stream, indent=2)
        print('FACET_TRANSPORT_RESULT', json.dumps({key: value for key, value in report.items() if key not in ('rows', 'original_input_sha256', 'source_code_sha256')}), flush=True)
        if not native_passed:
            raise ValueError('Native event-key playback exceeds2micrometre coordinate/contact allowance; failed receipt preserved')
    finally:
        for marker in created:
            action = marker.animation_data.action
            bpy.data.objects.remove(marker, do_unlink=True)
            if action.users == 0:
                bpy.data.actions.remove(action)
        remove_surface(derived)


if __name__ == '__main__':
    main()
