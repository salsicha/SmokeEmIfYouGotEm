from dataclasses import replace
from fractions import Fraction as F
import math

import numpy as np
import pytest
from scipy.integrate import quad

from subcell_inlet_lateral_energy import lateral_energy_flux
from subcell_inlet_lateral_flux import lateral_flux
from subcell_inlet_sweep_geometry import InletSweep
from test_subcell_inlet_sweep_geometry import fixture
from test_subcell_inlet_face_transport import split


def bounds(result):
    return result['outward_energy_rate_per_density_bounds']


@pytest.mark.parametrize('velocity', [(2,0), (2,F(1,5)), (3,F(1,2))])
@pytest.mark.parametrize('datum', [0, 10, 100])
def test_energy_matches_physical_distance_quadrature_of_interface_state(velocity, datum):
    sweep, receiver = fixture()
    sweep = replace(sweep, velocity=velocity)
    result = lateral_energy_flux(sweep, receiver, energy_datum=datum)
    speed = math.hypot(*map(float, velocity));g = float(sweep.gravity)
    age = float(sweep.time_root**3)
    def energy(distance):
        h = float(sweep.height_scale)*np.cbrt(age-distance/speed)
        bed = float(receiver.polygon[0][2])+distance/speed*float(sum(a*b for a,b in zip(receiver.gradient, sweep.velocity)))
        star_depth = 4*h/9
        normal_speed = 2*math.sqrt(g*h)/3
        # Direct energy+pressure definition, not the implementation's polynomial.
        e = star_depth*(.5*(speed**2+normal_speed**2)+.5*g*star_depth+g*(bed-datum))
        return normal_speed*(e+.5*g*star_depth**2)
    expected = quad(energy, 0, speed*age, epsabs=1e-13, epsrel=1e-11)[0]
    lo, hi = bounds(result)
    np.testing.assert_allclose(float((lo+hi)/2), expected, rtol=1e-10, atol=1e-13)
    assert result['outward_volume_rate_bounds'] == lateral_flux(sweep,receiver)['outward_volume_momentum_rate_bounds'][0]
    assert result['wet_side_energy_debit_rate_bounds'] == (-hi,-lo)
    assert result['dry_side_energy_credit_rate_bounds'] == (lo,hi)
    assert not result['coupled_time_or_energy_or_native_or_gameplay_accepted']


@pytest.mark.parametrize('h,g,tangent,bed', [(.25,9.81,.7,-2), (2.,1.,-3.,5.), (1e-8,9.81,.1,0.)])
def test_independent_dry_half_fan_energy_equals_interface_transfer(h,g,tangent,bed):
    # Self-similar 1D homogeneous fan at t=1. This checks the interface law,
    # not finite-time spreading of the spatially varying sloping-bed inlet.
    c = math.sqrt(g*h)
    def energy(xi):
        depth = (2*c-xi)**2/(9*g);normal = 2*(c+xi)/3
        return depth*(.5*(normal**2+tangent**2)+.5*g*depth+g*bed)
    integrated = quad(energy,0,2*c,epsabs=1e-30)[0]
    mass = 8*h*c/27
    expected = mass*(.5*tangent**2+F(2,3)*g*h+g*bed)
    np.testing.assert_allclose(integrated,float(expected),rtol=1e-13,atol=0)


def test_source_partitions_and_same_shared_front_keep_one_energy_flux():
    sweep, receiver = fixture()
    whole = bounds(lateral_energy_flux(sweep,receiver))
    parts = [bounds(lateral_energy_flux(sweep,p)) for p in split(receiver,F(3,200))]
    lo,hi = (sum(p[j] for p in parts) for j in range(2))
    assert lo <= whole[1] and whole[0] <= hi
    assert hi-lo < F(1,10**10)*max(map(abs,whole))
    sweep = replace(sweep,velocity=(2,F(1,5)))
    corner = (F(20,11),F(2,11),F(12,11))
    wet = replace(receiver,polygon=(receiver.polygon[0],corner,receiver.polygon[2]))
    dry = replace(receiver,polygon=(receiver.polygon[0],receiver.polygon[1],corner))
    result = lateral_energy_flux(sweep,receiver)
    assert bounds(lateral_energy_flux(sweep,wet)) == bounds(lateral_energy_flux(sweep,dry)) == bounds(result)


def test_rotation_and_large_shift_with_same_energy_reference_are_exact():
    sweep, receiver = fixture()
    sweep = replace(sweep,velocity=(2,F(1,5)))
    shift = F(10**15)
    move = lambda p: (-p[1]+F(10**12),p[0]-F(10**12),p[2]+shift)
    changed = replace(sweep,edge=tuple(move(p) for p in sweep.edge),velocity=(-sweep.velocity[1],sweep.velocity[0]))
    fragment = replace(receiver,polygon=tuple(move(p) for p in reversed(receiver.polygon)),gradient=(-receiver.gradient[1],receiver.gradient[0]))
    assert bounds(lateral_energy_flux(sweep,receiver)) == bounds(lateral_energy_flux(changed,fragment,energy_datum=shift))


def test_reference_shift_changes_energy_by_same_mass_not_zero():
    sweep, receiver = fixture()
    base = lateral_energy_flux(sweep,receiver)
    changed = lateral_energy_flux(sweep,receiver,energy_datum=100)
    qlo,qhi = base['outward_volume_rate_bounds']
    lo,hi = bounds(base);a,b = bounds(changed)
    assert a <= hi-100*sweep.gravity*qlo and lo-100*sweep.gravity*qhi <= b
    assert b < 0 < lo


def test_positive_subfloat_energy_and_exact_empty_intersection():
    sweep, receiver = fixture()
    tiny = InletSweep(sweep.edge,(F(1,10**126),0),1,F(1,10**255))
    result = lateral_energy_flux(tiny,receiver)
    assert bounds(result)[0] > 0 and float(bounds(result)[0]) == 0.
    assert result['maximum_scaled_energy_width'] < F(1,10**12)
    outside = replace(receiver,polygon=tuple((x,y+3,z+3) for x,y,z in receiver.polygon))
    assert bounds(lateral_energy_flux(sweep,outside)) == (0,0)


def test_invalid_geometry_and_unresolved_energy_are_rejected():
    sweep, receiver = fixture()
    with pytest.raises(ValueError,match='gradient and vertices'):
        lateral_energy_flux(sweep,replace(receiver,gradient=(0,0)))
    with pytest.raises(ValueError,match='bound unresolved'):
        lateral_energy_flux(sweep,split(receiver,F(3,200))[0],max_depth=1)
    with pytest.raises(ValueError,match='root bits'):
        lateral_energy_flux(sweep,receiver,root_bits=True)
    with pytest.raises(ValueError,match='integration bound'):
        lateral_energy_flux(sweep,receiver,relative_bound=0)
