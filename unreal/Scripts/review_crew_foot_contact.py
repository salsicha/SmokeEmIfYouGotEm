"""Measure actual production boot soles against uploaded raft floor triangles.

Read-only posed diagnostic, not animation or full crew acceptance. No assets or
levels are saved. RAFTSIM_FOOT_REVIEW_OUTPUT must name a fresh output directory.
"""
import importlib.util
import json
import math
import os
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
    report = dict(schema='raftsim.crew_foot_contact.v1', floor_section=1,
                  floor_triangles=len(triangles), poses=[], images=[],
                  assets_saved=False, visual_accepted=False, motion_accepted=False)
    for action in ('SEATED_IDLE', 'FORWARD_STROKE', 'BRACE', 'HIGH_SIDE_PORT', 'HIGH_SIDE_STARBOARD'):
        for host in crew:
            host.set_avatar_action(getattr(unreal.RaftSimCrewAvatarAction, action), 1.0)
            boots = [c for c in host.get_components_by_class(unreal.StaticMeshComponent)
                     if c.get_name() in ('ProductionLeftBoot', 'ProductionRightBoot')]
            if len(boots) != 2:
                raise RuntimeError('Missing production boots')
            for boot in boots:
                mesh = boot.get_editor_property('static_mesh')
                vertices = []
                for section in range(mesh.get_num_sections(0)):
                    vertices.extend(unreal.ProceduralMeshLibrary.get_section_from_static_mesh(mesh, 0, section)[0])
                sole_z = min(v.z for v in vertices)
                # Retain all vertices in the lowest 1 mm of the actual tread.
                sole = [xyz(unreal.MathLibrary.transform_location(boot.get_world_transform(), p))
                        for p in vertices if p.z <= sole_z+0.1]
                sole = list({tuple(p) for p in sole})
                samples = [dict(sole_cm=p, floor_z_cm=top_at(p, triangles)) for p in sole]
                clearances = [p['sole_cm'][2]-p['floor_z_cm'] for p in samples if p['floor_z_cm'] is not None]
                if not clearances or not all(math.isfinite(v) for v in clearances):
                    raise RuntimeError('No finite floor support samples')
                report['poses'].append(dict(action=action, crew=host.get_name(), boot=boot.get_name(),
                    mesh=mesh.get_path_name(), seat_cm=xyz(host.get_actor_location()),
                    minimum_clearance_cm=min(clearances), maximum_clearance_cm=max(clearances),
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
    for label, eye, aim in (('floor_front', unreal.Vector(400, 150, 210), unreal.Vector(50, 0, 15)),
                            ('floor_rear', unreal.Vector(-400, 150, 240), unreal.Vector(-70, 0, 15))):
        capture.set_actor_location(eye, False, False)
        capture.set_actor_rotation(helpers.look_at(eye, aim), False)
        component.set_editor_property('fov_angle', 48)
        report['images'].append(str(helpers.export_capture(world, component, target, label)))
    (output/'report.json').write_text(json.dumps(report, indent=2, allow_nan=False)+'\n', encoding='utf-8')
    unreal.log('Actual crew sole/floor diagnostic complete: '+str(output))


if __name__ == '__main__':
    try:
        main()
    finally:
        unreal.SystemLibrary.quit_editor()
