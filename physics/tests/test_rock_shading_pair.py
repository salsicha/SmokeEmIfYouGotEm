import importlib.util
from pathlib import Path
import sys
import types
import pytest


@pytest.fixture
def audit(monkeypatch):
    monkeypatch.setitem(sys.modules, 'unreal', types.ModuleType('unreal'))
    path = Path(__file__).resolve().parents[2]/'unreal/Scripts/audit_rock_shading_pair.py'
    spec = importlib.util.spec_from_file_location('rock_shading_pair_test', path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


def test_vertex_reindexing_preserves_directed_triangle(audit):
    v = [(0, 0, 0), (1, 0, 0), (0, 1, 0)]
    old = audit.canonical_triangles(v, [0, 1, 2], [(0, 0, 1)]*3)
    new = audit.canonical_triangles(v[::-1], [1, 0, 2], [(0, .1, .995)]*3)
    assert audit.compare_records(old, new)['changed_normal_corners'] == 3


@pytest.mark.parametrize('indices', [[0, 2, 1], [0, 1, 1]])
def test_winding_or_triangle_change_fails(audit, indices):
    v = [(0, 0, 0), (1, 0, 0), (0, 1, 0)]; n = [(0, 0, 1)]*3
    with pytest.raises(ValueError, match='triangles changed'):
        audit.compare_records(audit.canonical_triangles(v, [0, 1, 2], n), audit.canonical_triangles(v, indices, n))


def test_unchanged_normals_fail(audit):
    r = audit.canonical_triangles([(0, 0, 0), (1, 0, 0), (0, 1, 0)], [0, 1, 2], [(0, 0, 1)]*3)
    with pytest.raises(ValueError, match='No native shading change'): audit.compare_records(r, r)
