"""Mocked save-scope regressions; these are not native scene validation."""
import importlib.util
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest


@pytest.fixture
def binding(monkeypatch, tmp_path):
    saves = []
    unreal = SimpleNamespace(
        EditorLoadingAndSavingUtils=SimpleNamespace(
            save_packages=lambda packages, dirty: saves.append((packages, dirty)) or True),
        log=lambda message: None)
    monkeypatch.setitem(sys.modules, 'unreal', unreal)
    source = Path(__file__).resolve().parents[2] / 'unreal/Scripts/bind_south_fork_discharge_bed_runtime.py'
    spec = importlib.util.spec_from_file_location('runtime_binding_under_test', source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setattr(module, 'ROOT', tmp_path)
    (tmp_path / 'tmp').mkdir()
    props = dict(streaming_manifest_path='tmp/old/stream.json',
                 cooked_fields_dir='tmp/old/region_0008', coordinate_map_path='coords.json')
    package = object()
    config = SimpleNamespace(get_name=lambda: 'Water', get_package=lambda: package,
                             modify=lambda: None, get_editor_property=props.__getitem__,
                             set_editor_property=props.__setitem__,
                             get_class=lambda: SimpleNamespace(get_name=lambda: 'RaftSimRiverWaterConfig'))
    manager = SimpleNamespace(get_name=lambda: 'Manager',
                              get_editor_property=lambda key: 'route.json',
                              get_class=lambda: SimpleNamespace(get_name=lambda: 'RaftSimRunManager'))
    descs = [SimpleNamespace(name='Water', actor_package='/Game/Water'),
             SimpleNamespace(name='Manager', actor_package='/Game/Manager')]
    monkeypatch.setattr(module, 'load', lambda: (descs, config, manager))
    for name in ('unreal/Content/Water.uasset', 'unreal/Content/Manager.uasset', module.MAP_PATH,
                 'tmp/new/streaming_manifest_coverage_checked.json', 'tmp/new/region_0008/manifest.json'):
        file = tmp_path / name
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text('{}')
    monkeypatch.setenv('RAFTSIM_BIND_MODE', 'set')
    monkeypatch.setenv('RAFTSIM_BIND_REPORT', 'tmp/report.json')
    monkeypatch.setenv('RAFTSIM_RUNTIME_EXPORT', 'tmp/new')
    return module, unreal, saves, package


def test_saves_only_external_water_package(binding):
    module, _, saves, package = binding
    module.main()
    assert saves == [([package], False)]
    report = json.loads((module.ROOT / 'tmp/report.json').read_text())
    assert report['after']['initial_fields_manifest'] == 'tmp/new/region_0008/manifest.json'
    assert not report['coordinate_maps_changed'] and not report['run_manager_changed']


def test_failed_save_has_no_bulk_fallback_or_success_receipt(binding):
    module, unreal, saves, _ = binding
    unreal.EditorLoadingAndSavingUtils.save_packages = lambda *args: saves.append(args) or False
    with pytest.raises(RuntimeError, match='Failed to save'):
        module.main()
    assert len(saves) == 1
    assert not (module.ROOT / 'tmp/report.json').exists()


def test_inventory_does_not_save(binding, monkeypatch):
    module, _, saves, _ = binding
    monkeypatch.setenv('RAFTSIM_BIND_MODE', 'inventory')
    module.main()
    assert saves == []
    assert not json.loads((module.ROOT / 'tmp/report.json').read_text())['saved_assets']


@pytest.mark.parametrize('mode,report', [('typo', 'tmp/report.json'),
                                       ('set', 'tmp/../outside.json'),
                                       ('set', 'unreal/report.json'),
                                       ('set', 'tmp/new/region_0008/manifest.json')])
def test_bad_request_rejected_before_loading_scene(binding, monkeypatch, mode, report):
    module, _, saves, _ = binding
    monkeypatch.setenv('RAFTSIM_BIND_MODE', mode)
    monkeypatch.setenv('RAFTSIM_BIND_REPORT', report)
    monkeypatch.setattr(module, 'load', lambda: pytest.fail('must reject before loading scene'))
    with pytest.raises(ValueError):
        module.main()
    assert saves == []
