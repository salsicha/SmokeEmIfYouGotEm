"""Load the Troublemaker captured-geometry actors with the map, not mid-descent.

The retained rapid ground (803,842 triangles, complex collision), its captured
rock flanks, the inferred join and the 1,268-tree rapid-bank canopy share one
World Partition cell. Streaming that cell in during play (about 2 km before the
rapid) stalled a frame for ~430 ms in three repeated profiles. Marking these
four actors not spatially loaded moves that cost into map travel. Geometry,
materials, collision and transforms are unchanged; only the four external actor
packages are re-saved. Environment: RAFTSIM_ALWAYS_LOADED_REPORT (fresh tmp JSON).
"""
import hashlib
import json
import os
from pathlib import Path

import unreal

ROOT = Path(__file__).resolve().parents[2]
LEVEL = '/Game/RaftSim/Maps/L_SouthForkAmerican_FullReach'
LABELS = ('SouthFork_retained_rapid_SM_TroublemakerSurveyCandidate', 'SouthFork_Troublemaker_CapturedRock_InferredFlanks',
          'SouthFork_inferred_join_SM_SouthForkTroublemakerJoin', 'South Fork captured rapid-bank canopy - inferred trees')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    report = ROOT / os.environ['RAFTSIM_ALWAYS_LOADED_REPORT']
    assert report.is_relative_to(ROOT / 'tmp') and not report.exists()
    assert unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).load_level(LEVEL)
    descs = [d for d in unreal.WorldPartitionBlueprintLibrary.get_actor_descs() if str(d.label) in LABELS]
    assert sorted(str(d.label) for d in descs) == sorted(LABELS), [str(d.label) for d in descs]
    unreal.WorldPartitionBlueprintLibrary.load_actors([d.guid for d in descs])
    actors = {a.get_name(): a for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()}
    rows = []
    for d in descs:
        a = actors[str(d.name)]
        path = ROOT / ('unreal/Content/' + str(d.actor_package).removeprefix('/Game/') + '.uasset')
        before = sha(path)
        transform = a.get_actor_transform()
        a.modify()
        a.set_editor_property('is_spatially_loaded', False)
        assert unreal.EditorAssetLibrary.save_loaded_asset(a, only_if_is_dirty=False) or \
            unreal.EditorLoadingAndSavingUtils.save_dirty_packages(False, True)
        assert a.get_actor_transform().equals(transform)
        rows.append(dict(label=str(d.label), package=str(d.actor_package), sha256_before=before, sha256_after=sha(path)))
    after = {str(d.label): bool(d.is_spatially_loaded) for d in unreal.WorldPartitionBlueprintLibrary.get_actor_descs() if str(d.label) in LABELS}
    report.write_text(json.dumps(dict(level=LEVEL, actors=rows, spatially_loaded_after=after,
                                      geometry_materials_collision_changed=False), indent=2) + '\n')
    unreal.log('RAFTSIM_TROUBLEMAKER_ALWAYS_LOADED ' + json.dumps(after))


if __name__ == '__main__':
    main()
