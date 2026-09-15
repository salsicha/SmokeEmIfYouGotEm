"""Shared physical-height union and immutable dependency checks."""
import json
import numpy as np
import pytest
from south_fork_rock_union import SourceRockUnion,sha
from build_troublemaker_dem_rock_cap import close_cap_below_retained_terrain


@pytest.fixture
def source(tmp_path):
    xyz=np.array([[0,0,3],[1,0,4],[0,1,3.]])
    origin=np.array([100.,200.,20.]);faces=np.array([[0,1,2]])
    parent=tmp_path/'parent.npz';returns=tmp_path/'returns.npz';cap=tmp_path/'cap.npz'
    np.savez(parent,z_m=np.array([[2.,2.],[2.,2.]]))
    absolute=xyz+origin
    np.savez(returns,utm_easting_m=absolute[:,0],utm_northing_m=absolute[:,1],
        navd88_m=absolute[:,2],classification=np.ones(3,dtype=np.uint8))
    v,t,k,_=close_cap_below_retained_terrain(xyz,faces,1.)
    np.savez(cap,vertices_m=xyz,triangles=faces,original_return_index=np.arange(3),
        original_classification=np.ones(3,dtype=np.uint8),solid_vertices_m=v,solid_triangles=t,solid_face_kind=k)
    manifest=dict(schema='raftsim.original_return_rock_cap.v1',
        origin_utm_and_vertical_datum_m=origin.tolist(),inferred_solid=dict(internal_floor_m=1.))
    for name,path in [('source_mesh',parent),('original_returns',returns),('cap',cap)]:
        manifest[name+'_path']=path.name;manifest[name+'_sha256']=sha(path)
    path=tmp_path/'manifest.json';path.write_text(json.dumps(manifest))
    return tmp_path,path,parent,manifest


def load(source):
    root,path,parent,_=source
    return SourceRockUnion(path,root,parent,[100,200],20)


def test_union_preserves_parent_and_shapes_and_reports_only_real_changes(source):
    union=load(source);parent=np.array([[22.,25.,22.]])
    out,changed=union.apply([[100.1,100.8,102]],[[200.1,200.1,202]],parent)
    assert out.shape==parent.shape and changed.shape==parent.shape
    assert out.tolist()[0]==pytest.approx([23.1,25,22])
    assert changed.tolist()==[[True,False,False]]
    assert np.array_equal(parent,[[22,25,22]])
    assert not union.identity['original_terrain_modified']
    assert not union.identity['hydraulics_recooked']


def test_union_never_fills_outside_triangle_inside_bounding_box(source):
    out,changed=load(source).apply(100.9,200.9,22.)
    assert out==22 and not changed


@pytest.mark.parametrize('field',['source_mesh','original_returns','cap'])
def test_modified_dependency_is_rejected(source,field):
    root,_,_,manifest=source
    with (root/manifest[field+'_path']).open('ab') as output:output.write(b'changed')
    with pytest.raises(ValueError,match='dependency'):load(source)


def test_frame_mismatch_and_different_parent_fail(source):
    root,path,parent,_=source
    with pytest.raises(ValueError,match='frames'):SourceRockUnion(path,root,parent,[100,201],20)
    with pytest.raises(ValueError,match='different retained'):SourceRockUnion(path,root,root/'other.npz',[100,200],20)


def test_missing_parent_support_and_exposed_bottom_fail(source):
    union=load(source)
    with pytest.raises(ValueError,match='Finite'):union.apply(100.1,200.1,np.nan)
    with pytest.raises(ValueError,match='bottom exposed'):union.apply(100.1,200.1,20.)


def test_rehashed_cap_cannot_change_the_physical_solid(source):
    root,path,_,manifest=source
    cap=root/manifest['cap_path']
    with np.load(cap) as data:arrays={k:data[k] for k in data.files}
    arrays['solid_vertices_m']=arrays['solid_vertices_m'].copy()
    arrays['solid_vertices_m'][0,2]+=.01
    np.savez(cap,**arrays);manifest['cap_sha256']=sha(cap);path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError,match='do not match'):load(source)


def test_rehashed_cap_cannot_move_captured_roof(source):
    root,path,_,manifest=source
    cap=root/manifest['cap_path']
    with np.load(cap) as data:arrays={k:data[k] for k in data.files}
    arrays['vertices_m']=arrays['vertices_m'].copy();arrays['vertices_m'][0,0]+=.01
    np.savez(cap,**arrays);manifest['cap_sha256']=sha(cap);path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError,match='moved'):load(source)


def test_hydraulic_packet_retains_captured_stage_mask_and_unaffected_owners(source):
    from prepare_south_fork_rock_union_geometry import union_fields
    fields=dict(bed_navd88_m=np.full((80,80),22.),captured_surface_navd88_m=np.full((80,80),23.),
        captured_water_mask=np.ones((80,80),np.uint8),terrain_owner=np.full((80,80),2,np.uint8))
    updated,changed=union_fields(fields,[100,200],load(source))
    assert changed.sum()==3
    assert np.array_equal(updated['captured_water_mask'],fields['captured_water_mask'])
    assert np.array_equal(updated['captured_surface_navd88_m'],fields['captured_surface_navd88_m'])
    assert np.all(updated['terrain_owner'][changed]==5)
    assert np.all(updated['terrain_owner'][~changed]==2)
    assert np.array_equal(updated['bed_navd88_m'][~changed],fields['bed_navd88_m'][~changed])
    assert np.all(fields['bed_navd88_m']==22.)


def test_fresh_input_gate_rejects_old_depth_and_changed_boundary():
    from audit_south_fork_rock_union_input import validate_fresh_package
    scenario=dict(grid=dict(nx=80,ny=80),boundaries=[dict(edge='east',kind='outflow',stage=3.)],
        roughness=.035,fixed_dt=.05)
    bed=np.full((80,80),2.)
    geometry=dict(bed_navd88_m=bed+20,captured_surface_navd88_m=bed+21,captured_water_mask=np.ones((80,80)))
    h=np.ones_like(bed);u=h*.3;v=h*.2
    state=dict(depth=h,u=u,v=v,eta=bed+h,hu=h*u,hv=h*v,wet=h>1.e-6)
    validate_fresh_package(scenario,scenario,bed,state,geometry,20)
    with pytest.raises(ValueError,match='fresh source-stage'):
        validate_fresh_package(scenario,scenario,bed,dict(state,depth=h*.8),geometry,20)
    with pytest.raises(ValueError,match='physical setup'):
        validate_fresh_package(dict(scenario,boundaries=[]),scenario,bed,state,geometry,20)
