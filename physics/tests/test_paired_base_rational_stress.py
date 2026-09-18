"""Retained failed base stress and repaired default on the SAME two-pole states."""
import numpy as np
import pytest
from conservative_rational_stress import stress_stage, stress_stage_physical, negative_divergence
from smooth_rational_velocity_stage import make
from finite_depth_pressure_reference import response


@pytest.mark.parametrize('axis,sign', ((0,-1),(0,1),(1,-1),(1,1)))
def test_constant_physical_velocity_base_energy_obstruction_is_removed(axis, sign):
    h = np.array([[1., 2., 4.]])
    if axis == 0:
        h = h.T
    u = np.zeros((*h.shape, 2));u[..., 1-axis] = sign*.5
    g = make(h, np.zeros_like(h), .5)
    legacy = stress_stage_physical(g, h[..., None]*u, flux_scheme='donor-stress')
    paired = stress_stage_physical(g, h[..., None]*u, flux_scheme='paired-base')
    assert abs(legacy['energy_rate']) > 13
    assert abs(paired['energy_rate']) < 1e-10
    assert abs(paired['physical_momentum_rate'].sum(axis=(0, 1))).max() < 1e-10
    assert not paired['energy_or_variable_bed_or_dry_or_history_or_gameplay_accepted']


@pytest.mark.parametrize('shape', ((1, 7), (7, 1), (3, 4), (2, 11)))
def test_paired_flux_keeps_local_physical_momentum_and_mass(shape):
    rng = np.random.default_rng(9715)
    h = 1+rng.random(shape);v = .2*rng.normal(size=(*shape, 2))
    r = stress_stage(make(h, np.zeros_like(h), .5), v, flux_scheme='paired-base')
    assert r['auxiliary_momentum_identity_error'] < 1e-10
    assert r['local_momentum_flux_error'] < 1e-10
    np.testing.assert_allclose(negative_divergence(r['physical_momentum_fluxes'], .5),
                               r['physical_momentum_rate'], atol=1e-10, rtol=0)
    np.testing.assert_allclose(r['physical_momentum_rate'].sum(axis=(0, 1)), 0., atol=1e-10)
    assert abs(r['depth_rate'].sum()) < 1e-10
    assert np.min(h+.9*r['mass_only_forward_euler_bound']*r['depth_rate']) >= 0
    assert r['energy_coordinate_error'] < 1e-10
    assert r['energy_work_split_error'] < 1e-10
    assert not r['incremental_work_is_donor']
    assert r['donor_incremental_energy_rate'] is None


@pytest.mark.parametrize('axis', (0, 1))
def test_original_two_pole_linear_pressure_and_mass_response_retained(axis):
    n = 32;dx = .25;depth = 1.5;theta = 2*np.pi*2*np.arange(n)/n
    mode = np.cos(theta)[None, :];wave = np.sin(theta)[None, :]
    if axis == 0:
        mode, wave = mode.T, wave.T
    eps = 1e-5;pressure_rates = [];mass_rates = []
    for sign in (-1, 1):
        h = depth+sign*eps*wave
        r = stress_stage(make(h, np.zeros_like(h), dx), np.zeros((*h.shape, 2)), flux_scheme='paired-base')
        pressure_rates.append(r['physical_momentum_rate'][..., 1-axis])
        h = np.full_like(wave, depth);u = np.zeros((*h.shape, 2));u[..., 1-axis] = sign*eps*wave
        r = stress_stage_physical(make(h, np.zeros_like(h), dx), h[..., None]*u, flux_scheme='paired-base')
        mass_rates.append(r['depth_rate'])
    k = np.sin(2*np.pi*2/n)/dx
    measured = np.sum((pressure_rates[1]-pressure_rates[0])/(2*eps)*mode)/np.sum(mode*mode)
    assert abs(measured+9.81*depth*k*response(depth*k)) < 1e-7
    measured = np.sum((mass_rates[1]-mass_rates[0])/(2*eps)*mode)/np.sum(mode*mode)
    assert abs(measured+depth*k) < 1e-7


def test_unknown_pairing_is_not_silently_selected():
    g = make(np.ones((1, 3)), np.zeros((1, 3)), .5)
    with pytest.raises(ValueError, match='Unknown'):
        stress_stage(g, np.zeros((1, 3, 2)), flux_scheme='invented')


@pytest.mark.parametrize('resolution', (64, 128))
@pytest.mark.parametrize('seed', (2200, 2202, 2204, 2206))
def test_full_nonlinear_energy_conservation_still_required(seed, resolution):
    # The default now uses coupled metric transport, not the old paired stress.
    # Keep its failure visible as a negative control on the same original data.
    from audit_conservative_rational_stress import run
    legacy = run(seed, resolution, 'primal', 'paired-base')
    assert abs(legacy['energy_rate']) > 1e-10
    r = run(seed, resolution, 'primal')
    assert r['flux_scheme'] == 'metric-transport'
    assert r['source_state_sha256'] == legacy['source_state_sha256']
    assert abs(r['energy_rate']) < 1e-10
    assert r['local_momentum_flux_error'] < 1e-10
    assert max(map(abs, r['physical_total_momentum_rate'])) < 1e-10
