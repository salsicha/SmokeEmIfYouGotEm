from fractions import Fraction as F
from dataclasses import replace

import pytest

from subcell_affine_dry_fan import AffineDryFan
from subcell_front_prescribed_trace import FrontPrescribedTrace, face_mass_flux_rate
from test_subcell_affine_dry_fan import rectangle
from test_subcell_affine_front_pressure import fixture
from test_subcell_front_auxiliary_transport import U, V


@pytest.mark.parametrize('normal', ((1, 0), (3, 4), (-2, 1)))
def test_mass_flux_time_rate_reversal_partition_and_independent_time_difference(normal):
    fan = AffineDryFan((0, 0), normal, F(3, 4), (F(2, 5), -F(1, 7)), 3, (F(1, 5), -F(1, 8)))
    xyz = lambda x, y: (x, y, fan.bed+fan.gradient[0]*x+fan.gradient[1]*y)
    a, b, t = xyz(-F(3, 2), -F(2, 5)), xyz(F(3, 2), F(1, 3)), F(1, 5)
    actual = face_mass_flux_rate(fan, a, b, t)
    assert actual == -face_mass_flux_rate(fan, b, a, t)
    middle = tuple(x+F(2, 7)*(y-x) for x, y in zip(a, b))
    assert actual == face_mass_flux_rate(fan, a, middle, t)+face_mass_flux_rate(fan, middle, b, t)
    dt = F(1, 1000000)
    numerical = (fan.face_flux(a, b, t+dt)['volume_rate']-fan.face_flux(a, b, t-dt)['volume_rate'])/(2*dt)
    assert float(actual) == pytest.approx(float(numerical), abs=2e-9)


def test_affine_functional_gradient_and_full_time_derivative():
    fan, fragments, t = fixture()
    op = FrontPrescribedTrace(fan, fragments, t, boundary='prescribed-fan-velocity')
    result = op.evaluate(U, V)
    assert any(x != 0 for x in op.linear)
    # Exactly differentiate the quadratic in each velocity coordinate.
    for row in range(len(U)):
        for axis in range(2):
            before, after = [list(v) for v in U], [list(v) for v in U]
            before[row][axis] -= 1
            after[row][axis] += 1
            assert (op.evaluate(after)['kinetic_energy']-op.evaluate(before)['kinetic_energy'])/2 == result['velocity_gradient'][row][axis]
    dt = F(1, 1000000)
    energy = []
    for direction in (-1, 1):
        shifted = FrontPrescribedTrace(fan, fragments, t+direction*dt, boundary='prescribed-fan-velocity')
        velocities = tuple(tuple(a+direction*dt*b for a, b in zip(u, v)) for u, v in zip(U, V))
        energy.append(shifted.evaluate(velocities)['kinetic_energy'])
    assert float(result['kinetic_time_work']) == pytest.approx(float((energy[1]-energy[0])/(2*dt)), abs=2e-7)
    assert not result['natural_open_pressure_or_coupled_force_or_gameplay_accepted']


def test_boundary_flux_gradient_is_direct_local_kinetic_work():
    fan, fragments, t = fixture()
    op = FrontPrescribedTrace(fan, fragments, t, boundary='prescribed-fan-velocity')
    result, v = op.evaluate(U), op.vector(U)
    for face, derivative in zip(op.boundary_faces, result['boundary_mass_flux_gradient']):
        row = face['row']
        gram = op.geometry.forms[op.geometry.active[row]]['gram']
        jet = (sum((a*b for a, b in zip(op.geometry.divergence[row], v)), op.zero)+op.lift[row], *U[row])
        energies = []
        for sign in (-1, 1):
            perturbed = (jet[0]+sign/op.geometry.volumes[row], *jet[1:])
            energies.append(sum((perturbed[i]*gram[i][j]*perturbed[j]
                                 for i in range(3) for j in range(3)), op.zero)/2)
        assert (energies[1]-energies[0])/2 == derivative


def test_original_winding_and_shared_mass_cancellation_are_preserved():
    fan, fragments, t = fixture()
    a = FrontPrescribedTrace(fan, fragments, t, boundary='prescribed-fan-velocity')
    b = FrontPrescribedTrace(fan, tuple(replace(f, polygon=tuple(reversed(f.polygon))) for f in fragments),
                            t, boundary='prescribed-fan-velocity')
    assert a.evaluate(U, V) == b.evaluate(U, V)
    assert sum(a.geometry.volume_rates, a.zero) == -sum(a.outward_mass_flux, a.zero)


@pytest.mark.parametrize('slope', ((0, 0), (F(1, 5), -F(1, 7))))
def test_uniform_velocity_is_not_reflected_at_prescribed_boundary(slope):
    fan = AffineDryFan((0, 0), (1, 0), 1, (F(2, 5), -F(1, 3)), 2, slope)
    fragments = tuple(rectangle(x0=x, x1=x+1, bed=2, slope=slope) for x in (-4, -3))
    t = F(1, 10)
    op = FrontPrescribedTrace(fan, fragments, t, boundary='prescribed-fan-velocity')
    _, velocity = fan.state((-F(5, 2), 0), t)
    reflected = [sum((a*b for a, b in zip(row, velocity*2)), op.zero) for row in op.geometry.divergence]
    assert any(d != 0 for d in reflected)  # Negative control: walls DO change this state.
    assert all(d+b == 0 for d, b in zip(reflected, op.lift))
    result = op.evaluate((velocity, velocity))
    expected = sum((velocity[i]*form['gram'][i+1][j+1]*velocity[j]
                    for form in op.geometry.forms for i in range(2) for j in range(2)), op.zero)/2
    assert result['kinetic_energy'] == expected


def test_dry_domain_has_no_fabricated_boundary_unknown():
    fan = AffineDryFan((0, 0), (1, 0), 1, (0, 0), 0, (0, 0))
    op = FrontPrescribedTrace(fan, (rectangle(x0=4, x1=5),), F(1, 10), boundary='prescribed-fan-velocity')
    assert op.geometry.active == () and op.boundary_faces == []
    assert op.evaluate(())['kinetic_energy'] == 0


def test_positive_subfloat_trace_is_retained():
    fan = AffineDryFan((0, 0), (1, 0), 1, (0, 0), 0, (0, 0), gravity=1)
    t, epsilon = F(1, 10), F(1, 10**400)
    op = FrontPrescribedTrace(fan, (rectangle(x0=2*t-epsilon, x1=2*t, y0=0, y1=1),),
                              t, boundary='prescribed-fan-velocity')
    assert op.geometry.volumes[0] > 0 and float(op.geometry.volumes[0]) == 0
    assert op.lift[0] != 0
    assert any(f['outward_mass_flux'] != 0 for f in op.boundary_faces)
    assert op.evaluate(((0, 0),))['kinetic_energy'] > 0


def test_unspecified_open_pressure_and_invalid_velocity_are_rejected():
    fan, fragments, t = fixture()
    with pytest.raises(ValueError):
        FrontPrescribedTrace(fan, fragments, t, boundary='open')
    op = FrontPrescribedTrace(fan, fragments, t, boundary='prescribed-fan-velocity')
    with pytest.raises(ValueError):
        op.evaluate(((0, 0),))
