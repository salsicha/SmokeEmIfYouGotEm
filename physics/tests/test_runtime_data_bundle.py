"""Dependency portability/integrity tests, not hydraulic acceptance."""
import json
from pathlib import Path
import shutil
import struct

import pytest

from package_runtime_bundle import Closure, logical_path, prepare, relative_dependency, sha, verify_bundle, verify_staged, validate_coordinate_map


@pytest.fixture
def fixture(tmp_path):
    root = tmp_path/'repo'
    root.mkdir()
    def write(name, data):
        path = root/name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data if isinstance(data, bytes) else (json.dumps(data)+'\n').encode())
        return path
    arrays = {}
    for key in ('bed', 'h', 'u', 'v'):
        path = write('tmp/state/'+key+'.npy', b'array bytes '+key.encode())
        arrays[key] = dict(file='../state/'+key+'.npy', sha256=sha(path))
    atlas = write('tmp/atlas/manifest.json', dict(schema='raftsim.cartesian_state_atlas.v1',
        arrays=arrays, source_time_seconds=600, settled_hydraulics=False))
    bed = write('tmp/fields/bed.npy', b'terrain bytes')
    mask = write('tmp/fields/mask.npy', b'mask bytes')
    write('tmp/fields/manifest.json', dict(schema='raftsim.cooked_flow_fields.v1', bands=[dict(
        arrays=dict(bed=dict(file='bed.npy',sha256=sha(bed)),
                    captured_water_mask=dict(file='mask.npy',sha256=sha(mask))),
        shared_cartesian_state=dict(manifest='../atlas/manifest.json',sha256=sha(atlas)))]))
    write('tmp/stream.json', dict(schema='raftsim.cartesian_water_streaming.v1',
        windows=[dict(cooked_fields_manifest='tmp/fields/manifest.json')]))
    write('physics/route.json', dict(schema='raftsim.curved_river_coordinate_map.v1',
        points=[[0,0,0,0,1],[1,1,0,0,1]]))
    write('physics/hydraulic.json', dict(schema='raftsim.cartesian_water_coordinate_map.v1',
        hydraulic_bounds_m=[0,0,2,2],world_y_sign=-1,vertical_datum_m=220))
    map_path = write('unreal/Content/Map.umap', b'map')
    actor = write('unreal/Content/Actor.uasset', b'actor')
    entries = dict(streaming_manifest='tmp/stream.json', initial_fields_manifest='tmp/fields/manifest.json',
        hydraulic_coordinate_map='physics/hydraulic.json', route_coordinate_map='physics/route.json')
    bindings = write('bindings.json', dict(schema='raftsim.saved_runtime_bindings.v1', level='/Game/Map',
        map_sha256=sha(map_path), bindings=dict(config=dict(package='/Game/Actor',sha256=sha(actor))),
        entrypoints=entries, saved_assets=False))
    return root, bindings, root/'bundle', entries


def test_bundle_remains_complete_without_original_tmp_tree(fixture):
    root, bindings, output, entries = fixture
    expected = {name: row['sha256'] for name,row in Closure(root).collect(entries).items()}
    result = prepare(root, bindings, output)
    # Only isolated pytest fixture inputs are removed, never project data.
    shutil.rmtree(root/'tmp')
    checked = verify_bundle(output)
    assert {row['destination']:row['sha256'] for row in checked['files']} == expected
    assert checked == result and not checked['physical_acceptance']
    assert not checked['packaged_execution_verified']
    assert checked['entrypoints'] == entries


def test_bad_source_hash_produces_no_output(fixture):
    root, bindings, output, _ = fixture
    (root/'tmp/state/h.npy').write_bytes(b'corrupt')
    with pytest.raises(ValueError, match='hash mismatch'):
        prepare(root, bindings, output)
    assert not output.exists()


def test_changed_scene_produces_no_output(fixture):
    root, bindings, output, _ = fixture
    (root/'unreal/Content/Actor.uasset').write_bytes(b'new actor binding')
    with pytest.raises(ValueError, match='scene changed'):
        prepare(root, bindings, output)
    assert not output.exists()


