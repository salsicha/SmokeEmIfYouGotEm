"""Preview evidence must refer to the same source and actual hydraulic state."""
import pytest

from prepare_south_fork_joint_preview import Dependencies, asset_file, verify_audits, add_cap_dependencies, verify_native_state
from south_fork_rock_union import sha


@pytest.fixture
def audits():
    atlas = dict(input_manifest_sha256='input', source_time_seconds=50.,
                 arrays={n: dict(sha256=n) for n in ('h', 'u', 'v')})
    snapshot = dict(passed=True, input_manifest_sha256='input', time_seconds=50., step=1000,
                    arrays={n: dict(sha256=n) for n in ('h', 'u', 'v')})
    banks = dict(all_artificial_banks_exactly_dry=True, maximum_bank_depth_m=0.,
                 input_manifest_sha256='input', time_seconds=50., step=1000, h_sha256='h')
    coverage = dict(passed=True, failed_rectangles=[], minimum_raft_interior_margin_m=10.,
                    original_water_probes=406823, atlas_manifest_sha256='atlas',
                    repaired_streaming_manifest_sha256='stream')
    return atlas, snapshot, banks, coverage


def test_matching_preview_evidence_is_not_settling_acceptance(audits):
    for row in audits:
        row['settling_accepted'] = False
    verify_audits(*audits, 'atlas', 'stream')
    assert all(row['settling_accepted'] is False for row in audits)


@pytest.mark.parametrize('index,key,value', [
    (0, 'source_time_seconds', float('nan')),
    (0, 'source_time_seconds', 0.),
    (1, 'passed', False),
    (1, 'input_manifest_sha256', 'old'),
    (1, 'time_seconds', 49.),
    (2, 'step', 20),
    (2, 'time_seconds', 1.),
    (2, 'all_artificial_banks_exactly_dry', False),
    (2, 'maximum_bank_depth_m', 1e-20),
    (2, 'h_sha256', 'old'),
    (3, 'passed', False),
    (3, 'failed_rectangles', ['missing']),
    (3, 'minimum_raft_interior_margin_m', 7.999),
    (3, 'original_water_probes', 406822),
    (3, 'atlas_manifest_sha256', 'old'),
    (3, 'repaired_streaming_manifest_sha256', 'old'),
])
def test_mismatched_or_failed_audit_rejected(audits, index, key, value):
    audits[index][key] = value
    with pytest.raises(ValueError):
        verify_audits(*audits, 'atlas', 'stream')


@pytest.mark.parametrize('name', ['h', 'u', 'v'])
def test_each_water_component_has_to_match(audits, name):
    audits[1]['arrays'][name]['sha256'] = 'different snapshot'
    with pytest.raises(ValueError, match='array mismatch'):
        verify_audits(*audits, 'atlas', 'stream')


def test_dependencies_are_normalized_hashed_and_bounded(tmp_path):
    root = tmp_path / 'repo'
    root.mkdir()
    source = root / 'source.bin'
    source.write_bytes(b'original')
    deps = Dependencies(root)
    assert deps.add(source, sha(source)) == 'source.bin'
    assert deps.hashes == {'source.bin': sha(source)}
    with pytest.raises(ValueError, match='Changed dependency'):
        deps.add(source, 'wrong')
    outside = tmp_path / 'outside.bin'
    outside.write_bytes(b'outside')
    with pytest.raises(ValueError, match='escapes repository'):
        deps.add(outside)
    source.write_bytes(b'changed')
    with pytest.raises(ValueError, match='Changed dependency'):
        Dependencies(root).add(source, deps.hashes['source.bin'])


def test_asset_path_matches_its_package(tmp_path):
    assert asset_file('/Game/Review/Rock.Rock', tmp_path) == tmp_path / 'unreal/Content/Review/Rock.uasset'


def test_preview_hashes_interpreted_selection_alongside_original_cap_sources(tmp_path):
    cap={}
    for name in ('source_mesh','original_returns','cap'):
        path=tmp_path/(name+'.bin');path.write_bytes(name.encode())
        cap[name+'_path']=path.name;cap[name+'_sha256']=sha(path)
    selection=tmp_path/'selection.json';selection.write_text('interpreted, not measured')
    cap['reviewed_extension_selection']=dict(path=selection.name,sha256=sha(selection))
    deps=Dependencies(tmp_path);add_cap_dependencies(deps,cap)
    assert len(deps.hashes)==4 and deps.hashes[selection.name]==sha(selection)
    selection.write_text('changed selection')
    with pytest.raises(ValueError,match='Changed dependency'):
        add_cap_dependencies(Dependencies(tmp_path),cap)


@pytest.mark.parametrize('asset', ['/Engine/Rock', '/Game/../../escape', '/Game/', '/Game//Rock', '/Game/A\\B'])
def test_asset_escape_and_ambiguous_paths_rejected(tmp_path, asset):
    with pytest.raises(ValueError):
        asset_file(asset, tmp_path)


@pytest.fixture
def native_state():
    runtime = dict(field_queries_verified=True, atlas_sha256='atlas', fields_manifest='tmp/current/packet.json',
                   fields_manifest_sha256='packet', source_time_seconds=50., window_center_m=[1., 2.],
                   query_count=12800, wet_mismatches=0, solver_steps_run=0)
    collision = dict(failures=[], sampled_full_map_union_verified=True,
                     geometry_manifest_sha256='geometry', native_runtime=runtime)
    def check():
        verify_native_state(collision, 'atlas', 50., 'tmp/current/packet.json', 'packet', [1., 2.], 'geometry')
    return collision, runtime, check


def test_native_initial_state_matches_actual_preview(native_state):
    native_state[2]()


@pytest.mark.parametrize('key,value', [
    ('atlas_sha256', 'previous-atlas'), ('fields_manifest', 'tmp/old/packet.json'),
    ('fields_manifest_sha256', 'old-packet'), ('source_time_seconds', 1.),
    ('source_time_seconds', float('nan')), ('source_time_seconds', float('inf')),
    ('source_time_seconds', None), ('source_time_seconds', True),
    ('window_center_m', [1., 3.]), ('query_count', 12799), ('query_count', True),
    ('wet_mismatches', 1), ('solver_steps_run', 1), ('solver_steps_run', False),
    ('field_queries_verified', False), ('field_queries_verified', 'true'),
])
def test_native_old_or_incomplete_state_is_not_preview_evidence(native_state, key, value):
    native_state[1][key] = value
    with pytest.raises(ValueError):
        native_state[2]()


@pytest.mark.parametrize('key,value', [
    ('geometry_manifest_sha256', 'old-geometry'), ('failures', ['retained failure']),
    ('failures', None), ('sampled_full_map_union_verified', False), ('native_runtime', None),
])
def test_native_failed_or_different_geometry_is_rejected(native_state, key, value):
    native_state[0][key] = value
    with pytest.raises(ValueError):
        native_state[2]()


def test_legacy_native_report_without_state_hashes_is_not_silently_upgraded(native_state):
    for key in ('atlas_sha256', 'fields_manifest_sha256'):
        native_state[1].pop(key)
    with pytest.raises(ValueError, match='atlas mismatch'):
        native_state[2]()
