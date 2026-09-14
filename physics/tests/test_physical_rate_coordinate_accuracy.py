"""Original accuracy failures retained alongside same-operator patch controls."""
import numpy as np
import pytest
from audit_reconstructed_closed_energy import fixture
from reconstructed_energy_reference import metric
from smooth_rational_velocity_stage import make,stage
from rational_physical_momentum_rate import physical_rate


@pytest.fixture(scope='module',params=(2201,2203,2205,2207))
def original(request):
    source,b=fixture(request.param,'smooth',128);h=source[...,0];u=source[...,1:]/h[...,None]
    g=make(h,b,.125);k,_=metric(g,rational=True);root=np.sqrt(h)[...,None]
    v=(k@(root*u).ravel()).reshape(u.shape)/root;r=stage(g,v)
    return g,v,r['depth_rate'],r['canonical_velocity_rate']


@pytest.mark.parametrize('scheme',('block','patch'))
def test_original_energy_coordinate_gate(original,scheme):
    r=physical_rate(*original,derivative_preconditioner=scheme)
    scale=max(1.,abs(r['physical_energy_rate']),abs(r['canonical_energy_rate']))
    assert r['energy_coordinate_error']<=1e-10*scale
