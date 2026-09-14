from fractions import Fraction as F
import numpy as np
import pytest
import test_hydrostatic_energy_transport as original
import test_extremum_preserving_transport as ep_controls
from test_ep_transport_continuity import fixture
from continuous_extremum_transport import ContinuousExtremumTransport as Transport,continuous_slope,exact_continuous_slope
from extremum_preserving_transport import ep_slope
from total_depth_bank_replay import mc


@pytest.mark.parametrize('name',[
    'test_dry_velocities_have_no_mass_influence_and_barrier_does_not_leak',
    'test_second_order_smooth_periodic_mass_rate_in_l1',
    'test_rest_all_dry_and_invalid_requests'])
def test_original_mass_controls_unchanged(monkeypatch,name):
    monkeypatch.setattr(original,'Transport',Transport);getattr(original,name)()


@pytest.mark.parametrize('shape',[(7,9),(1,12),(2,8)])
def test_original_adjoint_and_positive_step_unchanged(monkeypatch,shape):
    monkeypatch.setattr(original,'Transport',Transport)
    original.test_same_face_adjoint_and_mass_positivity(shape)


@pytest.mark.parametrize('name',[
    'test_smooth_refinement_across_phase_direction_and_axis',
    'test_preserve_original_three_wet_cell_accuracy_next_to_dry_stencil'])
def test_existing_phase_and_bank_controls_unchanged(monkeypatch,name):
    monkeypatch.setattr(ep_controls,'Transport',Transport);getattr(ep_controls,name)()


def test_exact_counterexample_slope_constant_and_face_gap_shrinks():
    gaps=[]
    for exponent in (20,24,28):
        eps=F(1,2**exponent);flux=[]
        for t in (-eps,eps):
            values=fixture(t);h=np.array([[float(v) for v in values]])
            assert exact_continuous_slope(values)==F(1,4)
            assert continuous_slope(h,1)[0,2]==.25
            transport=Transport(h,np.zeros_like(h),np.ones((*h.shape,2)),1.,periodic=True)
            flux.append(transport.faces[0]['flux'][0,2])
        gaps.append(abs(flux[1]-flux[0]))
    assert gaps[0]/gaps[1]>8 and gaps[1]/gaps[2]>8


def test_independent_rational_envelope_and_square_step():
    rng=np.random.default_rng(9921)
    for scale in (1.,2.**-500):
        a=rng.integers(-40,40,(3,17)).astype(float)*scale
        for axis in (0,1):
            expected=np.empty_like(a)
            for point in np.ndindex(a.shape):
                values=[]
                for shift in (-2,-1,0,1,2):
                    q=list(point);q[axis]=(q[axis]+shift)%a.shape[axis]
                    values.append(F(float(a[tuple(q)])))
                expected[point]=float(exact_continuous_slope(values))
            np.testing.assert_array_equal(continuous_slope(a,axis),expected)
    h=np.ones((1,24));h[:,8:16]=4.
    np.testing.assert_array_equal(continuous_slope(h,1),0.)


def test_candidate_is_exactly_the_original_mc_ep_magnitude_envelope():
    rng=np.random.default_rng(9922)
    for scale in (1.,2.**-500):
        h=rng.integers(-40,40,(5,97)).astype(float)*scale
        bed=rng.integers(-40,40,h.shape).astype(float)*scale
        for axis in (0,1):
            for other in (None,bed):
                center=.5*(np.roll(h,-1,axis)-np.roll(h,1,axis))
                if other is not None:center+=.5*(np.roll(other,-1,axis)-np.roll(other,1,axis))
                expected=np.sign(center)*np.maximum(abs(mc(h,axis,True,other=other)),abs(ep_slope(h,axis,other)))
                np.testing.assert_array_equal(continuous_slope(h,axis,other),expected)
