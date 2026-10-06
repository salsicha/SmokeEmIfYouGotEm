"""Remove only audited inferred canopy instances inside the context water mask.

Preserves original placement and imagery. Backups precede actor-package edits.
Environment: RAFTSIM_CANOPY_CHANNEL_AUDIT, RAFTSIM_CANOPY_CHANNEL_REPAIR.
"""
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import unreal

ROOT = Path(__file__).resolve().parents[2]
LEVEL = '/Game/RaftSim/Maps/L_SouthForkAmerican_FullReach'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def signature(t):
    return [t.translation.x, t.translation.y, t.translation.z,
            t.rotation.x, t.rotation.y, t.rotation.z, t.rotation.w,
            t.scale3d.x, t.scale3d.y, t.scale3d.z]


def main():
    audit_path = ROOT / os.environ['RAFTSIM_CANOPY_CHANNEL_AUDIT']
    out = (ROOT / os.environ['RAFTSIM_CANOPY_CHANNEL_REPAIR']).resolve()
    assert out.is_relative_to(ROOT / 'tmp') and not out.exists()
    audit = json.loads(audit_path.read_text())
    assert audit['schema'] == 'raftsim.canopy_channel_audit.v1'
    assert sha(ROOT / audit['placement']) == audit['placement_sha256']
    assert sha(ROOT / audit['mask']) == audit['mask_sha256']
    assert audit['wet_count'] == len(audit['wet_instances']) == 266
    groups = {}
    for row in audit['wet_instances']:
        x, y, _ = row['world_root_cm']
        group = 'oak' if row['form_index'] < 3 else 'riparian-pine'
        prefix = f'South Fork NAIP canopy {math.floor(x / 25600)} {math.floor(y / 25600)} {group} -'
        groups.setdefault(prefix, []).append(row)
    assert unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).load_level(LEVEL)
    subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    descs = [d for d in unreal.WorldPartitionBlueprintLibrary.get_actor_descs()
             if any(str(d.label).startswith(p) for p in groups)]
    assert len(descs) == len(groups)
    unreal.WorldPartitionBlueprintLibrary.load_actors([d.guid for d in descs])
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    actors = subsystem.get_all_level_actors()
    plans, packages = [], []
    # Validate every target before editing any instance or saving a package.
    for prefix, rows in groups.items():
        actor, = [a for a in actors if a.get_actor_label().startswith(prefix)]
        assert actor.get_editor_property('placement_source_sha256') == audit['placement_sha256']
        package = actor.get_package()
        path = ROOT / 'unreal/Content' / (str(package.get_name()).removeprefix('/Game/') + '.uasset')
        packages.append((package, path, sha(path)))
        for form in sorted({r['form_index'] for r in rows}):
            comp = actor.get_editor_property(('canopy_a', 'canopy_b', 'canopy_c')[form % 3])
            before = [signature(comp.get_instance_transform(i, True)) for i in range(comp.get_instance_count())]
            matches = []
            for row in [r for r in rows if r['form_index'] == form]:
                x, y, z = row['world_root_cm']
                indices = [i for i, t in enumerate(before) if abs(t[0]-x) < .1 and abs(t[1]-y) < .1]
                assert len(indices) == 1, (row['id'], indices)
                index = indices[0]
                t = comp.get_instance_transform(index, True)
                bottom = t.translation.z + comp.static_mesh.get_bounding_box().min.z * t.scale3d.z
                assert abs(bottom - (z - 20)) < .1, 'Instance changed since installation'
                matches.append(index)
            assert len(set(matches)) == len(matches)
            plans.append((actor, comp, before, set(matches)))
    out.mkdir(parents=True)
    for _, path, digest in packages:
        backup = out / (path.stem + '.uasset')
        shutil.copy2(path, backup)
        assert sha(backup) == digest
    result = []
    for actor, comp, before, removed in plans:
        actor.modify()
        comp.modify()
        for index in sorted(removed, reverse=True):
            assert comp.remove_instance(index)
        actual = [signature(comp.get_instance_transform(i, True)) for i in range(comp.get_instance_count())]
        expected = [t for i, t in enumerate(before) if i not in removed]
        # HISM may swap indices when removing. Compare the unchanged multiset.
        assert sorted(actual) == sorted(expected), 'Surviving transforms changed'
        result.append(dict(actor=actor.get_name(), component=comp.get_name(),
                           before=len(before), after=len(actual), removed=len(removed)))
    assert sum(r['removed'] for r in result) == 266
    assert unreal.EditorLoadingAndSavingUtils.save_packages([p[0] for p in packages], False)
    report = dict(audit_sha256=sha(audit_path), placement_sha256=audit['placement_sha256'],
                  mask_sha256=audit['mask_sha256'], removed_count=266,
                  removed_ids=[r['id'] for r in audit['wet_instances']],
                  remaining_total=audit['total']-266, components=result,
                  packages=[dict(path=p.relative_to(ROOT).as_posix(), before=h, after=sha(p)) for _, p, h in packages],
                  captured_data_changed=False, geometry_or_water_changed=False,
                  reason='Inferred tree root is inside authoritative context water-mask cell')
    (out / 'repair.json').write_text(json.dumps(report, indent=2) + '\n')
    unreal.log('RAFTSIM_CANOPY_CHANNEL_REMOVED ' + str(out / 'repair.json'))


if __name__ == '__main__':
    main()
