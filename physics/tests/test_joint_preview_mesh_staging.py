"""Pure staging contract tests; actual native checks remain separately required."""
import importlib.util
import json
from pathlib import Path
import sys
import types

import pytest


@pytest.fixture
def stage(tmp_path,monkeypatch):
    monkeypatch.setitem(sys.modules,'unreal',types.ModuleType('unreal'))
    scripts=Path(__file__).resolve().parents[2]/'unreal/Scripts'
    monkeypatch.syspath_prepend(str(scripts))
    spec=importlib.util.spec_from_file_location('mesh_stage_test',scripts/'stage_south_fork_joint_preview_mesh.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    folder=tmp_path/'tmp/export';folder.mkdir(parents=True);(folder/'manifest.json').write_text('{}')
    native=tmp_path/'unreal/Saved/RaftSimValidation/result.json';native.parent.mkdir(parents=True);native.write_text('{}')
    raw=dict(export_directory='tmp/export',collision_audit='unreal/Saved/RaftSimValidation/result.json',report='tmp/stage.json',
        import_asset='/Game/RaftSim/Environment/GeneratedLocalReview/Import/SM_Rock',
        destination='/Game/RaftSim/Environment/GeneratedLocalReview/Joint/SM_Rock')
    path=tmp_path/'config.json'
    def load(**changes):
        path.write_text(json.dumps(raw|changes));return module.stage_configuration(path,tmp_path)
    return module,load


def test_stage_configuration_keeps_defaults_outside_override_scope(stage):
    _,load=stage;config=load()
    assert config['report'].name=='stage.json' and 'material' not in config


@pytest.mark.parametrize('change',[
    dict(export_directory='../outside'),dict(collision_audit='tmp/not-native.json'),dict(report='unreal/Content/source.uasset'),
    dict(destination='/Game/RaftSim/Maps/Production'),dict(import_asset='/Game/RaftSim/Environment/GeneratedLocalReview/../Production'),
    dict(destination='/Game/RaftSim/Environment/GeneratedLocalReview/Import/SM_Rock')])
def test_stage_configuration_refuses_out_of_scope_or_ambiguous_targets(stage,change):
    with pytest.raises(ValueError):stage[1](**change)


def test_stage_configuration_preserves_existing_report(stage):
    _,load=stage;report=load()['report'];report.write_text('retain')
    with pytest.raises(ValueError,match='Fresh'):load()
    assert report.read_text()=='retain'


def test_triangle_count_is_source_bound_not_old_candidate_constant(stage):
    module,_=stage
    export=dict(source_cap_sha256='cap',fbx_sha256='fbx',triangle_count=6404)
    collision=dict(source_cap_sha256='cap',fbx_sha256='fbx',sampled_full_map_union_verified=True,failures=[],
        native_runtime=dict(field_queries_verified=True,query_count=12800))
    assert module.validate_stage_evidence(export,collision)==6404
    for changed in (dict(sampled_full_map_union_verified=False),dict(sampled_full_map_union_verified='true'),
                    dict(failures=['retained failure']),dict(failures=None),dict(native_runtime=None),
                    dict(native_runtime=dict(field_queries_verified=False,query_count=12800)),
                    dict(native_runtime=dict(field_queries_verified='true',query_count=12800)),
                    dict(native_runtime=dict(field_queries_verified=True,query_count=True)),dict(source_cap_sha256='other')):
        with pytest.raises(ValueError):module.validate_stage_evidence(export,collision|changed)
    for count in (0,-1,1.5,True):
        with pytest.raises(ValueError):module.validate_stage_evidence(export|dict(triangle_count=count),collision)
