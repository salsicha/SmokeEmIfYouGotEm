"""A momentum-only repair cannot conserve energy with the current donor mass.

Manufactured flat, strictly wet, nonbreaking periodic control. With constant
physical u, Q sqrt(h)u=0 and E_h=g h-|u|²/2, E_p=u. For ANY conservative p_t,
E_t=g*sum(h*h_t)*area. The mass flux must therefore change as part of the fix.
The required energy-conservation tests deliberately retain the exposed failure.
"""
from fractions import Fraction as F
import numpy as np
import pytest
from conservative_rational_stress import stress_stage_physical
from continuous_extremum_transport import ContinuousExtremumTransport, exact_continuous_slope
from rational_primal_energy import evaluate, depth_gradient
from smooth_rational_velocity_stage import make


def exact_mass_control(sign):
    h = tuple(map(F,(1,2,4)))
    slopes = [exact_continuous_slope(tuple(h[(i+j)%3] for j in (-2,-1,0,1,2)))
              for i in range(3)]
    assert slopes == [F(0),F(3,2),F(0)]
    retained = [(h[i]+slopes[i]/2 if sign>0 else h[(i+1)%3]-slopes[(i+1)%3]/2)
                for i in range(3)]
    flux = [F(sign,2)*a for a in retained]
    ht = [-(flux[i]-flux[(i-1)%3])/F(1,2) for i in range(3)]
    energy_rate = F(981,100)*sum(a*b for a,b in zip(h,ht))*F(1,4)
    return ht, energy_rate


@pytest.fixture(params=((0,-1),(0,1),(1,-1),(1,1)))
def control(request):
    axis, sign = request.param
    h = np.array([[1.,2.,4.]])
    if axis == 0:h = h.T
    u = np.zeros((*h.shape,2))
    u[...,1-axis] = sign*.5
    p = h[...,None]*u
    g = make(h,np.zeros_like(h),.5)
    transport = ContinuousExtremumTransport(h,g.bed,u,.5,periodic=True)
    stage = stress_stage_physical(g,p)
    response = evaluate(g,p)
    eh, _ = depth_gradient(g,p,response,transport.mass_rate)
    return g,u,transport,stage,response,eh,exact_mass_control(sign)


def test_independent_constant_velocity_obstruction(control):
    g,u,transport,stage,response,eh,(ht,expected) = control
    np.testing.assert_allclose(transport.mass_rate.ravel(),list(map(float,ht)),rtol=0,atol=1e-14)
    np.testing.assert_allclose(stage['depth_rate'],transport.mass_rate,rtol=0,atol=1e-12)
    np.testing.assert_allclose(response['canonical_velocity'],u,rtol=0,atol=1e-12)
    np.testing.assert_allclose(eh,9.81*g.h-.125,rtol=0,atol=1e-11)
    assert abs(stage['physical_momentum_rate'].sum(axis=(0,1))).max()<1e-10
    assert abs(stage['energy_rate']-float(expected))<1e-10
    assert abs(float(expected))>13
    assert np.min(g.h+.9*transport.draining_bound*transport.mass_rate)>0


def test_nonbreaking_energy_conservation_still_required(control):
    assert abs(control[3]['energy_rate'])<1e-10
