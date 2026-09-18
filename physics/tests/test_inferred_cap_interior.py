import numpy as np
import pytest
from infer_cap_interior_surface import supported_plane,infer_surface
from audit_inferred_cap_surface import compare
from build_troublemaker_dem_rock_cap import close_cap_below_retained_terrain


def ring():
    angle=np.arange(16)*2*np.pi/16
    x,y=.5*np.cos(angle),.5*np.sin(angle)
    return np.column_stack([x,y,2+.1*x-.2*y])


def test_plane_fit_is_surrounded_and_reproduces_sloping_neighbors():
    fit=supported_plane([0,0,5],ring())
    assert fit['height_m']==pytest.approx(2,abs=1e-14)
    assert fit['threshold_m']==.3


def test_no_extrapolation_or_sparse_fit():
    points=ring()
    assert supported_plane([0,0,5],points[:7]) is None
    assert supported_plane([0,0,5],points[points[:,0]>=-1e-16]) is None


def test_only_ambiguous_interior_outlier_moves_and_original_arrays_are_immutable():
    xyz=np.vstack([[0,0,5],ring()]);before=xyz.copy()
    cap=dict(vertices_m=xyz.copy(),original_return_index=np.arange(17),boundary_edges=np.array([[1,2],[2,3]]))
    last=np.ones(17,bool);classes=np.ones(17,int)
    surface,protected,changes=infer_surface(cap,np.arange(4,17),xyz,last,classes)
    assert [r['vertex'] for r in changes]==[0]
    assert surface[0,2]==pytest.approx(2,abs=1e-14)
    np.testing.assert_array_equal(surface[protected],xyz[protected])
    np.testing.assert_array_equal(xyz,before)
    classes[0]=2
    surface,_,changes=infer_surface(cap,np.arange(4,17),xyz,last,classes)
    assert not changes
    np.testing.assert_array_equal(surface,xyz)


def test_low_or_consistent_center_is_not_raised_or_polished():
    for height in (1.,2.,2.2):
        xyz=np.vstack([[0,0,height],ring()])
        cap=dict(vertices_m=xyz.copy(),original_return_index=np.arange(17),boundary_edges=np.array([[1,2]]))
        surface,_,changes=infer_surface(cap,np.arange(3,17),xyz,np.ones(17,bool),np.ones(17,int))
        assert not changes
        np.testing.assert_array_equal(surface,xyz)


def test_boundary_z_requires_explicit_hypothesis_and_cannot_move_xy_or_seed():
    xyz=np.vstack([[0,0,5],ring()])
    cap=dict(vertices_m=xyz.copy(),original_return_index=np.arange(17),boundary_edges=np.array([[0,1]]))
    args=(cap,np.arange(1,17),xyz,np.ones(17,bool),np.ones(17,int))
    assert not infer_surface(*args)[2]
    surface,_,changes=infer_surface(*args,infer_boundary_heights=True)
    assert [r['vertex'] for r in changes]==[0]
    np.testing.assert_array_equal(surface[:,:2],xyz[:,:2])
    np.testing.assert_array_equal(surface[1:],xyz[1:])


@pytest.mark.parametrize('point,neighbors,radius',[
    ([0,0,float('nan')],ring(),.75),
    ([0,0,5],np.array([[0,0,float('inf')]]),.75),
    ([0,0,5],ring(),0),
    ([0,0,5],ring(),float('nan')),
])
def test_invalid_fit_inputs_fail_closed(point,neighbors,radius):
    with pytest.raises(ValueError,match='Finite XYZ'):
        supported_plane(point,neighbors,radius)


def test_original_cap_cannot_be_substituted_by_already_fitted_geometry():
    xyz=np.vstack([[0,0,5],ring()])
    cap=dict(vertices_m=xyz.copy(),original_return_index=np.arange(17),boundary_edges=np.array([[0,1]]))
    cap['vertices_m'][0,2]=4
    with pytest.raises(ValueError,match='Original cap XYZ changed'):
        infer_surface(cap,np.arange(1,17),xyz,np.ones(17,bool),np.ones(17,int))


def audit_fixture():
    xyz=np.array([[0.,0.,2.],[1.,0.,2.],[1.,1.,2.],[0.,1.,2.]])
    faces=np.array([[0,1,2],[0,2,3]])
    vertices,solid_faces,kinds,_=close_cap_below_retained_terrain(xyz,faces,0.)
    old=dict(vertices_m=xyz,triangles=faces,original_return_index=np.arange(4),
        original_classification=np.ones(4,np.uint8),boundary_edges=np.array([[0,1],[1,2],[2,3],[3,0]]),
        solid_vertices_m=vertices,solid_triangles=solid_faces,solid_face_kind=kinds)
    after=xyz.copy();after[3,2]=1.5
    fitted,_,_,_=close_cap_below_retained_terrain(after,faces,0.)
    new={k:v.copy() for k,v in old.items() if k!='vertices_m'}
    new.update(original_source_vertices_m=xyz.copy(),surface_vertices_m=after,
        solid_vertices_m=fitted,vertex_authority=np.array([0,0,0,1],np.uint8),
        protected_vertices=np.array([True,True,True,False]))
    probes=[dict(pixel=[10,20],source_hit=dict(source='cap',source_triangle=0,
        source_vertices=solid_faces[0].tolist()))]
    return old,new,probes


def test_audit_does_not_call_unchanged_target_a_repair():
    result=compare(*audit_fixture())
    assert result['changed_vertex_ids']==[3]
    assert result['all_retained_target_triangles_unchanged']


@pytest.mark.parametrize('tamper,message',[
    ('authority','authority'),('source','source/topology'),
    ('footprint','Footprint'),('protected','Protected'),('ray','Retained ray'),
])
def test_audit_rejects_false_provenance(tamper,message):
    old,new,probes=audit_fixture()
    if tamper=='authority':new['vertex_authority'][3]=0
    if tamper=='source':new['original_source_vertices_m'][0,2]=5
    if tamper=='footprint':new['surface_vertices_m'][3,0]=.1
    if tamper=='protected':new['protected_vertices'][3]=True
    if tamper=='ray':probes[0]['source_hit']['source_vertices']=[3,2,1]
    with pytest.raises(ValueError,match=message):compare(old,new,probes)
