"""Switch the saved Zambezi reference map to a moving live-solver window.

The fixed window simulated the whole 30 km, 5999 x 25 cell corridor every
1/60 s tick (~20 ms per step) and ran at ~5 FPS. This sets the same values the
map generator now writes (RaftSimEditorLandscapeGeometry.cpp): moving-window
streaming over the unchanged cooked field, 640 x 250 m, advancing every 80 m,
initial centre at station 320 m. Only the water config is modified and saved.
Environment: RAFTSIM_ZAMBEZI_REPORT (fresh tmp JSON).
"""
import hashlib
import json
import os
from pathlib import Path

import unreal

ROOT = Path(__file__).resolve().parents[2]
LEVEL = '/Game/RaftSim/Maps/L_Zambezi'
MANIFEST = 'physics/data/real_world/zambezi_batoka_gorge/scenario_zambezi_run/runtime/moving_water_streaming.json'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    report = ROOT / os.environ['RAFTSIM_ZAMBEZI_REPORT']
    assert report.is_relative_to(ROOT / 'tmp') and not report.exists()
    assert (ROOT / MANIFEST).is_file()
    assert unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).load_level(LEVEL)
    configs = [a for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
               if a.get_class().get_name() == 'RaftSimRiverWaterConfig']
    assert len(configs) == 1, len(configs)
    c = configs[0]
    names = ('enable_moving_window_streaming', 'streaming_manifest_path', 'window_center_m', 'moving_window_station_extent_m',
             'moving_window_lateral_extent_m', 'moving_window_advance_m', 'cooked_fields_dir', 'window_extent_m')
    before = {n: str(c.get_editor_property(n)) for n in names}
    package = c.get_outermost().get_path_name()
    c.modify()
    c.set_editor_property('enable_moving_window_streaming', True)
    c.set_editor_property('streaming_manifest_path', MANIFEST)
    c.set_editor_property('window_center_m', unreal.Vector2D(320.0, 0.0))
    c.set_editor_property('moving_window_station_extent_m', 640.0)
    c.set_editor_property('moving_window_lateral_extent_m', 250.0)
    c.set_editor_property('moving_window_advance_m', 80.0)
    after = {n: str(c.get_editor_property(n)) for n in names}
    assert unreal.EditorAssetLibrary.save_loaded_asset(c, only_if_is_dirty=False) or \
        unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
    report.write_text(json.dumps(dict(level=LEVEL, package=package, before=before, after=after,
                                      manifest=MANIFEST, manifest_sha256=sha(ROOT / MANIFEST)), indent=2) + '\n')
    unreal.log('RAFTSIM_ZAMBEZI_MOVING_WINDOW ' + json.dumps(after))


if __name__ == '__main__':
    main()
