from fractions import Fraction as F

import numpy as np
import pytest

from subcell_affine_front_total_energy import AffineFrontTotalEnergyVariation
from subcell_affine_moving_pressure import AffineMovingPressureMetric
from test_subcell_affine_moving_pressure import trace, P, PT
from test_subcell_affine_front_variation import independent_energy
from test_subcell_front_pressure_variation import primitives, floats


def fixture(time=F(1, 5), datum=F(1, 3)):
    boundary = trace(time)
    metric = AffineMovingPressureMetric.from_trace(boundary)
    solved = metric.evaluate(P, PT)
    total = AffineFrontTotalEnergyVariation(boundary, metric, P, energy_datum=datum, solved_state=solved)
    return boundary, metric, solved, total


def state(boundary, solved, coordinate):
    g = boundary.geometry
    result = primitives(g)
    result['boundary_flux'] = np.array([float(f['outward_mass_flux']) for f in boundary.boundary_faces])
    result['spatial'] = floats([g.forms[i]['depth_spatial_moments'] for i in g.active])
    result['bed'] = np.array([float(g.forms[i]['bed_at_origin']) for i in g.active])
    if coordinate == 'canonical':
        result['p'] = floats(solved['canonical_momentum'])
    return result


def independent_total(boundary, values, coordinate, datum=1/3):
    kinetic = independent_energy(boundary, **{k: v for k, v in values.items() if k not in ('spatial', 'bed')},
                                 coordinate=coordinate)
    g = boundary.geometry
    gravity = np.array([float(g.forms[i]['gravity']) for i in g.active])
    potential = np.sum(gravity*((values['bed']-datum)*values['moments'][:, 0]+values['moments'][:, 1]/2
                               +np.sum(values['slopes']*values['spatial'], axis=1)))
    return kinetic+potential


@pytest.mark.parametrize('coordinate', ('physical', 'canonical'))
@pytest.mark.parametrize('kind', ('p', 'moments', 'slopes', 'columns', 'boundary_flux', 'spatial', 'bed'))
def test_every_total_partial_against_independently_rebuilt_affine_poles(coordinate, kind):
    boundary, _, solved, total = fixture()
    values = state(boundary, solved, coordinate)
    expected = np.array(total.gradients[coordinate]['momentum' if kind == 'p' else kind], dtype=float)
    measured = np.zeros_like(expected)
    assert independent_total(boundary, values, coordinate) == pytest.approx(float(total.total_energy), rel=2e-13)
    for index in np.ndindex(expected.shape):
        changed = {k: v.astype(complex) for k, v in values.items()}
        changed[kind][index] += 1e-25j
        measured[index] = independent_total(boundary, changed, coordinate).imag/1e-25
    np.testing.assert_allclose(measured, expected, rtol=1e-10, atol=1e-10)


def test_full_time_work_preserves_boundary_lift_and_both_coordinates():
    boundary, metric, solved, total = fixture()
    physical = total.time_work(PT)
    canonical = total.time_work(solved['canonical_momentum_rate'], momentum_coordinate='canonical')
    assert total.kinetic_energy == solved['kinetic_energy']
    assert total.kinetic_energy != metric.dot(metric.vector(P), metric.vector(solved['canonical_velocity']))/2
    assert physical['energy_direction'] == canonical['energy_direction']
    assert physical['kinetic_energy_direction'] == solved['kinetic_energy_rate']
    assert physical['boundary_flux_work'] != 0
    assert physical['spatial_moment_work'] != 0
    for result in (physical, canonical):
        terms = ('momentum_work', 'depth_moment_work', 'bed_gradient_work', 'face_column_work',
                 'boundary_flux_work', 'spatial_moment_work', 'bed_height_work')
        assert sum(result[key] for key in terms) == result['energy_direction']
        assert not result['conservative_force_or_open_boundary_or_gameplay_accepted']


def test_datum_shift_is_exact_external_mass_work_not_a_momentum_force():
    boundary, metric, solved, before = fixture(datum=0)
    delta = F(17, 3)
    after = AffineFrontTotalEnergyVariation(boundary, metric, P, energy_datum=delta, solved_state=solved)
    g = boundary.geometry
    mass = sum(g.forms[i]['gravity']*g.volumes[row] for row, i in enumerate(g.active))
    rate = sum(g.forms[i]['gravity']*g.volume_rates[row] for row, i in enumerate(g.active))
    assert after.total_energy-before.total_energy == -delta*mass
    assert after.time_work(PT)['energy_direction']-before.time_work(PT)['energy_direction'] == -delta*rate
    for coordinate in ('physical', 'canonical'):
        for key in ('momentum', 'columns', 'boundary_flux', 'slopes', 'spatial', 'bed'):
            assert after.gradients[coordinate][key] == before.gradients[coordinate][key]


@pytest.mark.parametrize('spatial,bed', (((), (0, 0)), (((0,), (0, 0)), (0, 0)), (((0, 0), (0, 0)), (0,))))
def test_incomplete_new_primitive_directions_are_rejected(spatial, bed):
    boundary, _, _, total = fixture()
    g = boundary.geometry
    with pytest.raises(ValueError, match='Spatial moments'):
        total.work(PT, [(0, 0, 0)]*2, [(0, 0)]*len(g.faces), [(0, 0)]*2,
                   [0]*len(boundary.boundary_faces), spatial, bed)


@pytest.mark.parametrize('corruption', ('bed', 'gravity', 'saved_velocity'))
def test_original_geometry_and_solved_state_are_not_silently_repaired(corruption):
    from copy import deepcopy
    boundary, metric, solved, _ = fixture()
    if corruption == 'bed':
        boundary.geometry.forms[0]['bed_at_origin'] += F(1, 10**400)
    elif corruption == 'gravity':
        boundary.geometry.forms[0]['gravity'] = 0
    else:
        solved = deepcopy(solved)
        rows = [list(row) for row in solved['canonical_velocity']]
        rows[0][0] += F(1, 10**400)
        solved['canonical_velocity'] = rows
    with pytest.raises(ValueError):
        AffineFrontTotalEnergyVariation(boundary, metric, P, solved_state=solved)


def test_total_time_rate_converges_against_fresh_geometry_and_momentum():
    _, _, _, total = fixture()
    exact = total.time_work(PT)['energy_direction']
    errors = []
    for divisor in (200, 400, 800):
        eps = F(1, 5*divisor)
        energies = []
        for sign in (-1, 1):
            boundary = trace(F(1, 5)+sign*eps)
            metric = AffineMovingPressureMetric.from_trace(boundary)
            momentum = tuple(tuple(x+sign*eps*y for x, y in zip(row, rate)) for row, rate in zip(P, PT))
            energies.append(AffineFrontTotalEnergyVariation(boundary, metric, momentum,
                                                            energy_datum=F(1, 3)).total_energy)
        errors.append(abs(float((energies[1]-energies[0])/(2*eps)-exact)))
    assert all(a/b > 3.8 for a, b in zip(errors, errors[1:]))
    assert errors[-1] < 1e-6
