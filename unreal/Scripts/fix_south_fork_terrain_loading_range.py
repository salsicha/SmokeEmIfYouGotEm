"""Save the verified MainPartition range; retain the exact prior map for recovery."""
import hashlib
import json
from pathlib import Path
import zipfile
import unreal

ROOT = Path(__file__).resolve().parents[2]
LEVEL = '/Game/RaftSim/Maps/L_SouthForkAmerican_FullReach'
REPORT = ROOT/'unreal/Saved/RaftSimValidation/south-fork-terrain-range-normal-v1-20260924.json'
BACKUP = ROOT/'unreal/Saved/RaftSimValidation/south-fork-terrain-range-before-v1-20260924.zip'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    assert 'RaftSimFixTerrainRange' in unreal.SystemLibrary.get_command_line()
    assert not REPORT.exists() and not BACKUP.exists(), 'Inspect prior mutation before retry'
    path = ROOT/'unreal/Content/RaftSim/Maps/L_SouthForkAmerican_FullReach.umap'
    before = sha(path)
    assert before == 'c6bda5ff5f680d22b291eb30a6c902488acd909bb7f2b6177fa7103cdd40399f'
    levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    assert levels.load_level(LEVEL)
    layer = unreal.find_object(None, LEVEL+'.L_SouthForkAmerican_FullReach:PersistentLevel.WorldSettings.WorldPartition_0.WorldPartitionRuntimeHashSet_1.RuntimePartitionLHGrid_0')
    assert layer and layer.get_class().get_name() == 'RuntimePartitionLHGrid'
    runtime_hash = layer.get_outer()
    partitions = runtime_hash.get_editor_property('RuntimePartitions')
    assert len(partitions) == 1 and str(partitions[0].get_editor_property('Name')) == 'MainPartition'
    assert partitions[0].get_editor_property('MainLayer') == layer
    old = layer.get_editor_property('LoadingRange')
    assert 0 < old < 200000, old
    with zipfile.ZipFile(BACKUP, 'x', zipfile.ZIP_DEFLATED) as archive:
        archive.write(path, path.relative_to(ROOT).as_posix())
    layer.modify()
    layer.set_editor_property('LoadingRange', 200000)
    assert layer.get_editor_property('LoadingRange') == 200000
    assert levels.save_current_level()
    REPORT.write_text(json.dumps(dict(old_loading_range_cm=old,
        new_loading_range_cm=200000, map_before_sha256=before,
        map_after_sha256=sha(path), backup=str(BACKUP.relative_to(ROOT)),
        backup_sha256=sha(BACKUP), source_geometry_changed=False,
        runtime_validation_pending=True), indent=2)+'\n')

if __name__ == '__main__':
    try:
        main()
    finally:
        unreal.SystemLibrary.quit_editor()
