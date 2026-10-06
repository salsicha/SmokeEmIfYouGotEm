"""Measure actual production boot soles against uploaded raft floor triangles.

Read-only posed diagnostic, not animation or full crew acceptance. No assets or
levels are saved. RAFTSIM_FOOT_REVIEW_OUTPUT must name a fresh output directory.
Launch with -ExecCmds="py <absolute script path>": captures yield editor frames;
-ExecutePythonScript would close the editor before the callback completes.
"""
import importlib.util
import json
import math
import os
import hashlib
import time
import traceback
from pathlib import Path

import unreal


def xyz(point):
    return [float(point.x), float(point.y), float(point.z)]


def top_at(point, triangles):
    x, y, _ = point
    heights = []
    for a, b, c in triangles:
        if not (min(a[0], b[0], c[0])-1.e-6 <= x <= max(a[0], b[0], c[0])+1.e-6
                and min(a[1], b[1], c[1])-1.e-6 <= y <= max(a[1], b[1], c[1])+1.e-6):
            continue
        det = (b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
        if abs(det) < 1.e-10:
            continue
        u = ((b[1]-c[1])*(x-c[0])+(c[0]-b[0])*(y-c[1]))/det
        v = ((c[1]-a[1])*(x-c[0])+(a[0]-c[0])*(y-c[1]))/det
        if min(u, v, 1-u-v) >= -1.e-6:
            heights.append(u*a[2]+v*b[2]+(1-u-v)*c[2])
    return max(heights) if heights else None


def main():
    output = Path(os.environ['RAFTSIM_FOOT_REVIEW_OUTPUT'])
    output.mkdir(parents=True, exist_ok=False)
    spec = importlib.util.spec_from_file_location(
        'crew_helpers', Path(__file__).with_name('capture_cc0_production_roster.py'))
    helpers = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helpers)
    helpers.OUTPUT_ROOT = output
    world = unreal.EditorLevelLibrary.get_editor_world()
    raft = helpers.spawn(unreal.load_class(None, '/Script/RaftSimRaft.RaftSimRaftActor'), unreal.Vector())
    raft.initialize_crew_seating_for_validation()
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    crew = [a for a in unreal.EditorLevelLibrary.get_all_level_actors()
            if a.get_class().get_path_name() == helpers.HOST_CLASS and a.get_owner() == raft]
    if len(crew) != 5:
        raise RuntimeError('Expected five production crew')
    visual = next(c for c in raft.get_components_by_class(unreal.ProceduralMeshComponent)
                  if c.get_name() == 'RaftVisual')
    points, indices, _, _, _ = unreal.ProceduralMeshLibrary.get_section_from_procedural_mesh(visual, 1)
    points = [xyz(unreal.MathLibrary.transform_location(visual.get_world_transform(), p)) for p in points]
    triangles = [[points[indices[i+j]] for j in range(3)] for i in range(0, len(indices), 3)]
    if not triangles:
        raise RuntimeError('Missing actual floor section')
    tube_points, tube_indices, _, _, _ = unreal.ProceduralMeshLibrary.get_section_from_procedural_mesh(visual, 0)
    tube_points = [xyz(unreal.MathLibrary.transform_location(visual.get_world_transform(), p)) for p in tube_points]
    solids = triangles + [[tube_points[tube_indices[i+j]] for j in range(3)] for i in range(0, len(tube_indices), 3)]
    report = dict(schema='raftsim.crew_foot_contact.v3', floor_section=1,
                  solid_sections=[0, 1], solid_triangles=len(solids),
                  floor_triangles=len(triangles), poses=[], images=[],
                  assets_saved=False, visual_accepted=False, motion_accepted=False)
    source_vertices = {}
    for action in ('SEATED_IDLE', 'FORWARD_STROKE', 'BRACE', 'HIGH_SIDE_PORT', 'HIGH_SIDE_STARBOARD'):
        for host in crew:
            host.set_avatar_action(getattr(unreal.RaftSimCrewAvatarAction, action), 1.0)
            boots = [c for c in host.get_components_by_class(unreal.StaticMeshComponent)
                     if c.get_name() in ('ProductionLeftBoot', 'ProductionRightBoot')]
            if len(boots) != 2:
                raise RuntimeError('Missing production boots')
            for boot in boots:
                mesh = boot.get_editor_property('static_mesh')
                if mesh.get_path_name() not in source_vertices:
                    vertices = []
                    for section in range(mesh.get_num_sections(0)):
                        vertices.extend(unreal.ProceduralMeshLibrary.get_section_from_static_mesh(mesh, 0, section)[0])
                    source_vertices[mesh.get_path_name()] = vertices
                vertices = source_vertices[mesh.get_path_name()]
                sole_z = min(v.z for v in vertices)
                # Retain all vertices in the lowest 1 mm of the actual tread.
                sole = [xyz(unreal.MathLibrary.transform_location(boot.get_world_transform(), p))
                        for p in vertices if p.z <= sole_z+0.1]
                sole = list({tuple(p) for p in sole})
                low_x, high_x = min(p[0] for p in sole), max(p[0] for p in sole)
                low_y, high_y = min(p[1] for p in sole), max(p[1] for p in sole)
                nearby_solids = [t for t in solids if not (
                    max(p[0] for p in t) < low_x-1.e-6 or min(p[0] for p in t) > high_x+1.e-6 or
                    max(p[1] for p in t) < low_y-1.e-6 or min(p[1] for p in t) > high_y+1.e-6)]
                samples = [dict(sole_cm=p, floor_z_cm=top_at(p, triangles),
                                solid_z_cm=top_at(p, nearby_solids)) for p in sole]
                clearances = [p['sole_cm'][2]-p['floor_z_cm'] for p in samples if p['floor_z_cm'] is not None]
                solid_clearances = [p['sole_cm'][2]-p['solid_z_cm'] for p in samples if p['solid_z_cm'] is not None]
                if not all(math.isfinite(v) for v in clearances):
                    raise RuntimeError('Nonfinite floor support samples')
                if not solid_clearances or not all(math.isfinite(v) for v in solid_clearances):
                    raise RuntimeError('No finite solid support samples')
                body = host.get_production_visual_actor().get_component_by_class(unreal.PoseableMeshComponent)
                body_foot = body.get_bone_location_by_name(
                    'foot_l' if boot.get_name() == 'ProductionLeftBoot' else 'foot_r', unreal.BoneSpaces.WORLD_SPACE)
                # Reflected structs may alias the live property. Never mutate
                # a component while measuring its independently solved target.
                foot_target = unreal.Vector(*xyz(boot.get_editor_property('relative_location')))
                foot_target.z -= sole_z * (host.get_body_proportion_scale().z-boot.get_editor_property('relative_scale3d').z)
                foot_target = unreal.MathLibrary.transform_location(host.get_actor_transform(), foot_target)
                report['poses'].append(dict(action=action, crew=host.get_name(), boot=boot.get_name(),
                    planted_contact_solve=host.has_planted_rendered_feet(),
                    mesh=mesh.get_path_name(), seat_cm=xyz(host.get_actor_location()),
                    seat_contact_clearance_cm=raft.get_crew_seat_contact_clearance_cm(host),
                    body_foot_world_cm=xyz(body_foot), boot_target_world_cm=xyz(foot_target),
                    body_boot_target_error_cm=math.dist(xyz(body_foot), xyz(foot_target)),
                    # A high-side boot may stand wholly on the tube. Preserve
                    # missing floor as null, never infer floor beneath it.
                    minimum_clearance_cm=min(clearances) if clearances else None,
                    maximum_clearance_cm=max(clearances) if clearances else None,
                    minimum_solid_clearance_cm=min(solid_clearances), maximum_solid_clearance_cm=max(solid_clearances),
                    unsupported_solid_samples=sum(p['solid_z_cm'] is None for p in samples),
                    unsupported_samples=sum(p['floor_z_cm'] is None for p in samples), samples=samples))
    for host in crew:
        host.set_avatar_action(unreal.RaftSimCrewAvatarAction.SEATED_IDLE, 1.0)
    for eye in (unreal.Vector(200, 350, 400), unreal.Vector(-250, -350, 300)):
        helpers.configure_rect_light(eye, unreal.Vector(0, 0, 30), 180, 300, 300, unreal.Color(245, 241, 235, 255))
    capture = helpers.spawn(unreal.SceneCapture2D, unreal.Vector())
    component = capture.capture_component2d
    component.set_editor_property('capture_source', unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR)
    component.set_editor_property('capture_every_frame', False)
    component.set_editor_property('capture_on_movement', False)
    target = unreal.RenderingLibrary.create_render_target2d(world, 1280, 960,
        unreal.TextureRenderTargetFormat.RTF_RGBA8, unreal.LinearColor(0.03, 0.03, 0.03, 1), False)
    component.set_editor_property('texture_target', target)
    for command in ('r.EyeAdaptationQuality 0', 'r.TextureStreaming 0', 'r.Nanite 0'):
        unreal.SystemLibrary.execute_console_command(world, command)
    views = [(action, label, eye, aim)
             for action in ('SEATED_IDLE', 'HIGH_SIDE_PORT', 'HIGH_SIDE_STARBOARD')
             for label, eye, aim in (('floor_front', unreal.Vector(400, 150, 210), unreal.Vector(50, 0, 15)),
                                    ('floor_rear', unreal.Vector(-400, 150, 240), unreal.Vector(-70, 0, 15)))]
    state = dict(frame=0, index=0, started=time.monotonic(), hashes=set())
    report['capture_complete'] = False

    def finish(error=None):
        unreal.unregister_slate_post_tick_callback(state['handle'])
        report['capture_complete'] = error is None
        report['capture_error'] = error
        (output/'report.json').write_text(json.dumps(report, indent=2, allow_nan=False)+'\n', encoding='utf-8')
        if error:
            unreal.log_error(error)
        unreal.SystemLibrary.quit_editor()

    def tick(delta):
        try:
            if time.monotonic()-state['started'] > 120:
                raise RuntimeError('Posed captures exceeded two-minute wall bound')
            action, label, eye, aim = views[state['index']]
            if state['frame'] == 0:
                for host in crew:
                    host.set_avatar_action(getattr(unreal.RaftSimCrewAvatarAction, action), 1.0)
                capture.set_actor_location(eye, False, False)
                capture.set_actor_rotation(helpers.look_at(eye, aim), False)
                component.set_editor_property('fov_angle', 48)
            if state['frame'] in (3, 6):
                component.capture_scene()
            if state['frame'] == 9:
                # Export only after the camera, pose and capture have crossed
                # actual editor/render frames. Synchronous loops exported six
                # byte-identical stale images in the retained v1 attempt.
                name = action.lower()+'_'+label+'.png'
                unreal.RenderingLibrary.export_render_target(world, target, str(output), name)
                path = output/name
                digest = hashlib.sha256(path.read_bytes()).hexdigest()
                if digest in state['hashes']:
                    raise RuntimeError('Duplicate posed capture: '+name)
                state['hashes'].add(digest)
                report['images'].append(str(path))
                state['index'] += 1
                if state['index'] == len(views):
                    finish()
                    return
                state['frame'] = -1
            state['frame'] += 1
        except Exception:
            finish(traceback.format_exc())

    state['handle'] = unreal.register_slate_post_tick_callback(tick)


if __name__ == '__main__':
    try:
        main()
    except Exception:
        unreal.log_error(traceback.format_exc())
        unreal.SystemLibrary.quit_editor()
