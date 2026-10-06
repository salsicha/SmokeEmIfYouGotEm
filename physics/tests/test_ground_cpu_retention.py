import importlib.util
from pathlib import Path
import pytest

SCRIPT = Path(__file__).resolve().parents[2]/'unreal/Scripts/retain_ground_cpu_sources.py'
SPEC = importlib.util.spec_from_file_location('ground_cpu_retention', SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def identity():
    return dict(available=True, allow_cpu_access=False, format='source_v1',
        collision_lod=0, collision_trace_flag=3, collision_source_sha256='a'*64,
        triangle_count=12, provider_vertex_count=24, flip_normals=True)


def test_only_cpu_retention_changes():
    before = identity()
    MODULE.unchanged_source(before, dict(before, allow_cpu_access=True))


@pytest.mark.parametrize('key', MODULE.IDENTITY)
def test_no_identity_change_is_waived(key):
    before = identity()
    after = dict(before, allow_cpu_access=True)
    after[key] = 'changed'
    with pytest.raises(ValueError, match='source changed'):
        MODULE.unchanged_source(before, after)


@pytest.mark.parametrize('key,value', [('available', False), ('allow_cpu_access', False)])
def test_missing_source_or_retention_refuses(key, value):
    before = identity()
    after = dict(before, allow_cpu_access=True)
    after[key] = value
    with pytest.raises(ValueError):
        MODULE.unchanged_source(before, after)


@pytest.mark.parametrize('asset', ['/Game/Other/Mesh', '/Game/RaftSim/Environment/SouthForkReconstruction/../Mesh',
    '/Game/RaftSim/Environment/SouthForkReconstruction//Mesh', '/Game/RaftSim/Environment/GeneratedLocalReview/Mesh.Mesh'])
def test_package_scope_rejects_unrelated_or_ambiguous_assets(asset):
    with pytest.raises(ValueError):
        MODULE.package_file(asset)
