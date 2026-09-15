"""Preview evidence must refer to the same source and actual hydraulic state."""
import pytest

from prepare_south_fork_joint_preview import Dependencies, asset_file, verify_audits
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


@pytest.mark.parametrize('asset', ['/Engine/Rock', '/Game/../../escape', '/Game/', '/Game//Rock', '/Game/A\\B'])
def test_asset_escape_and_ambiguous_paths_rejected(tmp_path, asset):
    with pytest.raises(ValueError):
        asset_file(asset, tmp_path)
