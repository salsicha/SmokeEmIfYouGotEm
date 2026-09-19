from copy import deepcopy
from fractions import Fraction as F

import numpy as np
import pytest

from finite_depth_pressure_reference import LENGTHS, WEIGHTS
from subcell_affine_dry_fan import AffineDryFan
from subcell_affine_front_variation import AffineFrontPressureVariation
from subcell_affine_moving_pressure import AffineMovingPressureMetric
from subcell_front_prescribed_trace import FrontPrescribedTrace
from subcell_front_pressure_variation import FrontPressureVariation
from test_subcell_affine_dry_fan import rectangle
from test_subcell_affine_moving_pressure import trace, P, PT, ZERO
from test_subcell_front_pressure_variation import primitives, floats


def independent_energy(boundary, p, moments, slopes, columns, boundary_flux, coordinate):
    """Rebuild all primitives and affine dual terms without implementation matrices."""
    g, n = boundary.geometry, len(boundary.geometry.active)
    dtype = np.result_type(p, moments, slopes, columns, boundary_flux)
    d = np.zeros((n, 2*n), dtype=dtype)
    positions = {owner: row for row, owner in enumerate(g.active)}
    for face, column in zip(g.faces, columns):
        owners = face['owners']
        if any(owner not in positions for owner in owners):
            continue
        incidence = np.zeros((n, 2), dtype=dtype)
        incidence[positions[owners[0]]] = -column
        if len(owners) == 2:
            incidence[positions[owners[1]]] = column
        for owner in owners:
            row = positions[owner]
            d[row] += incidence.ravel()/(len(owners)*moments[row, 0])
    b = np.zeros(n, dtype=dtype)
    for face, flux in zip(boundary.boundary_faces, boundary_flux):
        b[face['row']] += flux/moments[face['row'], 0]
    c, l, k = np.zeros((2*n, 2*n), dtype=dtype), np.zeros(2*n, dtype=dtype), 0
    for row in range(n):
        h1, h2, h3 = moments[row]
        x, y = slopes[row]
        gram = np.array([[h3, -1.5*x*h2, -1.5*y*h2], [-1.5*x*h2, 3*x*x*h1, 3*x*y*h1],
                         [-1.5*y*h2, 3*x*y*h1, 3*y*y*h1]], dtype=dtype)
        j = np.zeros((3, 2*n), dtype=dtype)
        j[0] = d[row]
        j[1, 2*row] = j[2, 2*row+1] = 1
        lift = np.array([b[row], 0, 0], dtype=dtype)
        c += j.T@gram@j
        l += j.T@gram@lift
        k += lift@gram@lift/2
    mass = np.repeat(moments[:, 0], 2)
    mm = np.diag(mass)
    response, shift, dual_constant = (1-float(np.sum(WEIGHTS)))*mm, np.zeros(2*n, dtype=dtype), 0
    for lam, w in zip(LENGTHS, WEIGHTS):
        h = mm+lam*c
        s = np.linalg.solve(h, -lam*l)
        response += w*mm@np.linalg.solve(h, mm)
        shift += w*mass*s
        dual_constant += w*(s@h@s/2-lam*k)
    v = np.linalg.solve(response, p.ravel()-shift) if coordinate == 'physical' else p.ravel()/mass
    return v@response@v/2-dual_constant


def fixture():
    boundary = trace()
    m = AffineMovingPressureMetric.from_trace(boundary)
    result = m.evaluate(P, PT)
    return boundary, m, result, AffineFrontPressureVariation(boundary, m, P, solved_state=result)


@pytest.mark.parametrize('coordinate', ('physical', 'canonical'))
@pytest.mark.parametrize('kind', ('p', 'moments', 'slopes', 'columns', 'boundary_flux'))
def test_every_original_primitive_partial_matches_independent_complex_step(coordinate, kind):
    boundary, m, result, variation = fixture()
    state = primitives(boundary.geometry)
    state['boundary_flux'] = np.array([float(f['outward_mass_flux']) for f in boundary.boundary_faces])
    if coordinate == 'canonical':
        state['p'] = floats(result['canonical_momentum'])
    assert independent_energy(boundary, **state, coordinate=coordinate) == pytest.approx(float(result['kinetic_energy']), rel=2e-13)
    key = 'momentum' if kind == 'p' else kind
    expected = np.array(variation.gradients[coordinate][key], dtype=float)
    measured = np.zeros_like(expected)
    for index in np.ndindex(expected.shape):
        probe = {k: v.astype(complex) for k, v in state.items()}
        probe[kind][index] += 1e-25j
        measured[index] = independent_energy(boundary, **probe, coordinate=coordinate).imag/1e-25
    np.testing.assert_allclose(measured, expected, rtol=1e-10, atol=1e-10)


