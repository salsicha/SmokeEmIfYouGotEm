"""Mocked save-scope regressions; these are not native scene validation."""
import importlib.util
import copy
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


@pytest.fixture
def field_followup(binding):
    module, _, _, _ = binding
    source = Path(__file__).resolve().parents[2] / 'unreal/Scripts/inventory_envelope_conveyance_runtime.py'
    spec = importlib.util.spec_from_file_location('inventory_under_test', source)
    inventory = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(inventory)
    old = dict(streaming_manifest='tmp/old/stream.json',
               initial_fields_manifest='tmp/old/region_0008/manifest.json',
               hydraulic_coordinate_map='coords.json', route_coordinate_map='route.json')
    saved = dict(after=old, changed_packages={
        'unreal/Content/Water.uasset': dict(before='original', after='installed'),
        'unreal/Content/Ground.uasset': dict(before='old-ground', after='new-ground')})
    bound = dict(mode='set', level=module.LEVEL, before=dict(old),
                 after=dict(old, streaming_manifest='tmp/new/stream.json',
                            initial_fields_manifest='tmp/new/region_0008/manifest.json'),
                 coordinate_maps_changed=False, run_manager_changed=False,
                 config_package='unreal/Content/Water.uasset',
                 config_package_sha256_before='installed', config_package_sha256_after='next')
    return inventory, saved, bound


def test_field_followup_retains_original_geometry_receipt(field_followup):
    inventory, saved, bound = field_followup
    original = copy.deepcopy(saved)
    updated = inventory.with_field_binding(saved, bound)
    assert saved == original
    assert updated['changed_packages']['unreal/Content/Ground.uasset'] == saved['changed_packages']['unreal/Content/Ground.uasset']
    assert updated['changed_packages']['unreal/Content/Water.uasset']['after'] == 'next'
    assert updated['after'] == bound['after']


@pytest.mark.parametrize('change', ['mode', 'level', 'before', 'coordinates_flag', 'manager_flag',
                                   'package', 'previous_hash', 'coordinates_path', 'window', 'keys'])
def test_field_followup_rejects_changed_identity(field_followup, change):
    inventory, saved, bound = field_followup
    if change == 'mode': bound['mode'] = 'inventory'
    elif change == 'level': bound['level'] = '/Game/Other'
    elif change == 'before': bound['before']['streaming_manifest'] = 'unrelated.json'
    elif change == 'coordinates_flag': bound['coordinate_maps_changed'] = True
    elif change == 'manager_flag': bound['run_manager_changed'] = True
    elif change == 'package': bound['config_package'] = 'unrelated.uasset'
    elif change == 'previous_hash': bound['config_package_sha256_before'] = 'different'
    elif change == 'coordinates_path': bound['after']['hydraulic_coordinate_map'] = 'different.json'
    elif change == 'window': bound['after']['initial_fields_manifest'] = 'tmp/new/region_0009/manifest.json'
    elif change == 'keys': del bound['after']['route_coordinate_map']
    with pytest.raises(ValueError):
        inventory.with_field_binding(saved, bound)


@pytest.fixture
def field_chain(field_followup, tmp_path, monkeypatch):
    inventory, saved, first = field_followup
    monkeypatch.setattr(inventory, 'ROOT', tmp_path)
    first['map_sha256'] = 'map'
    second = copy.deepcopy(first)
    second.update(before=copy.deepcopy(first['after']),
                  after=dict(first['after'], streaming_manifest='tmp/final/stream.json',
                             initial_fields_manifest='tmp/final/region_0008/manifest.json'),
                  config_package_sha256_before='next', config_package_sha256_after='final')
    paths = [tmp_path/'tmp/first.json', tmp_path/'tmp/second.json']
    for path, receipt in zip(paths, (first, second)):
        path.write_text(json.dumps(receipt))
    return inventory, saved, paths


def test_ordered_field_chain_preserves_original_and_records_each_receipt(field_chain):
    import hashlib
    inventory, saved, paths = field_chain
    original = copy.deepcopy(saved)
    updated, proofs = inventory.with_field_binding_reports(saved, paths, 'map')
    assert saved == original
    assert updated['changed_packages']['unreal/Content/Water.uasset'] == dict(before='original', after='final')
    assert updated['changed_packages']['unreal/Content/Ground.uasset'] == saved['changed_packages']['unreal/Content/Ground.uasset']
    assert updated['after']['streaming_manifest'] == 'tmp/final/stream.json'
    assert [p['sha256'] for p in proofs] == [hashlib.sha256(p.read_bytes()).hexdigest() for p in paths]
    assert [p['path'] for p in proofs] == ['tmp/first.json', 'tmp/second.json']


@pytest.mark.parametrize('fault', ['skip', 'reverse', 'repeat', 'map', 'hash', 'coordinates', 'package'])
def test_field_chain_rejects_discontinuous_or_altered_history(field_chain, fault):
    inventory, saved, paths = field_chain
    original = copy.deepcopy(saved)
    if fault == 'skip': paths = paths[1:]
    elif fault == 'reverse': paths = list(reversed(paths))
    elif fault == 'repeat': paths = [paths[0], paths[0]]
    else:
        bound = json.loads(paths[1].read_text())
        if fault == 'map': bound['map_sha256'] = 'other-map'
        elif fault == 'hash': bound['config_package_sha256_before'] = 'wrong'
        elif fault == 'coordinates': bound['after']['route_coordinate_map'] = 'wrong'
        elif fault == 'package': bound['config_package'] = 'unreal/Content/Ground.uasset'
        paths[1].write_text(json.dumps(bound))
    with pytest.raises(ValueError):
        inventory.with_field_binding_reports(saved, paths, 'map')
    assert saved == original


def test_field_receipt_modes_and_legacy_compatibility(field_chain):
    inventory, saved, paths = field_chain
    assert inventory.field_binding_paths({}) == []
    assert inventory.field_binding_paths({'RAFTSIM_ENVELOPE_FIELD_BIND_REPORT': 'tmp/first.json'}) == paths[:1]
    assert inventory.field_binding_paths({'RAFTSIM_ENVELOPE_FIELD_BIND_REPORTS':
                                          '["tmp/first.json", "tmp/second.json"]'}) == paths
    updated, proofs = inventory.with_field_binding_reports(saved, paths[:1], 'map')
    assert updated['changed_packages']['unreal/Content/Water.uasset']['after'] == 'next'
    assert len(proofs) == 1


@pytest.mark.parametrize('value', ['[]', '{}', '"tmp/first.json"', '[null]', '[""]',
                                    '["tmp/../outside.json"]', '["tmp/first.json", "tmp/./first.json"]'])
def test_bad_field_receipt_paths_rejected(field_chain, value):
    inventory, _, _ = field_chain
    with pytest.raises(ValueError):
        inventory.field_binding_paths({'RAFTSIM_ENVELOPE_FIELD_BIND_REPORTS': value})


def test_ambiguous_field_receipt_modes_rejected(field_chain):
    inventory, _, _ = field_chain
    with pytest.raises(ValueError):
        inventory.field_binding_paths({'RAFTSIM_ENVELOPE_FIELD_BIND_REPORT': 'tmp/first.json',
                                       'RAFTSIM_ENVELOPE_FIELD_BIND_REPORTS': '["tmp/second.json"]'})
