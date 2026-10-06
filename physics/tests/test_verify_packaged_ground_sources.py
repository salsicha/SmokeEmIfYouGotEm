from copy import deepcopy
import hashlib
import json
from types import SimpleNamespace
import pytest
import verify_packaged_ground_sources as audit
from verify_packaged_ground_sources import FORMAT, expected_sources, verify_native_report, run
from source_asset_retention import IDENTITY


def evidence():
    rows = []
    for name, count in [('Ground', 12), ('Rock', 6404)]:
        asset = '/Game/RaftSim/Environment/'+name
        before = dict(asset=asset, format=FORMAT, collision_lod=0, collision_trace_flag=3,
                      collision_source_sha256=('a' if name == 'Ground' else 'b')*64,
                      triangle_count=count, provider_vertex_count=count+2, flip_normals=True,
                      available=True, allow_cpu_access=False, editor_only_data=True)
        rows.append(dict(asset=asset, before=before, after=dict(before, allow_cpu_access=True),
                         native_source_unchanged=True))
    receipt = dict(schema='raftsim.ground_cpu_retention.v1', completed=True, assets=rows)
    native = dict(passed=True, editor_only_data=False, assets=[
        dict(row['after'], editor_only_data=False, source_matches=True) for row in rows])
    return receipt, native


def test_exact_complete_native_identity_and_order_independence():
    receipt, native = evidence()
    before = deepcopy(receipt)
    native['assets'].reverse()
    assert verify_native_report(expected_sources(receipt), native) == dict(
        assets_verified=2, directed_triangles_verified=6416)
    assert receipt == before  # Historical editor evidence is never rewritten.


@pytest.mark.parametrize('key', IDENTITY)
def test_top_level_pass_cannot_hide_changed_or_missing_identity(key):
    receipt, native = evidence()
    expected = expected_sources(receipt)
    del native['assets'][0][key]
    with pytest.raises(ValueError):
        verify_native_report(expected, native)
    receipt, native = evidence()
    native['assets'][0][key] = native['assets'][1][key] if key in (
        'collision_source_sha256', 'triangle_count', 'provider_vertex_count') else 'changed'
    with pytest.raises(ValueError):
        verify_native_report(expected, native)


@pytest.mark.parametrize('case', ['missing', 'extra', 'duplicate', 'editor', 'row_editor',
                                'cpu', 'available', 'match', 'pass', 'bool_count', 'empty'])
def test_incomplete_or_editor_results_never_qualify(case):
    receipt, native = evidence()
    expected = expected_sources(receipt)
    if case == 'missing': native['assets'].pop()
    if case == 'extra': native['assets'].append(dict(native['assets'][0], asset='/Game/Extra'))
    if case == 'duplicate': native['assets'][1] = dict(native['assets'][0])
    if case == 'editor': native['editor_only_data'] = True
    if case == 'row_editor': native['assets'][0]['editor_only_data'] = True
    if case == 'cpu': native['assets'][0]['allow_cpu_access'] = False
    if case == 'available': native['assets'][0]['available'] = False
    if case == 'match': native['assets'][0]['source_matches'] = False
    if case == 'pass': native['passed'] = 1
    if case == 'bool_count': native['assets'][0]['triangle_count'] = True
    if case == 'empty': expected, native['assets'] = {}, []
    with pytest.raises(ValueError):
        verify_native_report(expected, native)


@pytest.mark.parametrize('case', ['incomplete', 'duplicate', 'empty', 'before_change',
                                'cpu', 'proof', 'asset', 'infinite', 'fraction', 'hash'])
