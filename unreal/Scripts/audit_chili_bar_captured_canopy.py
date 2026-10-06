"""Fresh-editor read-only check of the installed normal-scenario canopy."""
import json
from pathlib import Path
import sys
import zipfile

import unreal

sys.path.insert(0,str(Path(__file__).resolve().parent))
import integrate_chili_bar_captured_canopy as install


def main():
    root = install.ROOT
    report = install.SOURCE.parent/'integration_audit.json'
    assert not report.exists()
    evidence = json.loads(install.REPORT.read_text())
    source = json.loads(install.SOURCE.read_text())
    map_file = root/'unreal/Content/RaftSim/Maps/L_SouthForkAmerican_FullReach.umap'
    profile = root/'unreal/Saved/SaveGames/RaftSimVerticalSlice.sav'
    assert install.sha(map_file) == evidence['map_sha256']
    assert install.sha(profile) == evidence['profile_sha256']
    assert install.sha(install.SOURCE) == evidence['placement_sha256'] == install.SOURCE_SHA
    backup = root/evidence['backup']
    assert install.sha(backup) == evidence['backup_sha256']
    with zipfile.ZipFile(backup) as archive:
        previous = json.loads(archive.read('external_packages_before.json'))
    expected = previous | {row['package']:row['sha256'] for row in evidence['new_packages']}
    for package,digest in expected.items():
        assert install.sha(install.package_file(package)) == digest
    levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    assert levels.load_level(install.LEVEL)
    descriptors = unreal.WorldPartitionBlueprintLibrary.get_actor_descs()
    assert len(descriptors) == evidence['external_actor_count'] == 469
    assert {str(d.actor_package) for d in descriptors} == set(expected)
    rows = source['instances']
    xs,ys = [r['world_root_cm'][0] for r in rows],[r['world_root_cm'][1] for r in rows]
    ground = [d for d in descriptors if str(d.label).startswith(('SouthFork_coarse_terrain_','SouthFork_captured_context_'))
        and d.bounds.min.x <= max(xs) and d.bounds.max.x >= min(xs)
        and d.bounds.min.y <= max(ys) and d.bounds.max.y >= min(ys)]
    new = [d for d in descriptors if str(d.actor_package) not in previous]
    assert len(new) == 12 and all(d.is_spatially_loaded and not d.actor_is_editor_only for d in new)
    unreal.WorldPartitionBlueprintLibrary.load_actors([d.guid for d in ground+new])
    loaded = {a.get_name():a for a in actors.get_all_level_actors()}
    groups = {}
    for row in rows:
        x,y,_ = row['world_root_cm']
        groups.setdefault((int(x//25600),int(y//25600)),[]).append(row)
    errors = [install.verify(loaded[r['name']],groups[tuple(r['key'])],source) for r in evidence['actors']]
    collision_error = install.roots(actors,{str(d.name) for d in ground},rows)
    catalog = unreal.RaftSimProgressionLibrary.get_scenario_catalog()
    assert all('troublemaker' not in str(s.scenario_id).lower() for s in catalog)
    scenarios = [dict(id=str(s.scenario_id),level=str(s.level_name)) for s in catalog if 'SouthFork' in str(s.level_name)]
    assert len(scenarios) == 5 and all(s['level'] == install.LEVEL for s in scenarios)
    for package,digest in expected.items():
        assert install.sha(install.package_file(package)) == digest
    assert install.sha(map_file) == evidence['map_sha256'] and install.sha(profile) == evidence['profile_sha256']
    result = dict(schema='raftsim.chili_bar.canopy_fresh_reload.v1',passed=True,
        integration_report_sha256=install.sha(install.REPORT),placement_sha256=install.SOURCE_SHA,
        map_sha256=install.sha(map_file),profile_sha256=install.sha(profile),
        fresh_process=True,instance_count=len(rows),root_probe_count=len(rows),
        maximum_transform_error_cm=max(errors),maximum_root_collision_error_cm=collision_error,
        previous_external_actor_count=len(previous),external_actor_count=len(expected),
        new_packages=evidence['new_packages'],scenarios=scenarios,no_rapid_scenario=True,
        all_external_packages_unchanged=True,saved_no_assets=True,
        normal_map_integrated=True,tree_inventory_surveyed=False,photoreal_accepted=False,
        runtime_motion_or_performance_accepted=False)
    with report.open('x') as stream:
        json.dump(result,stream,indent=2);stream.write('\n')
    unreal.log('CHILI BAR FRESH RELOAD VERIFIED: '+str(report))


if __name__ == '__main__':
    try:
        main()
    finally:
        unreal.SystemLibrary.quit_editor()
