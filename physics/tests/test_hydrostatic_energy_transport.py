import numpy as np
import pytest
from hydrostatic_energy_transport import HydrostaticEnergyTransport as Transport


@pytest.mark.parametrize('shape',[(7,9),(1,12),(2,8)])
def test_same_face_adjoint_and_mass_positivity(shape):
    rng=np.random.default_rng(8401);h=np.exp(rng.uniform(-12,1,shape));b=rng.uniform(0,.5,shape)
    h[rng.random(shape)<.2]=0.;u=rng.normal(size=(*shape,2));a=rng.normal(size=shape)
    originals=[v.copy() for v in (h,b,u)];t=Transport(h,b,u,.5,periodic=True)
    arbitrary=rng.normal(size=u.shape)
    assert abs(np.sum(a*t.apply(arbitrary))-np.sum(arbitrary*t.adjoint(a)))<2e-13
    np.testing.assert_allclose(h[...,None]*t.adjoint(a,normalized=True),t.adjoint(a),atol=2e-14,rtol=0)
    assert np.all(t.mass_rate[h==0]>=0)
    step=min(.01,.9*t.draining_bound);later=t.forward_euler_mass(step)
    assert np.all(later>=0)
    assert abs(float(later.sum()-h.sum()))<2e-13
    for value,before in zip((h,b,u),originals):np.testing.assert_array_equal(value,before)


def test_dry_velocities_have_no_mass_influence_and_barrier_does_not_leak():
    h=np.ones((5,9));h[:,4]=0.;b=np.zeros_like(h);b[:,4]=10.
    u=np.ones((*h.shape,2));changed=u.copy();changed[h==0]=[1e6,-1e6]
    a=Transport(h,b,u,.5,periodic=True);c=Transport(h,b,changed,.5,periodic=True)
    np.testing.assert_array_equal(a.mass_rate,c.mass_rate)
    np.testing.assert_array_equal(a.mass_rate[:,4],0.)
    assert np.all(a.faces[0]['flux'][:,3]==0)
    down=h.copy();down[:,5:]=0.;bed=np.zeros_like(h)
    flowing=Transport(down,bed,u,.5,periodic=True)
    assert np.any(flowing.mass_rate[:,4]>0)  # Real wet-to-dry inflow is not suppressed.


def test_second_order_smooth_periodic_mass_rate_in_l1():
    errors=[]
    for n in (32,64,128):
        dx=2*np.pi/n;x=(np.arange(n)+.5)*dx
        h=(1+.2*np.sin(x+.31))[None];b=.1*np.cos(x+.13)[None]
        u=np.zeros((*h.shape,2));u[...,0]=1+.1*np.cos(x+.47)
        expected=-(.2*np.cos(x+.31)*(1+.1*np.cos(x+.47))-.1*h[0]*np.sin(x+.47))
        t=Transport(h,b,u,dx,periodic=True)
        errors.append(np.mean(abs(t.mass_rate[0]-expected)))
    assert errors[0]/errors[1]>3.2 and errors[1]/errors[2]>3.2


def test_rest_all_dry_and_invalid_requests():
    h=np.zeros((3,4));u=np.zeros((*h.shape,2));t=Transport(h,h,u,1.,periodic=True)
    np.testing.assert_array_equal(t.forward_euler_mass(1.),0.)
    np.testing.assert_array_equal(t.adjoint(np.ones_like(h),normalized=True),0.)
    with pytest.raises(ValueError):Transport(h,h,u,1.,periodic=False)
    with pytest.raises(ValueError):t.forward_euler_mass(0.)
    wet=np.ones_like(h);fast=np.ones_like(u)*10;t=Transport(wet,h,fast,1.,periodic=True)
    with pytest.raises(ValueError,match='draining'):t.forward_euler_mass(t.draining_bound*1.01)
