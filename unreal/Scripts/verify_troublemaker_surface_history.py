"""Verify prior protected assets or their explicitly recorded terrain revision."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REVISION = ROOT/'unreal/Saved/RaftSimValidation/troublemaker-sparse-rock-integration-20260912.json'
FLANK_REVISION = ROOT/'unreal/Saved/RaftSimValidation/troublemaker-inferred-flanks-integration-20260912.json'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_protected_assets(assets):
    revisions = [json.loads(REVISION.read_text())] if REVISION.exists() else []
    if FLANK_REVISION.exists():
        assert revisions, 'A flank revision requires its preserved captured-support parent'
        revisions.append(json.loads(FLANK_REVISION.read_text()))
    revision = revisions[-1] if revisions else None
    level = ROOT/'unreal/Content/RaftSim/Maps/L_SouthFork_Troublemaker.umap'
    for name, digest in assets.items():
        path = ROOT/name
        if revision and path == level:
            backup = ROOT/'tmp/troublemaker-playable-before-sparse-rock-20260912'/level.name
            assert sha(backup) == digest
            for index, record in enumerate(revisions):
                later = revisions[index+1] if index+1 < len(revisions) else None
                saved = ROOT/later['backup_directory'] if later else None
                assert sha(saved/level.name if saved else level) == record['level_sha256']
                mesh = ROOT/('unreal/Content/'+record['mesh'].removeprefix('/Game/')+'.uasset')
                assert sha(saved/mesh.name if saved else mesh) == record['mesh_sha256']
                texture = ROOT/'unreal/Content/RaftSim/Environment/SouthForkReconstruction/Troublemaker/T_TroublemakerSurfaceAuthority.uasset'
                assert sha(saved/texture.name if saved else texture) == record['authority_texture_sha256']
                source = ROOT/record.get('source_geometry_path',
                    'tmp/troublemaker-sparse-rock-support-20260912/registered_mesh_source.npz')
                assert sha(source) == record['source_geometry_sha256']
                if later:
                    assert later['previous_level_sha256'] == record['level_sha256']
                    assert later['previous_mesh_sha256'] == record['mesh_sha256']
        else:
            assert sha(path) == digest, name
    return revision