def test_expected_set_must_preserve_complete_retention_proof(case):
    receipt, _ = evidence()
    row = receipt['assets'][0]
    if case == 'incomplete': receipt['completed'] = False
    if case == 'duplicate': receipt['assets'].append(deepcopy(row))
    if case == 'empty': receipt['assets'] = []
    if case == 'before_change': row['before']['triangle_count'] += 1
    if case == 'cpu': row['after']['allow_cpu_access'] = False
    if case == 'proof': row['native_source_unchanged'] = False
    if case == 'asset': row['asset'] = '/Game/Other'
    if case == 'infinite': row['after']['triangle_count'] = float('inf')
    if case == 'fraction': row['after']['triangle_count'] = 1.5
    if case == 'hash': row['after']['collision_source_sha256'] = 'x'*64
    with pytest.raises(ValueError):
        expected_sources(receipt)


def test_existing_evidence_directory_is_never_overwritten(tmp_path):
    sentinel = tmp_path/'report.json'
    sentinel.write_bytes(b'previous evidence')
    with pytest.raises(ValueError, match='Fresh audit directory'):
        run(tmp_path/'absent.exe', 'a'*64, tmp_path/'absent.json', tmp_path/'absent', tmp_path)
    assert sentinel.read_bytes() == b'previous evidence'


@pytest.mark.parametrize('case', ['pass', 'exit_only', 'process_failure', 'editor_report',
                                'changed_exe', 'changed_receipt', 'changed_bundle'])
def test_runner_requires_fresh_native_evidence_not_just_exit_zero(tmp_path, monkeypatch, case):
    # Process orchestration tests use a fake binary, NOT claimed engine evidence.
    receipt, native = evidence()
    project = tmp_path/'package with spaces'/'SmokeEmIfYouGotEm'
    executable = project/'Binaries/Win64/SmokeEmIfYouGotEm.exe'
    executable.parent.mkdir(parents=True)
    executable.write_bytes(b'fake test executable')
    digest = hashlib.sha256(executable.read_bytes()).hexdigest()
    paks = project/'Content/Paks'
    paks.mkdir(parents=True)
    (paks/'test.pak').write_bytes(b'fake test package')
    receipt_path = tmp_path/'receipt.json'
    receipt_path.write_text(json.dumps(receipt))
    output = tmp_path/'fresh audit'
    stage_calls = []

    def stage(bundle, data_root):
        stage_calls.append(data_root)
        return dict(passed=True, generation=len(stage_calls) if case == 'changed_bundle' else 1)

    def process(command, **kwargs):
        assert kwargs['cwd'] == executable.parent
        assert 'timeout' not in kwargs
        assert command[0] == str(executable)
        assert '-nullrhi' in command and '-RaftSimEphemeralProfile' in command
        assert command[-1] == f'-ExecCmds=RaftSim.AuditGroundSources "{output / "expected.json"}" "{output / "native.json"}"'
        expected = json.loads((output/'expected.json').read_text())
        assert len(expected['assets']) == 2
        assert not (output/'native.json').exists()
        if case == 'editor_report': native['editor_only_data'] = True
        if case == 'changed_exe': executable.write_bytes(b'changed')
        if case == 'changed_receipt': receipt_path.write_text('{}')
        if case != 'exit_only': (output/'native.json').write_text(json.dumps(native))
        return SimpleNamespace(returncode=1 if case == 'process_failure' else 0)

    monkeypatch.setattr(audit, 'verify_staged', stage)
    monkeypatch.setattr(audit.subprocess, 'run', process)
    if case == 'pass':
        result = run(executable, digest, receipt_path, tmp_path/'bundle', output)
        assert result['packaged_execution_verified'] is True
        assert result['assets_verified'] == 2 and result['directed_triangles_verified'] == 6416
        assert all(result[key] is False for key in ('gameplay_verified', 'physical_acceptance',
                                                   'visual_acceptance', 'performance_accepted'))
        assert stage_calls == [executable.parent/'RaftSimRuntimeData']*2
    else:
        with pytest.raises((ValueError, FileNotFoundError)):
            run(executable, digest, receipt_path, tmp_path/'bundle', output)
        assert not (output/'report.json').exists()