def test_map_only_rebind_retains_all_runtime_payloads(fixture):
    from package_runtime_bundle import rebind_saved_map
    root, bindings, output, _ = fixture
    original = prepare(root, bindings, output)
    inventory = json.loads(bindings.read_text())
    scene = root / original['saved_scene_assets'][0]['path']
    scene.write_bytes(b'new canopy map, unchanged hydraulic actors')
    inventory['map_sha256'] = sha(scene)
    bindings.write_text(json.dumps(inventory))
    revised = rebind_saved_map(output, root, bindings)
    assert revised['files'] == original['files']
    assert revised['entrypoints'] == original['entrypoints']
    assert revised['saved_scene_assets'][1:] == original['saved_scene_assets'][1:]
    assert revised['saved_scene_assets'][0]['sha256'] == sha(scene)
    assert revised['native_bindings_sha256'] == sha(bindings)
    assert verify_bundle(output) == original  # Function must not write/bless inputs.


@pytest.mark.parametrize('change', ['entrypoint', 'actor', 'missing', 'duplicate', 'map', 'saved', 'payload'])
def test_map_rebind_cannot_bypass_existing_gates(fixture, change):
    from package_runtime_bundle import rebind_saved_map
    root, bindings, output, _ = fixture
    original = prepare(root, bindings, output)
    inventory = json.loads(bindings.read_text())
    actor_key = next(iter(inventory['bindings']))
    if change == 'entrypoint': inventory['entrypoints']['streaming_manifest'] = 'another.json'
    if change == 'actor': inventory['bindings'][actor_key]['sha256'] = '0'*64
    if change == 'missing': inventory['bindings'] = {}
    if change == 'duplicate': inventory['bindings']['duplicate'] = inventory['bindings'][actor_key]
    if change == 'map': inventory['map_sha256'] = '0'*64
    if change == 'saved': inventory['saved_assets'] = True
    if change == 'payload': (output/original['files'][0]['source']).write_bytes(b'corrupt')
    bindings.write_text(json.dumps(inventory))
    with pytest.raises(ValueError):
        rebind_saved_map(output, root, bindings)


def test_bundle_refuses_to_overwrite_previous_output(fixture):
    root, bindings, output, _ = fixture
    prepare(root, bindings, output)
    with pytest.raises(ValueError, match='Fresh'):
        prepare(root, bindings, output)


def test_corrupt_bundled_payload_is_rejected(fixture):
    root, bindings, output, _ = fixture
    result = prepare(root, bindings, output)
    (output/result['files'][0]['source']).write_bytes(b'corrupt')
    with pytest.raises(ValueError, match='payload changed'):
        verify_bundle(output)


@pytest.mark.parametrize('name', ['/absolute', '../outside', 'a/../b', 'a//b', 'a/./b', 'C:/path', 'a\\b', ''])
def test_nonportable_or_escaping_logical_paths_rejected(name):
    with pytest.raises(ValueError):
        logical_path(name)


def test_parent_references_are_allowed_only_inside_virtual_root():
    assert relative_dependency('tmp/atlas/manifest.json','../state/h.npy') == 'tmp/state/h.npy'
    with pytest.raises(ValueError):
        relative_dependency('tmp/atlas/manifest.json','../../../outside.npy')


@pytest.mark.parametrize('change', ['duplicate', 'extra', 'missing', 'redirect'])
def test_manifest_cannot_hide_incomplete_or_unrelated_payloads(fixture, change):
    root, bindings, output, _ = fixture
    result = prepare(root, bindings, output)
    if change == 'duplicate': result['files'].append(dict(result['files'][0]))
    if change == 'extra': result['files'].append(dict(result['files'][0], destination='unused.json'))
    if change == 'missing': result['files'] = result['files'][1:]
    if change == 'redirect': result['files'][0]['source'] = '../outside.json'
    (output/'manifest.json').write_text(json.dumps(result))
    with pytest.raises((ValueError, KeyError)):
        verify_bundle(output)


