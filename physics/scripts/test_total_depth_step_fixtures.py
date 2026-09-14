import numpy as np
import pytest
from export_total_depth_step_fixtures import step_reference
from export_total_depth_transport_fixtures import synthetic_cases


@pytest.mark.parametrize('multiple',[1,2])
def test_normal_minimum_uniform_state_has_exact_zero_rate_step(multiple):
    h=np.full((2,4),float(np.finfo(np.float32).tiny)*multiple)
    state=np.stack((h,2*h,h*0,h*0),axis=-1)
    initial,_,final,bounds=step_reference(state,h*0,1.,True,True,.001)
    np.testing.assert_array_equal(initial,state);np.testing.assert_array_equal(final,state)
    assert min(bounds)>.001


def test_step_fixtures_rest_and_no_input_mutation():
    for name,state,bed,dx,periodic,second_order in synthetic_cases():
        before=state.copy();before_bed=bed.copy()
        initial,represented_bed,final,bounds=step_reference(state,bed,dx,periodic,second_order,.001)
        np.testing.assert_array_equal(state,before);np.testing.assert_array_equal(bed,before_bed)
        assert np.isfinite(final).all() and np.all(final[...,0]>=0)
        assert min(bounds)>.001
        if name in ('dry','lake_bank'): np.testing.assert_array_equal(final,initial)
        if name in ('dam','first_order_dam'):
            np.testing.assert_array_equal(final[...,2],0)
            np.testing.assert_array_equal(final,np.broadcast_to(final[0:1],final.shape))


def test_explicit_hybrid_reference_preserves_inputs_and_nonbreaking_lake():
    for name,state,bed,dx,periodic,second_order in synthetic_cases():
        before=state.copy();before_bed=bed.copy()
        initial,_,final,_=step_reference(state,bed,dx,periodic,second_order,.001,breaking_model='hybrid_front')
        np.testing.assert_array_equal(state,before);np.testing.assert_array_equal(bed,before_bed)
        assert np.isfinite(final).all() and np.all(final[...,0]>=0)
        if name in ('dry','lake_bank'):np.testing.assert_array_equal(final,initial)
    with pytest.raises(ValueError):step_reference(state,bed,dx,periodic,second_order,.001,breaking_model='unknown')


def test_explicit_none_reference_is_bit_identical_to_default():
    for _,state,bed,dx,periodic,second_order in synthetic_cases():
        expected=step_reference(state,bed,dx,periodic,second_order,.001)
        actual=step_reference(state,bed,dx,periodic,second_order,.001,breaking_model='none')
        for a,b in zip(actual,expected):np.testing.assert_array_equal(a,b)


@pytest.mark.parametrize('breaking_model', ['none', 'hybrid_front'])
@pytest.mark.parametrize('limiter',['continuous','unscaled'])
def test_continuous_step_keeps_rest_positivity_mass_foam_and_original_inputs(breaking_model,limiter):
    for name,state,bed,dx,periodic,second_order in synthetic_cases():
        h=state[...,0];foam=.125*h
        state=np.concatenate((state,foam[...,None]),axis=-1)
        old_state,old_bed=state.copy(),bed.copy()
        initial,_,final,bounds=step_reference(state,bed,dx,periodic,second_order,.001,
            breaking_model=breaking_model,shoreline_limiter=limiter)
        np.testing.assert_array_equal(state,old_state);np.testing.assert_array_equal(bed,old_bed)
        assert np.isfinite(final).all() and np.all(final[..., [0,3]]>=0)
        assert min(bounds)>.001
        if name in ('dry','lake_bank'):np.testing.assert_array_equal(final,initial)
        # The represented Euler stage is explicitly rounded in this parity
        # fixture; compare inventory against that known FP32 precision budget.
        for component in (0,3):
            assert abs(final[...,component].sum()-initial[...,component].sum()) <= 2e-7*initial[...,component].sum()
