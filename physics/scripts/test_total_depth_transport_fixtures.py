import numpy as np
from export_total_depth_transport_fixtures import synthetic_cases,resting_lake_cases
from export_nonlinear_pressure_fixtures import fixture
from total_depth_bank_replay import mc,hydrostatic_faces
from detail_nonlinear_flux import G
import pytest


@pytest.mark.parametrize('periodic',[False,True])
@pytest.mark.parametrize('axis',[0,1])
def test_factored_hydrostatic_balance_equals_original_equation(periodic,axis):
    rng=np.random.default_rng(913)
    h=rng.uniform(.01,3.,(13,17));bed=rng.uniform(-2.,2.,h.shape);dx=.5
    dh=mc(h,axis,periodic);deta=mc(h,axis,periodic,other=bed)
    _,_,ha,hb,hsa,hsb=hydrostatic_faces(h,bed,dh,deta,axis,periodic)
    p=.25*G*(hsa*hsa+hsb*hsb)
    left=p+.5*G*(ha*ha-hsa*hsa);right=p+.5*G*(hb*hb-hsb*hsb)
    positive=range(1,p.shape[axis]);negative=range(p.shape[axis]-1)
    original=-(np.take(left,positive,axis=axis)-np.take(right,negative,axis=axis))/dx-G*h*(deta-dh)/dx
    jump=.25*G*(hsb-hsa)*(hsb+hsa)
    factored=-(np.take(jump,positive,axis=axis)+np.take(jump,negative,axis=axis))/dx-G*h*deta/dx
    np.testing.assert_allclose(factored,original,atol=8e-14,rtol=2e-14)


def test_transport_fixture_special_cases_and_input_isolation():
    for name,state,bed,dx,periodic,second_order in synthetic_cases():
        before=state.copy();before_bed=bed.copy()
        fields,meta=fixture(state,bed,dx,periodic,'nonbreaking',second_order=second_order)
        np.testing.assert_array_equal(state,before);np.testing.assert_array_equal(bed,before_bed)
        assert all(np.isfinite(field).all() for field in fields)
        assert meta['second_order']==second_order
        if name in ('dry','lake_bank'):
            np.testing.assert_array_equal(fields[2],0)
            np.testing.assert_array_equal(fields[9],0)
        if name=='dry': assert meta['cfl_bound_s'] is None
        if name=='thin_datum':
            assert np.all(fields[1][...,0]>0)
            assert meta['positive_depths_rounded_to_zero']==0
            assert np.any(fields[2][...,1]!=0)


@pytest.mark.parametrize('limiter',['binary','continuous','unscaled'])
def test_rough_lakes_are_exact_represented_equilibria(limiter):
    cases=list(resting_lake_cases());assert len(cases)==8
    for name,state,bed,dx,periodic,second_order in cases:
        before=state.copy();before_bed=bed.copy()
        np.testing.assert_array_equal(state,state.astype(np.float32).astype(float))
        np.testing.assert_array_equal(bed,bed.astype(np.float32).astype(float))
        eta=(state[...,0]+bed)[state[...,0]>0]
        np.testing.assert_array_equal(eta,np.full_like(eta,eta[0]))
        fields,meta=fixture(state,bed,dx,periodic,'nonbreaking',second_order=second_order,shoreline_limiter=limiter)
        np.testing.assert_array_equal(state,before);np.testing.assert_array_equal(bed,before_bed)
        np.testing.assert_array_equal(fields[2],0,err_msg=name)
        np.testing.assert_array_equal(fields[9],0,err_msg=name)