@pytest.mark.parametrize('coordinate', ('physical', 'canonical'))
def test_primitive_time_work_equals_complete_affine_energy_rate(coordinate):
    boundary, m, result, variation = fixture()
    rate = PT if coordinate == 'physical' else result['canonical_momentum_rate']
    work = variation.time_work(rate, momentum_coordinate=coordinate)
    assert work['energy_direction'] == result['kinetic_energy_rate']
    assert work['boundary_flux_work'] != 0
    assert work['bed_gradient_work'] == 0
    assert not work['nonlinear_force_or_topology_change_or_gameplay_accepted']
    if coordinate == 'physical':
        assert work['momentum_work'] == result['momentum_work']
        assert work['depth_moment_work']+work['face_column_work']+work['boundary_flux_work'] == result['geometry_time_work']
    else:
        assert variation.gradients[coordinate]['momentum'] != result['layer_velocity']


def test_reused_and_fresh_solutions_match_without_reusing_a_solve(monkeypatch):
    boundary, m, result, reused = fixture()
    fresh = AffineFrontPressureVariation(boundary, m, P)
    assert fresh.gradients == reused.gradients
    def forbidden(*args):
        raise AssertionError('Solved-state path must not solve again')
    monkeypatch.setattr(m.solve_physical, 'solve', forbidden)
    for pole in m.poles:
        monkeypatch.setattr(pole['solver'], 'solve', forbidden)
    assert AffineFrontPressureVariation(boundary, m, P, solved_state=result).gradients == fresh.gradients


@pytest.mark.parametrize('part', ('canonical', 'auxiliary', 'weight', 'length', 'momentum'))
def test_reused_unknowns_require_exact_original_equations(part):
    boundary, m, result, _ = fixture()
    result = deepcopy(result)
    p, epsilon = P, F(1, 10**400)
    if part == 'canonical':
        result['canonical_velocity'] = ((result['canonical_velocity'][0][0]+epsilon, result['canonical_velocity'][0][1]),
                                        result['canonical_velocity'][1])
    elif part == 'auxiliary':
        a = result['poles'][0]['auxiliary_velocity']
        result['poles'][0]['auxiliary_velocity'] = ((a[0][0]+epsilon, a[0][1]), a[1])
    elif part in ('weight', 'length'):
        result['poles'][0][part] += epsilon
    else:
        p = ((P[0][0]+epsilon, P[0][1]), P[1])
    with pytest.raises(ValueError, match='original|reconstruction'):
        AffineFrontPressureVariation(boundary, m, p, solved_state=result)


def test_incompatible_trace_or_boundary_shift_is_rejected():
    boundary, m, result, _ = fixture()
    m.linear = tuple(x+F(1, 10**400) for x in m.linear)
    with pytest.raises(ValueError, match='Matching'):
        AffineFrontPressureVariation(boundary, m, P, solved_state=result)
    m.linear = boundary.linear
    m.poles[0]['boundary_shift'] = (m.zero,)*4
    with pytest.raises(ValueError, match='shift'):
        AffineFrontPressureVariation(boundary, m, P, solved_state=result)


def test_invalid_directions_and_coordinate_do_not_truncate_silently():
    boundary, m, result, variation = fixture()
    with pytest.raises(ValueError, match='coordinate'):
        variation.time_work(PT, momentum_coordinate='layer')
    g = boundary.geometry
    args = [PT, [g.forms[i]['depth_moment_rates'] for i in g.active],
            [f['column_normal_rate'] for f in g.faces], [(0, 0)]*2,
            [f['outward_mass_flux_rate'] for f in boundary.boundary_faces]]
    for index in range(5):
        changed = list(args)
        changed[index] = changed[index][:-1]
        with pytest.raises(ValueError):
            variation.work(*changed)


def test_dry_owners_have_no_fabricated_derivative_or_topology_force():
    fan = AffineDryFan((0, 0), (1, 0), 1, (0, 0), 0, (0, 0))
    boundary = FrontPrescribedTrace(fan, (rectangle(x0=4, x1=5),), F(1, 10), boundary='prescribed-fan-velocity')
    m = AffineMovingPressureMetric.from_trace(boundary)
    variation = AffineFrontPressureVariation(boundary, m, ())
    assert variation.time_work(())['energy_direction'] == 0
    assert variation.gradients['physical']['boundary_flux'] == ()
    direction = [(0, 0)]*len(boundary.geometry.faces)
    direction[0] = (F(1, 10**400), 0)
    with pytest.raises(ValueError, match='topology'):
        variation.work((), (), direction, (), ())


@pytest.mark.parametrize('reuse', (False, True))
def test_reflecting_only_derivative_rejects_affine_metric(reuse):
    boundary, m, result, _ = fixture()
    with pytest.raises(ValueError, match='AffineFrontPressureVariation'):
        FrontPressureVariation(boundary.geometry, m, P, solved_state=result if reuse else None)
