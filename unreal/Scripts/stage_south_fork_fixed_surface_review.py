"""Give the bounded geographic review one fixed carrier; preserve physics and backup."""
from pathlib import Path
import hashlib
import json
import shutil
import unreal

ROOT = Path(__file__).resolve().parents[2]
LEVEL = '/Game/RaftSim/Maps/Review/Geographic/SouthForkRegisteredRockPlayable'
MAP = ROOT / 'unreal/Content/RaftSim/Maps/Review/Geographic/SouthForkRegisteredRockPlayable.umap'
EXPECTED = 'fce8fb675b353cb5fc97a7c092c1683a4b2b59d8420e4e22aba12b92ddf0836a'
OUT = ROOT / 'docs/reconstruction-review-2026-09-07/fixed-surface-scene'
BACKUP = ROOT / 'tmp/south-fork-geographic-before-fixed-surface/SouthForkRegisteredRockPlayable.umap'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    if sha(MAP) != EXPECTED or BACKUP.exists() or OUT.exists():
        raise RuntimeError('Unexpected map or prior attempt; inspect before proceeding')
    levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if not levels.load_level(LEVEL):
        raise RuntimeError('Cannot load geographic review')
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
    surfaces = [a for a in actors if a.get_class().get_name() == 'RaftSimWaterSurfaceActor']
    configs = [a for a in actors if a.get_class().get_name() == 'RaftSimRiverWaterConfig']
    if len(surfaces) != 1 or len(configs) != 1:
        raise RuntimeError('Expected one carrier and one hydraulic configuration')
    config = configs[0]
    source_paths = [ROOT / config.get_editor_property('coordinate_map_path'),
                    ROOT / config.get_editor_property('cooked_fields_dir') / 'manifest.json']
    sources = {str(p.relative_to(ROOT)): sha(p) for p in source_paths}
    properties = dict(fixed_curved_grid=True, fixed_curved_grid_center_station_meters=0.0,
                      curved_grid_length_meters=270.0, curved_grid_width_meters=162.0,
                      curved_grid_edge_blend_meters=0.0)
    surface = surfaces[0]
    before = {key: surface.get_editor_property(key) for key in properties}
    BACKUP.parent.mkdir(parents=True)
    shutil.copy2(MAP, BACKUP)
    if sha(BACKUP) != EXPECTED:
        raise RuntimeError('Backup mismatch')
    for key, value in properties.items():
        surface.set_editor_property(key, value)
    if not levels.save_current_level():
        raise RuntimeError('Map save failed')
    if any(sha(ROOT / name) != digest for name, digest in sources.items()):
        raise RuntimeError('Source data changed unexpectedly')
    OUT.mkdir(parents=True)
    (OUT / 'staging.json').write_text(json.dumps(dict(
        level=LEVEL, original_map_sha256=EXPECTED, backup=str(BACKUP.relative_to(ROOT)),
        updated_map_sha256=sha(MAP), before=before, after=properties,
        unchanged_sources=sources, production_promoted=False, visual_acceptance=False,
        note='Same 1.5 m presentation spacing, fixed 270 by 162 m extent; physics unchanged.'
    ), indent=2) + '\n')
    unreal.log('Fixed full-domain review carrier saved; runtime coverage/performance unverified')


if __name__ == '__main__':
    try:
        main()
    finally:
        unreal.SystemLibrary.quit_editor()
