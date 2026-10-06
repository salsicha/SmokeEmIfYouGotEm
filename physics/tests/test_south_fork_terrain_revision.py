import numpy as np
import pytest
from south_fork_terrain_revision import RegisteredTerrainRevision


def meshes():
    y,x=np.indices((4,4))
    a=(np.arange(16).reshape(4,4)[:-1,:-1]).ravel()
    faces=np.vstack((np.stack((a,a+1,a+4),1),np.stack((a+1,a+5,a+4),1)))
    original=dict(east_m=x.astype(float),north_m=-y.astype(float),z_m=np.zeros((4,4),np.float32),
        source_surface_m=np.ones((4,4),np.float32),authority=np.full((4,4),2,np.uint8),
        nominal_east_axis_m=np.arange(4.),nominal_north_axis_m=-np.arange(4.),triangles=faces)
    original['authority'][2,2]=3
    revised={k:v.copy() for k,v in original.items()};revised['z_m'][1,1]=-.75
    return original,revised


def test_exact_source_replacement_preserves_unaffected_samples():
    original,revised=meshes();revision=RegisteredTerrainRevision(original,revised,[100,200],20)
    x=np.array([100.,101.,101.25,103.,150.]);y=np.array([200.,199.,198.75,197.,200.])
    parent=np.array([20.,20.,20.,20.,40.])
    result,changed=revision.apply(x,y,parent)
    expected=np.r_[revision.revised.sample(x[:4]-100,y[:4]-200)+20,40.]
    np.testing.assert_array_equal(result,expected)
    np.testing.assert_array_equal(changed,[False,True,True,False,False])
    np.testing.assert_array_equal(parent,[20,20,20,20,40])


def test_stale_or_already_replaced_bed_is_refused():
    original,revised=meshes();revision=RegisteredTerrainRevision(original,revised,[100,200],20)
    with pytest.raises(ValueError,match='exact retained'):
        revision.apply([101],[199],[19.25])


@pytest.mark.parametrize('key',['east_m','north_m','source_surface_m','authority','triangles'])
def test_protected_arrays_cannot_change(key):
    original,revised=meshes();revised[key].flat[0]+=1
    with pytest.raises(ValueError,match='protected'):
        RegisteredTerrainRevision(original,revised,[100,200],20)


def test_measured_height_cannot_change():
    original,revised=meshes();revised['z_m'][2,2]=1
    with pytest.raises(ValueError,match='submerged-prior'):
        RegisteredTerrainRevision(original,revised,[100,200],20)


def test_seam_cannot_change_even_if_inferred():
    original,revised=meshes();revised['z_m'][0,0]=1
    with pytest.raises(ValueError,match='boundary'):
        RegisteredTerrainRevision(original,revised,[100,200],20)
