"""Actual native calls are separate; these exercise the exact comparison gate."""
import pytest
import json
from south_fork_terrain_replacement import directed_records,compare_native_records


def records():
    old=[(0.,0.,1.),(1.,0.,1.),(0.,1.,1.),(1.,1.,1.)]
    new=[(0.,0.,1.),(1.,0.,2.),(0.,1.,1.),(1.,1.,1.)]
    indices=[0,1,2,1,3,2]
    change=[dict(before=list(old[1]),after=list(new[1]))]
    return old,new,indices,change


def test_native_comparison_allows_only_declared_heights_and_cyclic_reordering():
    old,new,ids,changes=records()
    result=compare_native_records(directed_records(old,ids),directed_records(new,[3,2,1,2,0,1]),changes,2)
    assert result['all_directed_triangles_compared']==2
    assert result['changed_source_vertices']==1 and result['registered_xy_and_winding_bit_exact']


@pytest.mark.parametrize('mutation',['xy','winding','extra_height','wrong_height','missing_height'])
def test_native_comparison_refuses_unrelated_changes(mutation):
    old,new,ids,changes=records()
    if mutation=='xy':new[2]=(.001,1.,1.)
    if mutation=='winding':ids=[0,2,1,1,3,2]
    if mutation=='extra_height':new[3]=(1.,1.,1.01)
    if mutation=='wrong_height':new[1]=(1.,0.,2.01)
    if mutation=='missing_height':new=old
    with pytest.raises(ValueError):
        compare_native_records(directed_records(old,[0,1,2,1,3,2]),directed_records(new,ids),changes,2)


@pytest.fixture
def config_case(tmp_path):
    from south_fork_terrain_replacement import configuration,sha
    def put(name,value):
        path=tmp_path/name;path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(json.dumps(value));return sha(path)
    revision=dict(manifest='tmp/revision.json',manifest_sha256=put('tmp/revision.json',{}),
        mesh_path='tmp/source.npz',revised_geometry_sha256=put('tmp/source.npz','source'),original_geometry_sha256='original')
    geometry=dict(terrain_revision=revision,terrain_union=dict(terrain_revision=revision))
    probes=dict(terrain_revision=revision,terrain_replacement_required=True,geometry_manifest='tmp/geometry.json',
        geometry_manifest_sha256=put('tmp/geometry.json',geometry),parent_mesh_sha256='original')
    export=dict(fbx='tmp/export/terrain.fbx',fbx_sha256=put('tmp/export/terrain.fbx','fbx'),
        source_geometry_sha256=revision['revised_geometry_sha256'],source_bed_sampling='registered_triangles',triangle_count=8)
    put('tmp/export/manifest.json',export)
    raw=dict(export_directory='tmp/export',asset='/Game/RaftSim/Environment/GeneratedLocalReview/Test/SM_Ground')
    def check():
        put('tmp/config.json',raw);return configuration(tmp_path/'tmp/config.json',probes,tmp_path)
    return tmp_path,raw,probes,check


def test_configuration_allows_fresh_local_import_and_exact_readonly_reload(config_case):
    from south_fork_terrain_replacement import sha
    _,raw,_,check=config_case;config=check();package=config['package']
    package.parent.mkdir(parents=True);package.write_bytes(b'saved terrain')
    with pytest.raises(ValueError,match='overwrite'):check()
    raw.update(saved_mesh_sha256=sha(package),saved_source_sha256='a'*64)
    assert check()['saved_mesh_sha256']==sha(package)
    raw['save_verified_mesh']=True
    with pytest.raises(ValueError,match='rewritten'):check()


@pytest.mark.parametrize('key,value',[
    ('asset','/Game/Production'),('asset','/Game/RaftSim/Environment/GeneratedLocalReview/../Production'),
    ('save_verified_mesh','true'),('saved_mesh_sha256','a'*64),('export_directory','../outside')])
def test_configuration_refuses_unsafe_or_partial_requests(config_case,key,value):
    config_case[1][key]=value
    with pytest.raises(ValueError):config_case[3]()


def test_configuration_binds_the_actual_hydraulic_revision(config_case):
    config_case[2]['terrain_revision']=dict(config_case[2]['terrain_revision'],original_geometry_sha256='wrong')
    with pytest.raises(ValueError,match='provenance'):config_case[3]()
