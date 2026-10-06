"""Fresh-editor readback of corrected normal-scene canopy packages."""
import hashlib
import json
import os
from pathlib import Path
import unreal

ROOT = Path(__file__).resolve().parents[2]


def main():
    directory = ROOT / os.environ['RAFTSIM_CANOPY_CHANNEL_REPAIR']
    audit = json.loads((ROOT / os.environ['RAFTSIM_CANOPY_CHANNEL_AUDIT']).read_text())
    repair = json.loads((directory / 'repair.json').read_text())
    output = directory / 'fresh-verification.json'
    assert not output.exists()
    for row in repair['packages']:
        assert hashlib.sha256((ROOT / row['path']).read_bytes()).hexdigest() == row['after']
    assert unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).load_level('/Game/RaftSim/Maps/L_SouthForkAmerican_FullReach')
    names = {r['actor'] for r in repair['components']}
    descs = [d for d in unreal.WorldPartitionBlueprintLibrary.get_actor_descs() if str(d.name) in names]
    assert len(descs) == len(names)
    unreal.WorldPartitionBlueprintLibrary.load_actors([d.guid for d in descs])
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    actors = {a.get_name(): a for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors() if a.get_name() in names}
    removed_xy = {(round(r['world_root_cm'][0], 1), round(r['world_root_cm'][1], 1)) for r in audit['wet_instances']}
    checked = 0
    for row in repair['components']:
        actor = actors[row['actor']]
        comp, = [c for c in actor.get_components_by_class(unreal.InstancedStaticMeshComponent) if c.get_name() == row['component']]
        assert comp.get_instance_count() == row['after']
        assert comp.get_collision_enabled() == unreal.CollisionEnabled.NO_COLLISION
        for i in range(comp.get_instance_count()):
            p = comp.get_instance_transform(i, True).translation
            assert (round(p.x, 1), round(p.y, 1)) not in removed_xy
            checked += 1
    output.write_text(json.dumps(dict(passed=True, actor_packages=len(names),
        removed_count=repair['removed_count'], remaining_affected_instances_checked=checked,
        normal_map=True, fresh_process=True, canopy_collision=False), indent=2) + '\n')
    unreal.log('RAFTSIM_CANOPY_CHANNEL_VERIFIED ' + str(output))


if __name__ == '__main__':
    main()
