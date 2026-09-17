from dataclasses import replace
from fractions import Fraction as F
import math

import numpy as np
import pytest
from scipy.integrate import quad

from subcell_dry_front_flux import flux
from subcell_source_face_section import SourceFaceSection
from subcell_inlet_lateral_flux import lateral_flux
from subcell_inlet_sweep_geometry import InletSweep
from test_subcell_inlet_sweep_geometry import fixture
from test_subcell_inlet_face_transport import split


def mid(result):
    return np.array([float((a+b)/2) for a,b in result['outward_volume_momentum_rate_bounds']])


@pytest.mark.parametrize('velocity', [(2,0),(2,F(1,5)),(3,F(1,2))])
def test_integrated_flux_matches_existing_local_riemann_solver(velocity):
    sweep, receiver = fixture()
    sweep = replace(sweep, velocity=velocity)
    u = np.array(velocity, float)
    speed = np.linalg.norm(u)
    normal = np.array([u[1],-u[0]])/speed
    section = SourceFaceSection((((0,0),(1,0)),))
    # Integrate in physical distance along the ray, not the implementation's r.
    length = speed*float(sweep.time_root**3)
    def at(distance, j):
        h = float(sweep.height_scale)*np.cbrt(float(sweep.time_root**3)-distance/speed)
        return flux(section,h,0.,u,normal,float(sweep.gravity))[0][j]
    expected = [quad(lambda d: at(d,j),0,length,epsabs=1e-13,epsrel=1e-10)[0] for j in range(3)]
    np.testing.assert_allclose(mid(lateral_flux(sweep,receiver)),expected,rtol=1e-9,atol=1e-13)


def test_full_flux_closed_form_and_paired_signs():
    sweep, receiver = fixture()
    result = lateral_flux(sweep,receiver)
    mass = 16/81*2*math.sqrt(float(sweep.gravity))*float(sweep.time_root)**4.5
    np.testing.assert_allclose(mid(result),[mass,2*mass,-8/45*float(sweep.gravity)*2*float(sweep.time_root)**5],rtol=1e-14)
    for debit,credit in zip(result['wet_side_debit_rate_bounds'],result['dry_side_credit_rate_bounds']):
        assert debit == (-credit[1],-credit[0])
    assert result['positive_lateral_transfer_proven']
    assert not result['coupled_time_or_energy_or_native_or_gameplay_accepted']


def test_shared_front_uses_one_flux_not_two_one_sided_pressures():
    sweep, receiver = fixture()
    sweep = replace(sweep,velocity=(2,F(1,5)))
    corner = (F(20,11),F(2,11),F(12,11))
    wet = replace(receiver,polygon=(receiver.polygon[0],corner,receiver.polygon[2]))
    dry = replace(receiver,polygon=(receiver.polygon[0],receiver.polygon[1],corner))
    whole = lateral_flux(sweep,receiver)
    for piece in (wet,dry):
        assert lateral_flux(sweep,piece)['outward_volume_momentum_rate_bounds'] == whole['outward_volume_momentum_rate_bounds']


@pytest.mark.parametrize('cut',[F(7,256),F(3,200)])
def test_partition_preserves_whole_flux_enclosures(cut):
    sweep, receiver = fixture()
    parts = [lateral_flux(sweep,p) for p in split(receiver,cut)]
    whole = lateral_flux(sweep,receiver)
    for j,(lo,hi) in enumerate(whole['outward_volume_momentum_rate_bounds']):
        a,b = (sum(p['outward_volume_momentum_rate_bounds'][j][k] for p in parts) for k in range(2))
        assert a <= hi and lo <= b
        assert b-a < F(1,10**10)*max(abs(lo),abs(hi))


def test_rotation_winding_and_large_coordinate_shift_preserve_flux():
    sweep, receiver = fixture()
    sweep = replace(sweep,velocity=(2,F(1,5)))
    move = lambda p: (-p[1]+F(10**12),p[0]-F(10**12),p[2]+F(10**15))
    changed = replace(sweep,edge=tuple(move(p) for p in sweep.edge),velocity=(-sweep.velocity[1],sweep.velocity[0]))
    fragment = replace(receiver,polygon=tuple(move(p) for p in reversed(receiver.polygon)),gradient=(-receiver.gradient[1],receiver.gradient[0]))
    mass,x,y = lateral_flux(sweep,receiver)['outward_volume_momentum_rate_bounds']
    assert lateral_flux(changed,fragment)['outward_volume_momentum_rate_bounds'] == (mass,(-y[1],-y[0]),x)


def test_positive_subfloat_flux_is_not_erased():
    sweep, receiver = fixture()
    tiny = InletSweep(sweep.edge,(F(1,10**126),0),1,F(1,10**255))
    result = lateral_flux(tiny,receiver)
    assert result['outward_volume_momentum_rate_bounds'][0][0] > 0
    assert float(result['outward_volume_momentum_rate_bounds'][0][0]) == 0.
    assert result['maximum_relative_mass_width'] < F(1,10**12)


def test_resolution_failure_and_missing_ray_are_explicit():
    sweep, receiver = fixture()
    with pytest.raises(ValueError,match='bound unresolved'):
        lateral_flux(sweep,split(receiver,F(3,200))[0],max_depth=1)
    with pytest.raises(ValueError,match='root bits'):
        lateral_flux(sweep,receiver,root_bits=True)
    with pytest.raises(ValueError,match='integration bound'):
        lateral_flux(sweep,receiver,relative_bound=0)
    outside = replace(receiver,polygon=tuple((x,y+3,z+3) for x,y,z in receiver.polygon))
    assert lateral_flux(sweep,outside)['outward_volume_momentum_rate_bounds'] == ((0,0),)*3


@pytest.mark.parametrize('h,g',[(.25,9.81),(2.,1.),(1e-8,9.81)])
def test_independent_centered_fan_positive_half_conserves_interface_flux(h,g):
    # Exact self-similar fan into dry water: integral of conserved state over
    # x>0 at t=1 equals the constant interface flux. This is NOT a 2D step.
    c = math.sqrt(g*h)
    depth = lambda xi: (2*c-xi)**2/(9*g)
    speed = lambda xi: 2*(c+xi)/3
    volume = quad(lambda xi: depth(xi),0,2*c,epsabs=1e-30)[0]
    momentum = quad(lambda xi: depth(xi)*speed(xi),0,2*c,epsabs=1e-30)[0]
    section = SourceFaceSection((((0,0),(1,0)),))
    value = flux(section,h,0.,[0,0],[1,0],g)[0]
    np.testing.assert_allclose(value,[volume,momentum,0],rtol=1e-13,atol=0)
