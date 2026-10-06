"""Exact material restoration refuses stale targets and unrelated archive paths."""
import hashlib
import json
from pathlib import Path
import sys
import zipfile

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]/'unreal/Scripts'))
from raftsim_restore_material_backup import restore


@pytest.fixture
def case(tmp_path):
    root = tmp_path/'project'
    saved = root/'unreal/Saved/RaftSimValidation'
    saved.mkdir(parents=True)
    target = root/'unreal/Content/RaftSim/Water/Test.uasset'
    target.parent.mkdir(parents=True)
    target.write_bytes(b'installed candidate')
    original = b'original material bytes'
    baseline = hashlib.sha256(original).hexdigest()
    report = saved/'install.json'
    report.write_text(json.dumps(dict(material='/Game/RaftSim/Water/Test',
        material_sha256=hashlib.sha256(target.read_bytes()).hexdigest(),
        original_graphs={'MP_NORMAL': {'original': {'code': 'unchanged'}}})))
    backup = report.with_suffix('.backup.zip')
    with zipfile.ZipFile(backup,'w') as archive:
        archive.writestr(target.relative_to(root).as_posix(), original)
    return root, report, baseline, saved/'restored.json', target, backup, original


def test_exact_restore_requires_fresh_audit(case):
    root, report, baseline, output, target, backup, original = case
    before_backup = backup.read_bytes()
    result = restore(root, report, baseline, output)
    assert target.read_bytes() == original and backup.read_bytes() == before_backup
    assert result['exact_backup_restoration'] and result['requires_fresh_process_audit']
    assert not result['visual_or_physical_accepted']
    assert result['saved_graphs'] == json.loads(report.read_text())['original_graphs']
    with pytest.raises(AssertionError): restore(root, report, baseline, output)
    assert target.read_bytes() == original


@pytest.mark.parametrize('damage', ['target', 'backup_hash', 'extra_member', 'target_escape', 'output_escape', 'output_exists'])
def test_reject_without_overwriting_target(case, damage):
    root, report, baseline, output, target, backup, original = case
    if damage == 'target': target.write_bytes(b'user edit after installation')
    if damage == 'backup_hash': baseline = '0'*64
    if damage == 'extra_member':
        with zipfile.ZipFile(backup,'a') as archive: archive.writestr('../unrelated.uasset', b'other')
    if damage == 'target_escape':
        data = json.loads(report.read_text()); data['material'] = '/Game/../../unrelated'
        report.write_text(json.dumps(data))
    if damage == 'output_escape': output = root/'unrelated.json'
    if damage == 'output_exists': output.write_text('existing audit')
    before = target.read_bytes()
    with pytest.raises(AssertionError): restore(root, report, baseline, output)
    assert target.read_bytes() == before
    if damage == 'output_exists': assert output.read_text() == 'existing audit'
    else: assert not output.exists()
