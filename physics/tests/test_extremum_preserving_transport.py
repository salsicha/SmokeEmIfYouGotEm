import numpy as np
import pytest
import test_hydrostatic_energy_transport as original
from extremum_preserving_transport import ExtremumPreservingTransport as Transport,ep_slope,exact_slope
from fractions import Fraction


@pytest.mark.parametrize('name',[
    'test_dry_velocities_have_no_mass_influence_and_barrier_does_not_leak',
    'test_second_order_smooth_periodic_mass_rate_in_l1',
    'test_rest_all_dry_and_invalid_requests'])
def test_original_controls_unchanged(monkeypatch,name):
    monkeypatch.setattr(original,'Transport',Transport)
    getattr(original,name)()


@pytest.mark.parametrize('shape',[(7,9),(1,12),(2,8)])
def test_original_adjoint_and_positivity_unchanged(monkeypatch,shape):
    monkeypatch.setattr(original,'Transport',Transport)
    original.test_same_face_adjoint_and_mass_positivity(shape)


def test_slope_matches_independent_rational_equations():
    rng=np.random.default_rng(4112)
    for scale in (1.,2.**-500):
        values=rng.integers(-40,40,size=(5,21)).astype(float)*scale
        for axis in (0,1):
            expected=np.empty_like(values)
            for point in np.ndindex(values.shape):
                stencil=[]
                for shift in (-2,-1,0,1,2):
                    q=list(point);q[axis]=(q[axis]+shift)%values.shape[axis]
                    stencil.append(Fraction(float(values[tuple(q)])))
                expected[point]=float(exact_slope(stencil))
            np.testing.assert_array_equal(ep_slope(values,axis),expected)


def test_no_slopes_at_square_discontinuity_and_no_dry_gap_lookthrough():
    h=np.ones((1,24));h[:,8:16]=4.
    np.testing.assert_array_equal(ep_slope(h,1),0)
    h[:,12]=0;b=np.zeros_like(h)
    fa,fb=Transport.face_heights(h,b,1)
    for owner in (10,11,12,13,14):
        assert fa[0,owner]==h[0,owner]
        assert fb[0,(owner-1)%24]==h[0,owner]


@pytest.mark.parametrize('scale',[1.,2.**-500])
def test_thin_positive_faces_and_draining_bound(scale):
    h=np.array([[0.,1.,.1,4.,.01,1.,0.,3.]])*scale
    b=np.array([[0.,.3,.4,.1,.2,.1,5.,0.]])*scale
    u=np.ones((*h.shape,2));t=Transport(h,b,u,.5,periodic=True)
    assert all(np.all(f['retained']>=0) for f in t.faces)
    later=t.forward_euler_mass(min(.01,.9*t.draining_bound))
    assert np.all(later>=0)
    assert abs(float(later.sum()-h.sum()))<=4e-15*scale


def test_smooth_refinement_across_phase_direction_and_axis():
    # Extra probes, not replacements for the original fixed-phase check.
    for phase in np.arange(16)*2*np.pi/16:
        for direction in (-1.,1.):
            errors=[]
            for n in (32,64,128):
                dx=2*np.pi/n;x=(np.arange(n)+.5)*dx
                h=(1+.2*np.sin(x+phase))[None];b=.1*np.cos(x+phase-.18)[None]
                u=np.zeros((*h.shape,2));u[...,0]=direction*(1+.1*np.cos(x+phase+.16))
                expected=-direction*(.2*np.cos(x+phase)*(1+.1*np.cos(x+phase+.16))
                    -.1*h[0]*np.sin(x+phase+.16))
                t=Transport(h,b,u,dx,periodic=True)
                errors.append(np.mean(abs(t.mass_rate[0]-expected)))
                rotated=Transport(h.T,b.T,u.transpose(1,0,2)[...,::-1],dx,periodic=True)
                np.testing.assert_allclose(t.mass_rate.T,rotated.mass_rate,atol=1e-14,rtol=0)
            assert errors[0]/errors[1]>3.2 and errors[1]/errors[2]>3.2


def test_preserve_original_three_wet_cell_accuracy_next_to_dry_stencil():
    # EP may not look across a dry gap, but that must not flatten an extra
    # owner whose ORIGINAL three-cell MC reconstruction is fully connected.
    h=np.arange(8,dtype=float)[None];b=np.zeros_like(h)
    original_a,original_b=original.Transport.face_heights(h,b,1)
    a,c=Transport.face_heights(h,b,1)
    for owner in (2,6):
        assert a[0,owner]==original_a[0,owner]
        assert c[0,(owner-1)%8]==original_b[0,(owner-1)%8]
