"""Full-velocity research controls; not terrain or time-evolution acceptance."""
import numpy as np
import pytest

from audit_rational_metric_transport_2d import compare, summarize
from finite_depth_pressure_reference import response
from rational_metric_transport_2d import stage
from rational_metric_transport_stage import stage as one_dimensional
from smooth_rational_velocity_stage import make


@pytest.fixture(scope='module')
def comparisons():
    return [compare(seed, n) for seed in (2310, 2312) for n in (16, 32, 64)]


def test_vortical_nonlinear_profiles_conserve_and_converge(comparisons):
    result = summarize(comparisons)
    assert result['conservation_passed']
    assert result['necessary_consistency_trend_passed']
    assert result['comparator_trend_passed']
    assert min(r['canonical_vorticity_rms'] for r in comparisons) > .1
    assert not result['nonlinear_model_or_terrain_or_dry_or_history_or_gameplay_accepted']


@pytest.mark.parametrize('shape', ((3, 4), (5, 7), (8, 8)))
def test_local_conservation_and_reconstructed_tensor_on_irregular_states(shape):
    rng = np.random.default_rng(2318)
    h = 1.+rng.random(shape)
    p = h[..., None]*rng.normal(size=(*shape, 2))*.3
    result = stage(make(h, np.zeros_like(h), .5), p)
    assert abs(result['energy_rate']) < 1e-10
    assert abs(result['net_mass_rate']) < 1e-10
    np.testing.assert_allclose(result['total_momentum_rate'], 0., atol=1e-10)
    assert result['local_momentum_flux_error'] < 1e-10
    assert result['metric_time_flux_error'] < 1e-10
    assert result['skew_flux_error'] < 1e-10
    assert result['reconstructed_derivative_error'] < 1e-12
    assert abs(result['skew_energy_work']) < 1e-10


@pytest.mark.parametrize('axis', (0, 1))
def test_existing_longitudinal_stage_is_recovered(axis):
    x = np.arange(24)*2*np.pi/24
    h, speed = (1.4+.2*np.sin(x))[None, :], (.7+.3*np.cos(x))[None, :]
    if axis == 0:
        h, speed = h.T, speed.T
    p = np.zeros((*h.shape, 2)); p[..., 1-axis] = h*speed
    g = make(h, np.zeros_like(h), .5)
    prior, full = one_dimensional(g, p), stage(g, p)
    for key in ('depth_rate', 'physical_momentum_rate', 'physical_acceleration'):
        np.testing.assert_allclose(full[key], prior[key], atol=1e-11, rtol=0)
    np.testing.assert_allclose(full['physical_momentum_faces'][1-axis], prior['physical_momentum_face'], atol=1e-11)


def test_axis_exchange_and_velocity_reversal():
    rng = np.random.default_rng(2320)
    h = 1.2+.3*rng.random((5, 7))
    p = h[..., None]*rng.normal(size=(5, 7, 2))*.2
    original = stage(make(h, np.zeros_like(h), .5), p)
    exchanged = stage(make(h.T, np.zeros_like(h.T), .5), p.transpose(1, 0, 2)[..., ::-1])
    reverse = stage(make(h, np.zeros_like(h), .5), -p)
    np.testing.assert_allclose(exchanged['depth_rate'], original['depth_rate'].T, atol=1e-12)
    np.testing.assert_allclose(exchanged['physical_momentum_rate'],
        original['physical_momentum_rate'].transpose(1, 0, 2)[..., ::-1], atol=1e-11)
    np.testing.assert_allclose(reverse['depth_rate'], -original['depth_rate'], atol=1e-12)
    np.testing.assert_allclose(reverse['physical_momentum_rate'], original['physical_momentum_rate'], atol=1e-11)


@pytest.mark.parametrize('component', (0, 1))
def test_steady_transverse_shear_is_not_damped(component):
    h = np.full((8, 8), 1.5)
    indices = np.indices(h.shape)
    p = np.zeros((*h.shape, 2))
    p[..., component] = h*.4*np.sin(indices[component]*2*np.pi/8)
    result = stage(make(h, np.zeros_like(h), .5), p)
    np.testing.assert_allclose(result['depth_rate'], 0., atol=1e-12)
    np.testing.assert_allclose(result['physical_momentum_rate'], 0., atol=1e-11)


def test_oblique_linear_wave_retains_mass_pressure_and_transverse_null_mode():
    ny, nx = 12, 16; dx = .5; depth = 1.5; eps = 1e-5
    y, x = np.indices((ny, nx))
    phase = 2*np.pi*(2*x/nx+y/ny)
    wave, mode = np.sin(phase), np.cos(phase)
    k = np.array([np.sin(4*np.pi/nx), np.sin(2*np.pi/ny)])/dx
    norm = np.linalg.norm(k)
    direction = k/norm
    perpendicular = np.array([-direction[1], direction[0]])
    pressure, mass, transverse = [], [], []
    for sign in (-1, 1):
        h = depth+sign*eps*wave
        pressure.append(stage(make(h, np.zeros_like(h), dx), np.zeros((*h.shape, 2)))['physical_momentum_rate'])
        h = np.full_like(wave, depth)
        g = make(h, np.zeros_like(h), dx)
        mass.append(stage(g, h[..., None]*sign*eps*wave[..., None]*direction)['depth_rate'])
        transverse.append(stage(g, h[..., None]*sign*eps*wave[..., None]*perpendicular))
    measured = np.sum((pressure[1]-pressure[0])/(2*eps)*mode[..., None], axis=(0, 1))/np.sum(mode*mode)
    np.testing.assert_allclose(measured, -9.81*depth*k*response(depth*norm), atol=1e-7, rtol=0)
    measured = np.sum((mass[1]-mass[0])/(2*eps)*mode)/np.sum(mode*mode)
    assert abs(measured+depth*norm) < 1e-7
    for key in ('depth_rate', 'physical_momentum_rate'):
        np.testing.assert_allclose((transverse[1][key]-transverse[0][key])/(2*eps), 0., atol=1e-7)


def test_variable_bed_and_unknown_tensor_rejected():
    h = np.ones((3, 4)); p = np.zeros((3, 4, 2))
    with pytest.raises(ValueError, match='Unknown'):
        stage(make(h, np.zeros_like(h), 1.), p, tensor_coupling='unqualified')
    b = np.zeros_like(h); b[0, 0] = .1
    with pytest.raises(ValueError, match='Flat'):
        stage(make(h, b, 1.), p)
    with pytest.raises(ValueError, match='Complete'):
        summarize([])
