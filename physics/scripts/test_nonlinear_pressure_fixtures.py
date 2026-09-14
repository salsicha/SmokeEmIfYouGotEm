import numpy as np
import pytest
from export_nonlinear_pressure_fixtures import fixture


def test_exported_pressure_fields_share_one_quantized_state_without_mutating_input():
    y,x=np.indices((5,9));h=.8+.1*np.sin(x)
    state=np.stack((h,.3*h*np.cos(y),-.2*h*np.sin(x)),axis=-1)
    bed=.01*np.sin(x+y);before=state.copy();before_bed=bed.copy()
    fields,meta=fixture(state,bed,.5,False,'mixed')
    np.testing.assert_array_equal(state,before);np.testing.assert_array_equal(bed,before_bed)
    np.testing.assert_array_equal(fields[0][...,0],fields[1][...,0])
    assert meta['positive_depths_rounded_to_zero']==0
    assert len(fields)==10 and all(np.all(np.isfinite(v)) for v in fields)
    assert fields[5].dtype==np.uint32
    assert fields[6].shape==fields[7].shape==fields[8].shape==(5,9,4)
    assert fields[9].shape==(5,9,2)
    again,other=fixture(state,bed,.5,False,'mixed')
    for first,second in zip(fields,again):np.testing.assert_array_equal(first,second)
    assert meta==other


def test_lake_and_zero_fraction_reference_fields_are_exactly_zero():
    h=np.ones((5,9));state=np.stack((h,h*0,h*0),axis=-1)
    fields,_=fixture(state,h*0,.5,False,'lake')
    for index in (6,7,8,9):np.testing.assert_array_equal(fields[index],0)
    state[...,1]=h
    fields,_=fixture(state,h*0,.5,False,'zero')
    for index in (6,7,8,9):np.testing.assert_array_equal(fields[index],0)


@pytest.mark.parametrize('tiny',[2.**-149,2.**-130,2.**-126])
def test_tiny_positive_pressure_fixture_remains_connected(tiny):
    h=np.ones((5,9));h[2,4]=tiny
    state=np.stack((h,h*.5,-h),axis=-1)
    fields,meta=fixture(state,h*0,.5,False,'nonbreaking')
    assert fields[0][2,4,0]==tiny and fields[1][2,4,0]==tiny
    assert fields[5][2,4]!=0
    assert meta['positive_depths_rounded_to_zero']==0
    assert all(np.isfinite(v).all() for v in fields)
