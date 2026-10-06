"""Exercise capture guards with fake engine objects, not engine acceptance."""
import ast
import hashlib
import json
import struct
from pathlib import Path
from types import SimpleNamespace as NS
import traceback

import pytest


@pytest.fixture
def harness(tmp_path):
    path=Path(__file__).resolve().parents[2]/'unreal/Scripts/play_verified_south_fork_terrain.py'
    # Execute the real callbacks without running the top-level Unreal startup.
    tree=ast.parse(path.read_text())
    callbacks=ast.Module(body=[node for node in tree.body if isinstance(node,ast.FunctionDef)],type_ignores=[])
    records=NS(commands=[],errors=[],logs=[],unregistered=[],quit=[],end_play=[],now=10.,actors=[],configs=[])
    world=NS(get_path_name=lambda:'/Game/UEDPIE_0_FullReach')
    records.worlds=[world]
    unreal=NS(StaticMeshActor=type('StaticMeshActor',(),{}),RaftSimRiverWaterConfig=type('WaterConfig',(),{}),
        EditorLevelLibrary=NS(get_pie_worlds=lambda _: records.worlds),
        LevelEditorSubsystem=object,
        get_editor_subsystem=lambda _: NS(editor_request_end_play=lambda:records.end_play.append(True)),
        SystemLibrary=NS(execute_console_command=lambda w,c:records.commands.append(c),
            quit_editor=lambda:records.quit.append(True)),
        log=records.logs.append,log_error=records.errors.append,
        unregister_slate_post_tick_callback=records.unregistered.append)
    unreal.GameplayStatics=NS(get_all_actors_of_class=lambda w,c:
        records.actors if c is unreal.StaticMeshActor else records.configs)
    def actor(mesh,tags=()):
        return NS(tags=tags,get_name=lambda:mesh.rsplit('/',1)[-1],
            static_mesh_component=NS(static_mesh=NS(get_path_name=lambda:mesh)))
    records.actors=[actor('/Game/Revised.Revised'),actor('/Game/Rock.Rock',['RaftSimPhysicalGround'])]
    records.configs=[NS(get_editor_property=lambda key:'paired')]
    env=dict(hashlib=hashlib,json=json,struct=struct,Path=Path,traceback=traceback,unreal=unreal,
        time=NS(perf_counter=lambda:records.now),started=0.,ROOT=tmp_path,
        state={'handle':object()},protected={},report=tmp_path/'report.json',label='test',
        terrain={'mesh_asset':'/Game/Revised','original_mesh_asset':'/Game/Old'},
        descriptor={'mesh_asset':'/Game/Rock.Rock','source_time_seconds':50.,'atlas_manifest':'paired-atlas'},
        config_values={'streaming_manifest_path':'paired'})
    exec(compile(callbacks,str(path),'exec'),env)
    return env,records,actor


def test_nonserializable_delegate_does_not_prevent_verified_capture(harness):
    env,records,_=harness
    env['tick'](0.)
    assert len(records.commands)==1 and not records.errors
    assert env['state']['verified_play_world']=='/Game/UEDPIE_0_FullReach'
    env['tick'](0.)
    assert len(records.commands)==1


@pytest.mark.parametrize('fault',['old_ground','duplicate_ground','wrong_water','unregistered_rock'])
def test_rejects_mismatched_actual_play_before_capture(harness,fault):
    env,records,actor=harness
    if fault=='old_ground':records.actors[0]=actor('/Game/Old.Old')
    if fault=='duplicate_ground':records.actors.append(actor('/Game/Revised.Revised'))
    if fault=='wrong_water':records.configs=[NS(get_editor_property=lambda key:'old')]
    if fault=='unregistered_rock':records.actors[1].tags=[]
    env['tick'](0.)
    assert not records.commands and records.quit
    assert not json.loads(env['report'].read_text())['complete']


def test_missing_streamed_ground_has_bounded_wait(harness):
    env,records,_=harness
    records.actors=[]
    env['tick'](0.)
    assert not records.commands and not records.quit
    records.now+=21
    env['tick'](0.)
    assert records.quit and not records.commands


def test_finish_never_overwrites_existing_evidence(harness):
    env,records,_=harness
    env['report'].write_text('original evidence')
    env['finish']('failed setup')
    assert env['report'].read_text()=='original evidence'
    assert records.quit and records.errors


def test_complete_capture_does_not_promote_acceptance(harness):
    env,records,_=harness
    screenshots=env['ROOT']/'unreal/Saved/Screenshots'
    screenshots.mkdir(parents=True)
    header=b'\x89PNG\r\n\x1a\n'+struct.pack('>I',13)+b'IHDR'+struct.pack('>II',1014,550)
    for i in range(3):(screenshots/f'test_{i:03d}.png').write_bytes(header)
    env['tick'](0.)
    assert records.end_play and not env['report'].exists() and not records.quit
    env['tick'](0.)
    assert not env['report'].exists()
    records.worlds=[]
    env['tick'](0.)
    report=json.loads(env['report'].read_text())
    assert report['complete'] and len(report['screenshots'])==3
    assert report['play_session_ended'] and records.quit
    assert report['actual_capture_size']==[1014,550] and not report['capture_resolution_matched']
    for field in ('linked_v2_loader_exercised','performance_accepted','visual_accepted',
                  'normal_scenario_promoted','saved_map_or_actor_packages'):
        assert report[field] is False
    assert len(records.unregistered)==1


def test_changed_protected_package_rejects_completion(harness):
    env,records,_=harness
    package=env['ROOT']/'map.umap';package.write_bytes(b'changed')
    env['protected'][str(package)]=hashlib.sha256(b'original').hexdigest()
    env['finish']()
    report=json.loads(env['report'].read_text())
    assert not report['complete'] and 'Protected package changed' in report['error']
    assert records.quit


def test_missing_protected_package_reports_failure(harness):
    env,records,_=harness
    env['protected'][str(env['ROOT']/'missing.umap')]='original'
    env['finish']()
    assert not json.loads(env['report'].read_text())['complete'] and records.quit


def test_report_destination_rejects_escape_and_existing_evidence(harness):
    env,_,_=harness
    resolve=env['report_destination'];root=env['ROOT']
    assert resolve(root,'tmp/new.json')==root/'tmp/new.json'
    for value in ('outside.json','tmp/../../outside.json'):
        with pytest.raises(ValueError,match='fresh path'):resolve(root,value)
    (root/'tmp').mkdir();existing=root/'tmp/existing.json';existing.write_text('original')
    with pytest.raises(ValueError,match='fresh path'):resolve(root,'tmp/existing.json')
    assert existing.read_text()=='original'
