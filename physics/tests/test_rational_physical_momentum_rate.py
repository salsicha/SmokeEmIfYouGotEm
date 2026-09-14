"""Independent derivative/Legendre controls, not solver acceptance."""
import numpy as np
import pytest
from rational_physical_momentum_rate import physical_rate, factor_transpose_direction
from rational_dual_energy_reference import evaluate, factor_direction
from reconstructed_acceleration_system import ReconstructedAccelerationSystem
from reconstructed_energy_reference import metric
from smooth_pressure_geometry import SmoothPressureGeometryRate
from smooth_rational_velocity_stage import make


@pytest.mark.parametrize('shape',((3,4),(1,7),(2,4)))
def test_full_physical_direction_and_legendre_energy(shape):
    rng=np.random.default_rng(9417);h=1.+rng.random(shape);bed=.2*rng.normal(size=shape)
    v=rng.normal(size=(*shape,2));ht=.1*rng.normal(size=shape);vt=.2*rng.normal(size=v.shape)
    g=make(h,bed,.6);r=physical_rate(g,v,ht,vt)
    direction=SmoothPressureGeometryRate(g,bed,ht)
    for length in (.4052787713439809,.03916567310046354):
        system=ReconstructedAccelerationSystem(g,length)
        z=rng.normal(size=v.shape);s=rng.normal(size=shape)
        w,b=factor_direction(g,direction,z)
        for bottom,forward in ((False,w),(True,b)):
            adj=factor_transpose_direction(system,direction,s,bottom=bottom)
            assert abs(np.sum(s*forward)-np.sum(z*adj))<1e-11
    eps=1e-5; values=[]
    for sign in (-1,1):
        values.append(evaluate(make(h+sign*eps*ht,bed,.6),v+sign*eps*vt)['canonical_gradient_flux'])
    np.testing.assert_allclose((values[1]-values[0])/(2*eps),r['momentum_rate'],rtol=2e-7,atol=2e-9)
    assert r['energy_coordinate_error']<1e-10
    # Independent physical-momentum perturbation and dense metric inversion.
    # This re-expresses the SAME two-pole energy; no alternative closure.
    pt=.2*rng.normal(size=v.shape);energies=[]
    for sign in (-1,1):
        hh=h+sign*eps*ht;pp=r['momentum']+sign*eps*pt;gg=make(hh,bed,.6)
        k,_=metric(gg,rational=True);root=np.sqrt(hh)[...,None]
        vv=(k@(pp/root).ravel()).reshape(v.shape)/root
        energies.append(evaluate(gg,vv)['total'])
    expected=np.sum(r['physical_depth_energy_gradient']*ht+np.sum(v*pt,axis=-1))*.6**2
    assert abs((energies[1]-energies[0])/(2*eps)-expected)<1e-7


@pytest.mark.parametrize('axis',(0,1))
def test_flat_constant_mode_and_zero_direction(axis):
    h=np.array([[1.,2.,4.]])
    if axis==0:h=h.T
    bed=np.zeros_like(h);v=np.zeros((*h.shape,2));v[...,1-axis]=.3
    ht=np.array([[.1,-.2,.3]]).reshape(h.shape);vt=np.full_like(v,.2)
    r=physical_rate(make(h,bed,.5),v,ht,vt)
    np.testing.assert_allclose(r['momentum_rate'],ht[...,None]*v+h[...,None]*vt,rtol=1e-12,atol=1e-12)
    z=physical_rate(make(h,bed,.5),v,np.zeros_like(h),np.zeros_like(v))
    np.testing.assert_array_equal(z['momentum_rate'],0.)


def test_invalid_direction_is_not_repaired():
    g=make(np.ones((1,3)),np.zeros((1,3)),.5);v=np.zeros((1,3,2))
    with pytest.raises(ValueError):physical_rate(g,v,np.ones((3,)),v)
    bad=v.copy();bad[0,0,0]=float('nan')
    with pytest.raises(ValueError):physical_rate(g,v,np.zeros((1,3)),bad)
