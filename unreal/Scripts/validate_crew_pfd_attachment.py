"""Check actual raft crew attachment, including a deliberately displaced PFD.

Run in an editor commandlet with RAFTSIM_PFD_ATTACHMENT_REPORT set to a fresh
JSON path. No assets are saved. This is not a garment-intersection test.
"""
import json
import os
from pathlib import Path
import unreal

output = Path(os.environ['RAFTSIM_PFD_ATTACHMENT_REPORT'])
if output.exists():
    raise RuntimeError(f'Preserve prior evidence: {output}')
world = unreal.EditorLevelLibrary.get_editor_world()
raft = unreal.EditorLevelLibrary.spawn_actor_from_class(
    unreal.load_class(None, '/Script/RaftSimRaft.RaftSimRaftActor'), unreal.Vector())
raft.initialize_crew_seating_for_validation()
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
crew = [a for a in unreal.EditorLevelLibrary.get_all_level_actors()
        if a.get_owner() == raft and a.get_class().get_path_name() == '/Script/RaftSimRaft.RaftSimCrewAvatarActor']
if len(crew) != 5:
    raise RuntimeError(f'Expected five crew, got {len(crew)}')
raft.set_actor_location(unreal.Vector(10300, -7400, 2300), False, False)
raft.set_actor_rotation(unreal.Rotator(pitch=7, yaw=35, roll=-9), False)
rows = []
for host in crew:
    visual = host.get_production_visual_actor()
    if visual.get_class().get_path_name() != '/Script/RaftSimRaft.RaftSimCC0CrewVisualActor':
        raise RuntimeError('Expected actual CC0 body')
    pfd = next(c for c in host.get_components_by_class(unreal.StaticMeshComponent)
               if c.get_name() == 'ProductionPfd')
    for action in ('SEATED_IDLE', 'FORWARD_STROKE', 'BRACE', 'REENTRY'):
        host.set_avatar_action(getattr(unreal.RaftSimCrewAvatarAction, action), 1.0)
        before = pfd.get_world_location()
        attached = host.get_production_pfd_torso_error_cm()
        try:
            pfd.set_world_location(before + unreal.Vector(3, 4, 0), False, False)
            displaced = host.get_production_pfd_torso_error_cm()
        finally:
            pfd.set_world_location(before, False, False)
        restored = host.get_production_pfd_torso_error_cm()
        rows.append(dict(mesh=visual.get_selected_mesh_path(), action=action,
                         attached_cm=attached, displaced_cm=displaced, restored_cm=restored,
                         passed=attached < .01 and abs(displaced-5) < .01 and restored < .01))
report = dict(rows=rows, passed=len(rows) == 20 and all(r['passed'] for r in rows),
              assets_saved=False, garment_clearance_accepted=False, motion_accepted=False)
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps(report, indent=2), encoding='utf-8')
if not report['passed']:
    raise RuntimeError(f'Attachment checks failed: {output}')
unreal.log(f'PFD attachment: all {len(rows)} fault-injection cases passed')
