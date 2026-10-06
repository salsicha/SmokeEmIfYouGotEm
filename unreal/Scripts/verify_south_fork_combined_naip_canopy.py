"""Read-only fresh-editor inventory of both shipped NAIP canopy passes.

Verify every surviving original and additive tree, not just a root sample.
The original placement remains archival; the 266 channel removals are applied
only to the expected inventory. No source, actor or package is saved here.
RAFTSIM_COMBINED_CANOPY_REPORT must name a fresh repo-relative tmp JSON.
This checks placement/mesh/scale/streaming/collision, not visual acceptance,
ground clearance, yaw, HLOD coverage or hydraulic behaviour.
"""
import hashlib
import json
import math
import os
from pathlib import Path
import unreal

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'physics/data/real_world/south_fork_american_chili_bar/reconstruction_2026_09/full_reach'
LEVEL = '/Game/RaftSim/Maps/L_SouthForkAmerican_FullReach'
SLOTS = ('canopy_a', 'canopy_b', 'canopy_c')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    output = (ROOT / os.environ['RAFTSIM_COMBINED_CANOPY_REPORT']).resolve()
    assert output.is_relative_to(ROOT / 'tmp') and not output.exists()
    repair_path = ROOT / 'docs/reconstruction-review-2026-09-07/canopy-channel-repair/repair.json'
    repair = json.loads(repair_path.read_text())
    removed = set(repair['removed_ids'])
    assert len(removed) == repair['removed_count'] == 266
    passes = [
        ('South Fork NAIP canopy', 'placement.json', removed),
        ('South Fork lower-gorge NAIP canopy', 'lower_gorge_additions_placement.json', set()),
    ]
    expected, sources, xy_seen = {}, [], set()
    for prefix, filename, excluded in passes:
        path = BASE / 'naip_canopy_20260926' / filename
        data = json.loads(path.read_text())
        digest = sha(path)
        assert data['level'] == LEVEL and len(data['instances']) == data['instance_count']
        assert len({r['id'] for r in data['instances']}) == data['instance_count']
        assert excluded.issubset({r['id'] for r in data['instances']})
        if excluded:
            assert digest == repair['placement_sha256']
        else:
            assert data['addition_to_placement_sha256'] == repair['placement_sha256']
        count = 0
        for row in data['instances']:
            if row['id'] in excluded:
                continue
            x, y, _ = row['world_root_cm']
            xy = (round(x, 1), round(y, 1))
            assert xy not in xy_seen, 'Duplicate original/additive root'
            xy_seen.add(xy)
            form = row['form_index']
            assert 0 <= form < 6
            group = 'oak' if form < 3 else 'riparian-pine'
            label = f'{prefix} {math.floor(x / 25600)} {math.floor(y / 25600)} {group} - imagery canopy, inferred species'
            entry = expected.setdefault(label, dict(digest=digest, assets=data['assets'], rows=[[], [], []]))
            entry['rows'][form % 3].append(row)
            count += 1
        sources.append(dict(path=path.relative_to(ROOT).as_posix(), sha256=digest, expected_instances=count))
    assert sum(s['expected_instances'] for s in sources) == 164628
    assert unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).load_level(LEVEL)
    descs = [d for d in unreal.WorldPartitionBlueprintLibrary.get_actor_descs()
             if any(str(d.label).startswith(p[0] + ' ') for p in passes)]
    assert len(descs) == len(expected) and {str(d.label) for d in descs} == set(expected)
    assert all(d.is_spatially_loaded for d in descs)
    unreal.WorldPartitionBlueprintLibrary.load_actors([d.guid for d in descs])
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    actors = [a for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
              if a.get_actor_label() in expected]
    assert len(actors) == len(expected)
    checked, max_position_error, max_scale_error = 0, 0.0, 0.0
    for actor in actors:
        entry = expected[actor.get_actor_label()]
        assert actor.get_editor_property('placement_source_sha256') == entry['digest']
        for slot, rows in enumerate(entry['rows']):
            component = actor.get_editor_property(SLOTS[slot])
            assert component.get_instance_count() == len(rows)
            assert component.get_collision_enabled() == unreal.CollisionEnabled.NO_COLLISION
            assert not component.get_editor_property('generate_overlap_events')
            if not rows:
                continue
            package = entry['assets'][rows[0]['form_index']]['package']
            assert component.static_mesh.get_path_name().split('.')[0] == package
            bounds = component.static_mesh.get_bounding_box()
            buckets = {}
            for row in rows:
                x, y, _ = row['world_root_cm']
                buckets.setdefault((math.floor(x / 100), math.floor(y / 100)), []).append(row)
            for index in range(component.get_instance_count()):
                transform = component.get_instance_transform(index, True)
                p, scale = transform.translation, transform.scale3d
                bx, by = math.floor(p.x / 100), math.floor(p.y / 100)
                matches = [(key, row) for dx in (-1, 0, 1) for dy in (-1, 0, 1)
                           for key in [(bx + dx, by + dy)] for row in buckets.get(key, [])
                           if abs(p.x - row['world_root_cm'][0]) <= 1 and abs(p.y - row['world_root_cm'][1]) <= 1]
                assert len(matches) == 1, 'Missing, extra, duplicate or shifted installed root'
                key, row = matches[0]
                buckets[key].remove(row)
                x, y, z = row['world_root_cm']
                bottom_z = p.z + bounds.min.z * scale.z
                error = max(abs(p.x-x), abs(p.y-y), abs(bottom_z-(z-20)))
                expected_scale = row['height_m'] * 100 / (bounds.max.z-bounds.min.z)
                scale_error = max(abs(s-expected_scale) for s in (scale.x, scale.y, scale.z))
                assert error <= 1 and scale_error <= .0001
                max_position_error = max(max_position_error, error)
                max_scale_error = max(max_scale_error, scale_error)
                checked += 1
            assert not any(buckets.values())
    assert checked == 164628
    result = dict(schema='raftsim.combined_naip_canopy_readback.v1', passed=True,
                  sources=sources, repair_sha256=sha(repair_path), actors=len(actors), instances=checked,
                  max_position_error_cm=max_position_error, max_scale_error=max_scale_error,
                  excluded_original_water_roots=len(removed), duplicate_roots=0,
                  spatially_loaded=True, collision=False, assets_modified=False,
                  fresh_editor_process=True, visual_or_hydraulic_acceptance=False)
    output.write_text(json.dumps(result, indent=2) + '\n')
    unreal.log('RAFTSIM_COMBINED_CANOPY_VERIFIED ' + json.dumps(result))


if __name__ == '__main__':
    main()
