"""Read-only installed-instance and all-static-ground audit of localized roots."""
import hashlib
import json
import math
import os
from pathlib import Path
import unreal

ROOT = Path(__file__).resolve().parents[2]
LEVEL = '/Game/RaftSim/Maps/L_SouthForkAmerican_FullReach'


def main():
    source = ROOT / os.environ['RAFTSIM_NAIP_CANOPY_PLACEMENT']
    localized = ROOT / os.environ['RAFTSIM_NAIP_CANOPY_LOCALIZED']
    output = (ROOT / os.environ['RAFTSIM_NAIP_CANOPY_OUTLIER_REPORT']).resolve()
    assert output.is_relative_to(ROOT / 'tmp') and not output.exists()
    data = json.loads(source.read_text())
    outliers = json.loads(localized.read_text())['outliers_over_20cm']
    expected_sha = hashlib.sha256(source.read_bytes()).hexdigest()
    assert unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).load_level(LEVEL)
    subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    descs = unreal.WorldPartitionBlueprintLibrary.get_actor_descs()
    prefixes = set()
    for row in outliers:
        x, y, _ = row['world_root_cm']
        group = 'oak' if row['form_index'] < 3 else 'riparian-pine'
        prefixes.add(f'South Fork NAIP canopy {math.floor(x / 25600)} {math.floor(y / 25600)} {group} -')
    chosen = [d for d in descs if d.native_class.get_name() == 'StaticMeshActor' or
              any(str(d.label).startswith(p) for p in prefixes)]
    unreal.WorldPartitionBlueprintLibrary.load_actors([d.guid for d in chosen])
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    actors = subsystem.get_all_level_actors()
    ground = [a for a in actors if a.get_class().get_name() == 'StaticMeshActor']
    ignore = [a for a in actors if a not in ground]
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    result = []
    for row in outliers:
        x, y, z = row['world_root_cm']
        form = row['form_index']
        group = 'oak' if form < 3 else 'riparian-pine'
        prefix = f'South Fork NAIP canopy {math.floor(x / 25600)} {math.floor(y / 25600)} {group} -'
        canopy, = [a for a in actors if a.get_actor_label().startswith(prefix)]
        assert canopy.get_editor_property('placement_source_sha256') == expected_sha
        comp = canopy.get_editor_property(('canopy_a', 'canopy_b', 'canopy_c')[form % 3])
        matches = []
        for index in range(comp.get_instance_count()):
            transform = comp.get_instance_transform(index, True)
            p = transform.translation
            if abs(p.x - x) < .1 and abs(p.y - y) < .1:
                matches.append((index, transform))
        index, transform = matches[0] if len(matches) == 1 else (None, None)
        assert transform is not None, 'Ambiguous installed instance'
        bottom = transform.translation.z + comp.static_mesh.get_bounding_box().min.z * transform.scale3d.z
        hit = unreal.SystemLibrary.line_trace_single(world, unreal.Vector(x, y, z + 5000),
            unreal.Vector(x, y, z - 5000), unreal.TraceTypeQuery.TRACE_TYPE_QUERY1,
            True, ignore, unreal.DrawDebugTrace.NONE, False)
        values = hit.to_tuple() if hit else None
        assert values and values[0], 'No all-static ground hit'
        result.append(dict(id=row['id'], actor=canopy.get_name(), actor_label=canopy.get_actor_label(),
                           component=comp.get_name(), instance=index, world_root_cm=row['world_root_cm'],
                           installed_mesh_bottom_z_cm=bottom, all_static_ground_z_cm=values[5].z,
                           actual_bottom_minus_ground_cm=bottom-values[5].z,
                           previous_filtered_ground_z_cm=row['ground_z_cm'], hit=str(values)))
    output.write_text(json.dumps(dict(placement_sha256=expected_sha, static_ground_actors=len(ground),
                                      instances=result, assets_modified=False), indent=2) + '\n')
    unreal.log('RAFTSIM_CANOPY_OUTLIERS ' + str(output))


if __name__ == '__main__':
    main()
