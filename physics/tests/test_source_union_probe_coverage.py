from types import SimpleNamespace
import numpy as np
import pytest
from prepare_south_fork_union_collision import changed_face_ids


def pair():
    a=SimpleNamespace(xyz=np.array([[0.,0.,0.],[1.,0.,0.],[0.,1.,0.],[1.,1.,0.]]),
                      faces=np.array([[0,1,2],[1,3,2]]))
    b=SimpleNamespace(xyz=a.xyz.copy(),faces=a.faces.copy())
    return a,b


@pytest.mark.parametrize('axis',[0,1,2])
def test_each_coordinate_change_is_covered(axis):
    a,b=pair();b.xyz[0,axis]+=.1
    np.testing.assert_array_equal(changed_face_ids(a,b),[0])


def test_connectivity_only_change_is_covered():
    a,b=pair();b.faces[:]=[[0,1,3],[0,3,2]]
    np.testing.assert_array_equal(changed_face_ids(a,b),[0,1])


def test_unchanged_geometry_has_no_changed_faces():
    a,b=pair();assert not len(changed_face_ids(a,b))


def test_count_changes_are_not_silently_paired():
    a,b=pair();b.faces=b.faces[:1]
    with pytest.raises(ValueError):changed_face_ids(a,b)


def test_approach_station_interpolation_uses_original_geographic_frame():
    from audit_constriction_approach import route_xy
    route=dict(origin_utm_m=[100,200],points=[[0,0,0,0,1],[5,3,4,0,1],[10,3,9,0,1]])
    np.testing.assert_array_equal(route_xy(route,[0,2.5,5,7.5,10]),
        [[100,200],[101.5,202],[103,204],[103,206.5],[103,209]])
    with pytest.raises(ValueError):route_xy(route,[-1])
    with pytest.raises(ValueError):route_xy(route,[11])


def test_moved_centroid_checks_both_partitions(monkeypatch):
    import prepare_south_fork_union_collision as module
    a,b=pair();b.xyz[0,0]+=.15
    a.sample=lambda x,y:np.zeros_like(x)
    revision=SimpleNamespace(original=a,revised=b,origin=np.array([100.,200.]),datum=20.)
    union=SimpleNamespace(terrain_revision=revision)
    monkeypatch.setattr(module,'physical_union_samples',lambda u,xy,parent:(parent+1,np.zeros(len(xy),bool)))
    before,after=module.revision_triangle_probes(union,[100,200],20.)
    assert len(before)==len(after)==2
    assert [r['source_partition'] for r in after]==['original','revised']
    assert all(r['source_triangle_index']==0 for r in after)
    assert after[1]['world_position_cm'][0]-after[0]['world_position_cm'][0]==pytest.approx(5.)


def test_height_only_revision_keeps_original_probe_set(monkeypatch):
    import prepare_south_fork_union_collision as module
    a,b=pair();b.xyz[0,2]+=1
    a.sample=lambda x,y:np.zeros_like(x)
    union=SimpleNamespace(terrain_revision=SimpleNamespace(original=a,revised=b,origin=np.zeros(2),datum=0.))
    monkeypatch.setattr(module,'physical_union_samples',lambda u,xy,parent:(parent,np.zeros(len(xy),bool)))
    before,after=module.revision_triangle_probes(union,[0,0],0.)
    assert len(before)==len(after)==1 and after[0]['source_partition']=='original'
