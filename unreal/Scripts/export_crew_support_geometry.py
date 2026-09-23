"""Read-only uploaded hull/boot/joint geometry for bounded stance analysis."""
import json
import os
from pathlib import Path
import unreal


def xyz(p):
    return [float(p.x), float(p.y), float(p.z)]


try:
    output = Path(os.environ['RAFTSIM_CREW_GEOMETRY_OUTPUT'])
    output.mkdir(parents=True, exist_ok=False)
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    raft = actors.spawn_actor_from_class(unreal.load_class(None, '/Script/RaftSimRaft.RaftSimRaftActor'), unreal.Vector())
    raft.initialize_crew_seating_for_validation()
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    visual = next(c for c in raft.get_components_by_class(unreal.ProceduralMeshComponent) if c.get_name() == 'RaftVisual')
    report = dict(schema='raftsim.crew_support_geometry.v1', sections=[], crew=[], assets_saved=False)
    for section in (0, 1):
        points, indices, _, _, _ = unreal.ProceduralMeshLibrary.get_section_from_procedural_mesh(visual, section)
        report['sections'].append(dict(section=section, points_cm=[xyz(unreal.MathLibrary.transform_location(visual.get_world_transform(), p)) for p in points], indices=list(indices)))
    for host in actors.get_all_level_actors():
        if host.get_owner() != raft or host.get_class().get_path_name() != '/Script/RaftSimRaft.RaftSimCrewAvatarActor':
            continue
        host.set_avatar_action(unreal.RaftSimCrewAvatarAction.SEATED_IDLE, 1.)
        transform = host.get_actor_transform()
        body = host.get_production_visual_actor().get_component_by_class(unreal.PoseableMeshComponent)
        entry = dict(name=host.get_name(), origin_cm=xyz(host.get_actor_location()),
                     basis=[xyz(unreal.MathLibrary.transform_direction(transform, axis)) for axis in (unreal.Vector(1,0,0), unreal.Vector(0,1,0), unreal.Vector(0,0,1))],
                     profile=xyz(host.get_body_proportion_scale()), joints={}, boots=[])
        for bone in ('thigh_l','calf_l','foot_l','thigh_r','calf_r','foot_r'):
            entry['joints'][bone] = xyz(body.get_bone_location_by_name(bone, unreal.BoneSpaces.WORLD_SPACE))
        for boot in host.get_components_by_class(unreal.StaticMeshComponent):
            if boot.get_name() not in ('ProductionLeftBoot','ProductionRightBoot'):
                continue
            mesh = boot.get_editor_property('static_mesh')
            box = mesh.get_bounding_box()
            entry['boots'].append(dict(name=boot.get_name(), mesh=mesh.get_path_name(),
                minimum_cm=xyz(box.min), maximum_cm=xyz(box.max), scale=xyz(boot.get_editor_property('relative_scale3d'))))
        report['crew'].append(entry)
    if len(report['crew']) != 5 or any(len(c['boots']) != 2 for c in report['crew']):
        raise RuntimeError('Incomplete production roster/boots')
    (output/'geometry.json').write_text(json.dumps(report, indent=2, allow_nan=False)+'\n', encoding='utf-8')
    unreal.log('CREW_SUPPORT_GEOMETRY exported '+str(output))
finally:
    unreal.SystemLibrary.quit_editor()
