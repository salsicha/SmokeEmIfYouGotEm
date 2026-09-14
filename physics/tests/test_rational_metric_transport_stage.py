"""Research-stage controls do not qualify wet fronts, time or gameplay."""
import numpy as np
import pytest

from audit_rational_metric_transport import compare, summarize
from finite_depth_pressure_reference import response
from rational_metric_transport_stage import stage
from smooth_rational_velocity_stage import make


@pytest.fixture(scope='module')
def comparisons():
    return [compare(seed, n) for seed in (2200, 2202, 2204, 2206) for n in (32, 64, 128)]


def test_original_profiles_conserve_energy_mass_and_local_momentum(comparisons):
    assert all(r['conservation_passed'] and r['local_flux_passed'] for r in comparisons)
    assert max(r['maximum_solve_residual'] for r in comparisons) < 2e-5


def test_nonlinear_rate_converges_to_independent_potential_control(comparisons):
    summary = summarize(comparisons)
    assert summary['necessary_consistency_trend_passed']
    assert summary['comparator_trend_passed']
    # The independently transported negative control still conserves totals,
    # but is not the intended nonlinear model. Never replace this rate gate
    # with the conservation gate or an area-integrated shrinking-width error.
    assert all(c['independent_refinement_ratios'][-1] < 1.1 for c in summary['controls'])
    assert not summary['nonlinear_model_or_local_flux_or_dry_or_history_or_gameplay_accepted']


@pytest.mark.parametrize('axis', (0, 1))
@pytest.mark.parametrize('speed', (-.5, .5))
def test_constant_physical_velocity(axis, speed):
    h = np.array([[1., 2., 4.]])
    if axis == 0:
        h = h.T
    p = np.zeros((*h.shape, 2)); p[..., 1-axis] = h*speed
    r = stage(make(h, np.zeros_like(h), .5), p)
    assert abs(r['energy_rate']) < 1e-10
    assert r['local_momentum_flux_error'] < 1e-10
    np.testing.assert_allclose(r['total_momentum_rate'], 0, atol=1e-10)


@pytest.mark.parametrize('axis', (0, 1))
def test_original_finite_kh_linear_mass_and_pressure(axis):
    n = 32; dx = .25; depth = 1.5; eps = 1e-5
    phase = 2*np.pi*2*np.arange(n)/n
    wave, mode = np.sin(phase)[None, :], np.cos(phase)[None, :]
    if axis == 0:
        wave, mode = wave.T, mode.T
    pressure, mass = [], []
    for sign in (-1, 1):
        h = depth+sign*eps*wave
        r = stage(make(h, np.zeros_like(h), dx), np.zeros((*h.shape, 2)))
        pressure.append(r['physical_momentum_rate'][..., 1-axis])
        h = np.full_like(wave, depth)
        p = np.zeros((*h.shape, 2)); p[..., 1-axis] = h*sign*eps*wave
        r = stage(make(h, np.zeros_like(h), dx), p)
        mass.append(r['depth_rate'])
    k = np.sin(2*np.pi*2/n)/dx
    project = lambda values: np.sum((values[1]-values[0])/(2*eps)*mode)/np.sum(mode*mode)
    assert abs(project(pressure)+9.81*depth*k*response(depth*k)) < 1e-7
    assert abs(project(mass)+depth*k) < 1e-7


@pytest.mark.parametrize('axis', (0, 1))
def test_velocity_reversal_and_local_face_ownership(axis):
    x = np.arange(16)*2*np.pi/16
    h = (1.4+.2*np.sin(x))[None, :]
    velocity = (.7+.3*np.cos(x))[None, :]
    if axis == 0:
        h, velocity = h.T, velocity.T
    p = np.zeros((*h.shape, 2)); p[..., 1-axis] = h*velocity
    g = make(h, np.zeros_like(h), .5)
    forward, reverse = stage(g, p), stage(g, -p)
    np.testing.assert_allclose(forward['depth_rate'], -reverse['depth_rate'], atol=1e-12)
    np.testing.assert_allclose(forward['physical_momentum_rate'], reverse['physical_momentum_rate'], atol=1e-12)
    face = forward['physical_momentum_face']
    flux_rate = -(face-np.roll(face, 1, axis))/.5
    np.testing.assert_allclose(flux_rate, forward['physical_momentum_rate'], atol=1e-10, rtol=0)
    assert forward['metric_time_flux_error'] < 1e-10
    assert forward['skew_flux_error'] < 1e-10


def test_reject_unsupported_scope_and_unknown_coupling():
    h = np.ones((1, 4)); p = np.zeros((1, 4, 2))
    with pytest.raises(ValueError, match='Unknown'):
        stage(make(h, np.zeros_like(h), 1.), p, auxiliary_transport='unqualified')
    with pytest.raises(ValueError, match='Flat'):
        stage(make(h, np.array([[0., .1, 0., 0.]]), 1.), p)
    with pytest.raises(ValueError, match='Flat'):
        stage(make(np.ones((2, 2)), np.zeros((2, 2)), 1.), p)
    p[..., 1] = 1.
    with pytest.raises(ValueError, match='transverse'):
        stage(make(h, np.zeros_like(h), 1.), p)


def test_summary_rejects_missing_original_profile():
    with pytest.raises(ValueError, match='Complete'):
        summarize([])


@pytest.mark.parametrize('axis', (0, 1))
def test_galilean_boost_rate_defect_converges_without_shrinking_width(axis):
    from audit_reconstructed_closed_energy import fixture
    errors = []
    for n in (32, 64, 128):
        source, bed = fixture(2200, 'smooth', n)
        h, velocity = source[..., 0], source[..., 1]/source[..., 0]
        if axis == 0:
            h, velocity, bed = h.T, velocity.T, bed.T
        p = np.zeros((*h.shape, 2)); p[..., 1-axis] = h*velocity
        g = make(h, bed, 16/n)
        boost = 1.2
        boosted = p.copy(); boosted[..., 1-axis] += h*boost
        original, shifted = stage(g, p), stage(g, boosted)
        derivative = lambda f: (np.roll(f, -1, axis)-np.roll(f, 1, axis))/(2*g.dx)
        expected = (original['physical_momentum_rate'][..., 1-axis]
            +boost*original['depth_rate']-boost*derivative(p[..., 1-axis])
            -boost*boost*derivative(h))
        np.testing.assert_allclose(shifted['depth_rate'],
            original['depth_rate']-boost*derivative(h), atol=1e-12, rtol=0)
        errors.append(float(np.sqrt(np.mean((shifted['physical_momentum_rate'][..., 1-axis]-expected)**2))))
    assert all(errors[i]/errors[i+1] > 3 for i in (0, 1))