def test_case_collisions_are_rejected_even_on_case_sensitive_hosts(fixture):
    root, _, _, _ = fixture
    closure = Closure(root)
    closure.add('physics/route.json')
    with pytest.raises(ValueError, match='Case-colliding'):
        closure.add('physics/Route.json')


def test_no_arbitrary_nonruntime_files_can_enter_bundle(fixture):
    root, _, _, _ = fixture
    with pytest.raises(ValueError, match='JSON/NumPy'):
        Closure(root).add('private.env')


@pytest.mark.parametrize('changes', [dict(hydraulic_bounds_m=[0,0,0,1]),
    dict(hydraulic_bounds_m=[0,0,float('inf'),1]), dict(world_y_sign=0),
    dict(vertical_datum_m=None), dict(schema='unknown')])
def test_cartesian_coordinate_contract_is_not_a_curved_route(changes):
    data=dict(schema='raftsim.cartesian_water_coordinate_map.v1',
        hydraulic_bounds_m=[0,0,1,1],world_y_sign=-1,vertical_datum_m=220)
    validate_coordinate_map(data)
    with pytest.raises(ValueError):
        validate_coordinate_map(data|changes)


@pytest.mark.parametrize('points', [[[0,0],[1,1]], [[0,0,0,0,1],[0,1,0,0,1]],
    [[0,0,0,0,1],[1,1,0,0,0]]])
def test_curved_coordinate_contract_is_preserved(points):
    with pytest.raises(ValueError):
        validate_coordinate_map(dict(schema='raftsim.curved_river_coordinate_map.v1',points=points))


def test_staging_audit_does_not_use_original_or_bundle_as_fallback(fixture):
    root, bindings, output, _ = fixture
    result = prepare(root, bindings, output)
    stage = root/'standalone/RaftSimRuntimeData'
    for row in result['files']:
        path=stage/row['destination']
        path.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(output/row['source'],path)
    report = verify_staged(output,stage)
    assert report['passed'] and report['files_verified'] == len(result['files'])
    assert not report['external_source_fallback_used'] and not report['packaged_execution_verified']
    (stage/result['files'][0]['destination']).unlink()
    with pytest.raises(FileNotFoundError):
        verify_staged(output,stage)


def test_staging_audit_rejects_corrupt_file_even_with_valid_original(fixture):
    root, bindings, output, _ = fixture
    result = prepare(root, bindings, output)
    stage = root/'standalone/RaftSimRuntimeData'
    for row in result['files']:
        path=stage/row['destination']
        path.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(output/row['source'],path)
    (stage/result['files'][0]['destination']).write_bytes(b'bad staged file')
    with pytest.raises(ValueError,match='Staged runtime payload changed'):
        verify_staged(output,stage)


@pytest.fixture
def curved_fixture(fixture):
    root, bindings, output, entries = fixture
    baseline = struct.pack('<IIiiff', 0x52534246, 1, 2, 2, -1., 2.)
    baseline += struct.pack('<i2f', 2, 0., 2.)
    baseline += struct.pack('<i4f', 4, *([700.] * 4))
    baseline += struct.pack('<i4f', 4, *([.25] * 4))
    baseline += struct.pack('<i4B', 4, 1, 1, 1, 1)
    for part in ('initial', 'transit'):
        folder = root/'tmp/curved'/part
        folder.mkdir(parents=True)
        arrays = {}
        for key in ('bed', 'h', 'u', 'v', 'wet_mask'):
            path = folder/(key+'.npy')
            path.write_bytes((part+key).encode())
            arrays[key] = dict(file=path.name, sha256=sha(path))
        path = folder/'support_band_field_normal.bin'
        path.write_bytes(baseline)
        fields = dict(schema='raftsim.cooked_flow_fields.v1', bands=[dict(band_id='normal', arrays=arrays,
            presentation_baseline=dict(file=path.name, sha256=sha(path)))])
        (folder/'manifest.json').write_text(json.dumps(fields))
    entries.update(initial_fields_manifest='tmp/curved/initial/manifest.json',
                   hydraulic_coordinate_map='physics/route.json')
    (root/entries['streaming_manifest']).write_text(json.dumps(dict(
        schema='raftsim.south_fork.moving_water_streaming.v1',
        full_reach_transit_seed=dict(cooked_fields_manifest='tmp/curved/transit/manifest.json',
            cooked_fields_manifest_sha256=sha(root/'tmp/curved/transit/manifest.json')),
        windows=[dict(cooked_fields_manifest=entries['initial_fields_manifest'])])))
    inventory = json.loads(bindings.read_text())
    inventory['entrypoints'] = entries
    bindings.write_text(json.dumps(inventory))
    return root, bindings, output, entries


