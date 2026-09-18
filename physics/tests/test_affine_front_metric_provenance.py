import hashlib
import sys
from types import SimpleNamespace

import pytest
import audit_south_fork_affine_front_metric as audit


def fixture(tmp_path,monkeypatch,suffix='.py'):
    monkeypatch.setattr(audit,'ROOT',tmp_path)
    folder=tmp_path/'physics/scripts';folder.mkdir(parents=True)
    path=folder/('old_tool'+suffix);path.write_bytes(b'current')
    old=hashlib.sha256(b'original').hexdigest()
    monkeypatch.setattr(audit,'git_blob',lambda p,r:b'original')
    return path,{str(path):old},{str(path):'a'*40}


def test_changed_tool_needs_explicit_exact_historical_version(tmp_path,monkeypatch):
    path,protected,historical=fixture(tmp_path,monkeypatch)
    with pytest.raises(ValueError,match='Protected source changed'):audit.verify_protected(protected,{})
    current,records=audit.verify_protected(protected,historical)
    assert protected[str(path)]==hashlib.sha256(b'original').hexdigest()
    assert current[str(path)]==hashlib.sha256(b'current').hexdigest()
    assert not records[0]['current_matches_recorded'] and not records[0]['used_for_this_computation']


@pytest.mark.parametrize('kind',('data','imported','wrong-bytes','wrong-revision','unknown'))
def test_source_and_loaded_code_cannot_use_historical_exception(tmp_path,monkeypatch,kind):
    path,protected,historical=fixture(tmp_path,monkeypatch,'.npy' if kind=='data' else '.py')
    if kind=='imported':monkeypatch.setitem(sys.modules,'fake_loaded_physics',SimpleNamespace(__file__=str(path)))
    if kind=='wrong-bytes':monkeypatch.setattr(audit,'git_blob',lambda p,r:b'unrelated')
    if kind=='wrong-revision':historical[str(path)]='HEAD'
    if kind=='unknown':protected={}
    with pytest.raises(ValueError):audit.verify_protected(protected,historical)
