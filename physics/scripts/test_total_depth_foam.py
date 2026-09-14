import numpy as np
import pytest
from total_depth_bank_replay import rate
from export_total_depth_step_fixtures import step_reference


@pytest.mark.parametrize('periodic',[False,True])
@pytest.mark.parametrize('second_order',[False,True])
def test_foam_shared_flux_conservation_positivity_and_passivity(periodic,second_order):
    rng=np.random.default_rng(731)
    for _ in range(20):
        h=np.exp(rng.uniform(-8,2,(13,17)))
        u=rng.uniform(-3,3,(*h.shape,2))
        state=np.concatenate((h[...,None],h[...,None]*u),axis=-1)
        bed=rng.uniform(-.2,.2,h.shape);foam=np.exp(rng.uniform(-8,2,h.shape))
        before=foam.copy()
        hydro,bound=rate(state,bed,.5,periodic=periodic,second_order=second_order)
        full,fb=rate(state,bed,.5,periodic=periodic,second_order=second_order,foam=foam)
        np.testing.assert_array_equal(full[...,:3],hydro)
        np.testing.assert_array_equal(foam,before)
        assert fb==bound
        assert abs(full[...,3].sum())<2e-14*max(1,abs(full[...,3]).sum())
        assert np.all(foam+bound*full[...,3]>=0)


def test_constant_concentration_follows_water_and_resting_patch_stays_still():
    y,x=np.indices((13,17));h=.5+.02*x
    state=np.stack((h,h*(.2+.01*y),h*.1),axis=-1);bed=np.zeros_like(h)
    result,_=rate(state,bed,.5,periodic=True,second_order=True,foam=.3*h)
    np.testing.assert_allclose(result[...,3],.3*result[...,0],atol=2e-15,rtol=2e-14)
    bed=.125*(x+y);h=np.maximum(0,1-bed)
    result,_=rate(np.stack((h,h*0,h*0),axis=-1),bed,.5,second_order=True,foam=.2+np.sin(x)**2)
    np.testing.assert_array_equal(result,0)


def test_thin_film_does_not_form_overflowing_foam_concentration():
    h=np.full((5,7),1e-310);foam=np.ones_like(h);foam[:,3]=2
    state=np.stack((h,h,h*0),axis=-1)
    with np.errstate(over='raise',invalid='raise'):
        result,bound=rate(state,np.zeros_like(h),.5,periodic=True,foam=foam)
    assert np.isfinite(result).all() and np.all(foam+bound*result[...,3]>=0)
    assert result[...,3].max()>0 and result[...,3].min()<0


def test_ssprk_foam_patch_moves_without_changing_water_solution():
    y,x=np.indices((13,17));h=np.ones_like(x,dtype=float);bed=h*0
    hydro=np.stack((h,h*.4,h*-.2),axis=-1)
    foam=.01+np.exp(-((x-8)**2+(y-6)**2)/6.)
    initial=np.concatenate((hydro,foam[...,None]),axis=-1)
    _,_,final,_=step_reference(initial,bed,.5,True,True,.001)
    _,_,hydro_final,_=step_reference(hydro,bed,.5,True,True,.001)
    np.testing.assert_array_equal(final[...,:3],hydro_final)
    assert np.all(final[...,3]>=0) and np.max(abs(final[...,3]-initial[...,3]))>1e-5
    assert abs(final[...,3].sum()-np.float32(foam).astype(float).sum())<2e-7


def test_zero_foam_is_not_generated_by_transport_or_pressure():
    y,x=np.indices((13,17));h=1.+.2*np.sin(x*.2);bed=.1*np.cos(y*.3)
    state=np.stack((h,h*(1.+.1*y),h*.3,h*0),axis=-1)
    _,_,final,_=step_reference(state,bed,.5,False,True,.001)
    np.testing.assert_array_equal(final[...,3],0)


@pytest.mark.parametrize('value',[-1,np.nan,np.inf])
def test_invalid_foam_refused(value):
    state=np.zeros((3,3,3));state[...,0]=1;foam=np.zeros((3,3));foam[1,1]=value
    with pytest.raises(ValueError,match='foam'):
        rate(state,np.zeros((3,3)),.5,foam=foam)
