"""Pure configuration tests; these do not emulate or certify Unreal collision."""
import importlib.util
import json
from pathlib import Path
import sys
import types

import pytest


@pytest.fixture
def configuration(tmp_path, monkeypatch):
    monkeypatch.setitem(sys.modules,'unreal',types.ModuleType('unreal'))
    script=Path(__file__).resolve().parents[2]/'unreal/Scripts/verify_troublemaker_dem_rock_cap_collision.py'
    spec=importlib.util.spec_from_file_location('rock_collision_config_test',script)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    folder=tmp_path/'tmp/candidate';folder.mkdir(parents=True)
    (folder/'manifest.json').write_text('{}');(folder/'probes.json').write_text('{}')
    record=dict(export_directory='tmp/candidate',probes='tmp/candidate/probes.json',
        report='unreal/Saved/RaftSimValidation/new.json',
        asset='/Game/RaftSim/Environment/GeneratedLocalReview/NewCandidate/SM_Rock')
    path=tmp_path/'config.json'
    def load(**changes):
        path.write_text(json.dumps(record|changes))
        return module.candidate_configuration(path,tmp_path)
    return load,tmp_path


def test_configuration_resolves_only_local_generated_targets(configuration):
    load,root=configuration
    assert load()['export_directory']==root/'tmp/candidate'
    assert load()['report']==root/'unreal/Saved/RaftSimValidation/new.json'


@pytest.mark.parametrize('changes',[
    dict(export_directory='../outside'),dict(probes='../outside.json'),
    dict(report='unreal/Content/source.uasset'),dict(report='unreal/Saved/RaftSimValidation/../../source.json'),
    dict(asset='/Game/RaftSim/Maps/Production'),dict(asset='/Game/RaftSim/Environment/GeneratedLocalReview/../Production')])
def test_configuration_refuses_out_of_scope_paths(configuration,changes):
    with pytest.raises(ValueError):configuration[0](**changes)


def test_configuration_cannot_overwrite_previous_report(configuration):
    load,_=configuration
    report=load()['report'];report.parent.mkdir(parents=True);report.write_text('retained')
    with pytest.raises(ValueError,match='Fresh'):load()
    assert report.read_text()=='retained'