def test_curved_bundle_includes_distinct_transit_and_binary_baselines(curved_fixture):
    root, bindings, output, entries = curved_fixture
    result = prepare(root, bindings, output)
    names = {row['destination'] for row in result['files']}
    assert 'tmp/curved/transit/manifest.json' in names
    assert all('tmp/curved/'+part+'/support_band_field_normal.bin' in names for part in ('initial', 'transit'))
    assert len(names) == 16  # 2 x (manifest + 5 arrays + baseline), stream, shared route.
    assert not any('/atlas/' in name or '/state/' in name for name in names)
    stage = root/'standalone/RaftSimRuntimeData'
    for row in result['files']:
        target = stage/row['destination']; target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(output/row['source'], target)
    shutil.rmtree(root/'tmp')  # Only isolated fixture sources, never project data.
    assert verify_bundle(output)['entrypoints'] == entries
    assert verify_staged(output, stage)['files_verified'] == 16
    (stage/'tmp/curved/transit/support_band_field_normal.bin').unlink()
    with pytest.raises(FileNotFoundError):
        verify_staged(output, stage)


@pytest.mark.parametrize('change', ['missing_transit', 'transit_hash', 'missing_baseline', 'baseline_hash',
    'wrong_sidecar_name', 'missing_velocity', 'wrong_coordinates', 'malformed_binary', 'array_count',
    'truncated_binary', 'trailing_binary', 'oversized_binary', 'invalid_spacing'])
def test_curved_bundle_rejects_incomplete_or_corrupt_closure(curved_fixture, change):
    root, bindings, output, entries = curved_fixture
    path = root/entries['streaming_manifest']; stream = json.loads(path.read_text())
    fields_path = root/entries['initial_fields_manifest']; fields = json.loads(fields_path.read_text())
    band = fields['bands'][0]
    if change == 'missing_transit': del stream['full_reach_transit_seed']
    if change == 'transit_hash': stream['full_reach_transit_seed']['cooked_fields_manifest_sha256'] = '0'*64
    if change == 'missing_baseline': del band['presentation_baseline']
    if change == 'baseline_hash': band['presentation_baseline']['sha256'] = '0'*64
    if change == 'wrong_sidecar_name': band['presentation_baseline']['file'] = 'different.bin'
    if change == 'missing_velocity': del band['arrays']['v']
    if change == 'wrong_coordinates':
        inventory = json.loads(bindings.read_text())
        inventory['entrypoints']['hydraulic_coordinate_map'] = 'physics/hydraulic.json'
        bindings.write_text(json.dumps(inventory))
    if change in ('malformed_binary', 'array_count', 'truncated_binary', 'trailing_binary',
                  'oversized_binary', 'invalid_spacing'):
        binary = fields_path.parent/band['presentation_baseline']['file']
        data = bytearray(binary.read_bytes())
        if change == 'malformed_binary': data[:4] = b'bad!'
        elif change == 'array_count': data[24:28] = struct.pack('<i', 2147483647)
        elif change == 'truncated_binary': del data[-1]
        elif change == 'trailing_binary': data.append(0)
        elif change == 'oversized_binary': data[8:16] = struct.pack('<ii', 512, 2147483647)
        elif change == 'invalid_spacing': data[20:24] = struct.pack('<f', float('nan'))
        binary.write_bytes(data)
        band['presentation_baseline']['sha256'] = sha(binary)
    fields_path.write_text(json.dumps(fields)); path.write_text(json.dumps(stream))
    with pytest.raises((ValueError, KeyError)):
        prepare(root, bindings, output)
    assert not output.exists()
