"""Terrain research gates; no local force, finite history or scene acceptance."""
import numpy as np
import pytest

from patch_pressure_preconditioner import PatchPressureSystem
from rational_primal_energy import BETAS
from reconstructed_acceleration_system import ReconstructedAccelerationSystem
from rational_terrain_metric_transport import PhysicalFactors, stage, tensor_action
from smooth_pressure_geometry import SmoothPressureGeometryRate
from smooth_rational_velocity_stage import make
import terrain_metric_force_ledger as ledger


def fixture(shape=(5, 7)):
    rng = np.random.default_rng(2405)
    h = 1.4+.2*rng.random(shape)
    bed = .1*rng.normal(size=shape)
    p = h[..., None]*.3*rng.normal(size=(*shape, 2))
    return rng, make(h, bed, .5), p


@pytest.mark.parametrize('bottom', (False, True))
def test_actual_factor_time_and_transpose_pairing(bottom):
    rng, g, p = fixture()
    ht = .2*rng.normal(size=g.h.shape)
    tangent = SmoothPressureGeometryRate(g, g.bed, ht)
    f = PhysicalFactors(PatchPressureSystem(g, BETAS[0]), tangent)
    u = p/g.h[..., None]
    scalar = rng.normal(size=g.h.shape)
    assert abs(np.sum(scalar*f.action(u, bottom=bottom))
               -np.sum(u*f.transpose(scalar, bottom=bottom))) < 1e-11
    assert abs(np.sum(scalar*f.rate(u, bottom=bottom))
               -np.sum(u*f.transpose_rate(scalar, bottom=bottom))) < 1e-11
    samples = []
    for sign in (-1, 1):
        gs = make(g.h+sign*1e-5*ht, g.bed, g.dx)
        fs = PhysicalFactors(PatchPressureSystem(gs, BETAS[0]), SmoothPressureGeometryRate(gs, gs.bed, ht))
        samples.append((fs.action(u, bottom=bottom), fs.transpose(scalar, bottom=bottom)))
    np.testing.assert_allclose((samples[1][0]-samples[0][0])/2e-5,
                               f.rate(u, bottom=bottom), atol=2e-9, rtol=0)
    np.testing.assert_allclose((samples[1][1]-samples[0][1])/2e-5,
                               f.transpose_rate(scalar, bottom=bottom), atol=2e-9, rtol=0)


def test_tensor_self_adjoint_and_geometric_commutator_skew():
    rng, g, p = fixture()
    ht = .2*rng.normal(size=g.h.shape)
    f = PhysicalFactors(PatchPressureSystem(g, BETAS[0]), SmoothPressureGeometryRate(g, g.bed, ht))
    u, v = p/g.h[..., None], rng.normal(size=p.shape)
    c, s = rng.normal(size=g.h.shape), rng.normal(size=g.h.shape)
    assert abs(np.sum(u*tensor_action(g, c, s, v))-np.sum(v*tensor_action(g, c, s, u))) < 1e-11
    assert abs(np.sum(u*f.commutator(v))+np.sum(v*f.commutator(u))) < 1e-11
    assert np.max(abs(f.commutator(u))) > 1e-4
    assert np.max(abs(tensor_action(g, c, s, np.ones_like(u)))) > 1e-4


@pytest.mark.parametrize('shape', ((3, 4), (5, 7), (8, 8)))
@pytest.mark.parametrize('coupling', ('full', 'no-commutator', 'no-hessian'))
def test_mass_and_energy_are_necessary_but_not_model_acceptance(shape, coupling):
    _, g, p = fixture(shape)
    result = stage(g, p, coupling=coupling)
    for key in ('net_mass_rate', 'energy_rate', 'skew_energy_work',
                'commutator_energy_work', 'gravity_mass_work_error',
                'local_momentum_ledger_error', 'metric_time_ledger_error', 'skew_ledger_error'):
        assert abs(result[key]) < 1e-10, key
    assert result['maximum_solve_residual'] < 2e-5
    assert not result['local_physical_bed_force_ledger_accepted']
    assert not result['nonlinear_model_or_dry_or_history_or_gameplay_accepted']
    np.testing.assert_allclose(result['total_momentum_rate'],
                               result['physical_bed_force'].sum(axis=(0, 1))*g.dx**2, atol=1e-10)


def test_nonflat_lake_at_rest():
    _, original, p = fixture()
    g = make(2.-original.bed, original.bed, original.dx)
    result = stage(g, np.zeros_like(p))
    np.testing.assert_allclose(result['depth_rate'], 0., atol=1e-12)
    np.testing.assert_allclose(result['physical_momentum_rate'], 0., atol=1e-11)


def test_axis_exchange_velocity_reversal_and_bed_datum():
    _, g, p = fixture()
    original = stage(g, p)
    exchange = stage(make(g.h.T, g.bed.T, g.dx), p.transpose(1, 0, 2)[..., ::-1])
    reverse = stage(g, -p)
    translated = stage(make(g.h, g.bed+100., g.dx), p)
    np.testing.assert_allclose(exchange['depth_rate'], original['depth_rate'].T, atol=1e-11)
    np.testing.assert_allclose(exchange['physical_momentum_rate'],
                               original['physical_momentum_rate'].transpose(1, 0, 2)[..., ::-1], atol=1e-11)
    np.testing.assert_allclose(reverse['depth_rate'], -original['depth_rate'], atol=1e-11)
    np.testing.assert_allclose(reverse['physical_momentum_rate'], original['physical_momentum_rate'], atol=1e-11)
    np.testing.assert_allclose(translated['physical_momentum_rate'], original['physical_momentum_rate'], atol=1e-10)


def test_invalid_input_rejected():
    _, g, p = fixture()
    with pytest.raises(ValueError, match='Unknown'):
        stage(g, p, coupling='independent-modes')
    with pytest.raises(ValueError, match='Finite'):
        stage(g, np.zeros_like(g.h))
    with pytest.raises(ValueError, match='Finite'):
        stage(g, np.full_like(p, np.nan))
    with pytest.raises(ValueError, match='Smooth'):
        stage(None, p)


def test_flat_physical_momentum_has_no_bed_source():
    _, original, p = fixture()
    g = make(original.h, np.zeros_like(original.bed), original.dx)
    result = stage(g, p)
    np.testing.assert_allclose(result['physical_bed_force'], 0., atol=1e-11)
    np.testing.assert_allclose(result['total_momentum_rate'], 0., atol=1e-11)
    assert result['local_momentum_ledger_error'] < 1e-10


@pytest.mark.parametrize('length', (.01, .1, .7))
def test_frozen_reference_is_spd_and_solves_original_terrain_matrix(length):
    rng, g, _ = fixture((3, 4))
    system = ReconstructedAccelerationSystem(g, length)
    shape, size = (*g.h.shape, 2), 2*g.h.size
    identity = np.eye(size)
    dense = np.column_stack([system.apply(column.reshape(shape)).ravel() for column in identity])
    before = dense.copy()
    preconditioner = np.column_stack([system.precondition(column.reshape(shape), 'spectral-frozen-depth').ravel()
                                     for column in identity])
    np.testing.assert_allclose(preconditioner, preconditioner.T, atol=1e-12)
    assert np.linalg.eigvalsh(preconditioner).min() > 0
    rhs = rng.normal(size=shape)
    solved, stats = system.solve(rhs, iterations=40, preconditioner='spectral-frozen-depth')
    np.testing.assert_allclose(solved.ravel(), np.linalg.solve(dense, rhs.ravel()), atol=1e-11)
    assert stats['iterations'] <= 40
    assert stats['relative_residual'] < 2e-5
    after = np.column_stack([system.apply(column.reshape(shape)).ravel() for column in identity])
    np.testing.assert_array_equal(before, after)
    with pytest.raises(ValueError, match='flat'):
        system.precondition(rhs, 'spectral-flat')


def test_preconditioners_agree_on_full_terrain_force():
    _, g, p = fixture()
    patch = stage(g, p, preconditioner='patch')
    frozen = stage(g, p)
    np.testing.assert_allclose(patch['physical_momentum_rate'], frozen['physical_momentum_rate'], atol=1e-11)
    np.testing.assert_allclose(patch['physical_bed_force'], frozen['physical_bed_force'], atol=1e-11)


def test_local_traction_and_changing_coefficients_match_independent_operator():
    rng, g, _ = fixture()
    pressure, bottom, ht = rng.normal(size=(3, *g.h.shape))
    tangent = SmoothPressureGeometryRate(g, g.bed, ht)
    np.testing.assert_allclose(ledger.traction(g, pressure, bottom).action(g.dx),
                               g.gradient_traction(pressure, bottom), atol=1e-12)
    np.testing.assert_allclose(ledger.traction(g, pressure, bottom, tangent=tangent).action(g.dx),
                               tangent.force_operator_rate(pressure, bottom), atol=1e-12)
    f = PhysicalFactors(PatchPressureSystem(g, BETAS[0]), tangent)
    for is_bottom in (False, True):
        np.testing.assert_allclose(ledger.factor_transpose(g, pressure, bottom=is_bottom).action(g.dx),
                                   f.transpose(pressure, bottom=is_bottom), atol=1e-12)
        np.testing.assert_allclose(ledger.factor_transpose(g, pressure, bottom=is_bottom, tangent=tangent).action(g.dx),
                                   f.transpose_rate(pressure, bottom=is_bottom), atol=1e-12)


def test_original_oblique_linear_response_and_transverse_null():
    from finite_depth_pressure_reference import response
    ny, nx, dx, depth, eps = 8, 12, .5, 1.5, 1e-5
    y, x = np.indices((ny, nx))
    phase = 2*np.pi*(2*x/nx+y/ny)
    wave, mode = np.sin(phase), np.cos(phase)
    k = np.array([np.sin(4*np.pi/nx), np.sin(2*np.pi/ny)])/dx
    norm = np.linalg.norm(k)
    normal, transverse = k/norm, np.array([-k[1], k[0]])/norm
    pressure, mass, null = [], [], []
    for sign in (-1, 1):
        h = depth+sign*eps*wave
        pressure.append(stage(make(h, np.zeros_like(h), dx), np.zeros((*h.shape, 2)))['physical_momentum_rate'])
        h = np.full_like(wave, depth)
        g = make(h, np.zeros_like(h), dx)
        mass.append(stage(g, h[..., None]*sign*eps*wave[..., None]*normal)['depth_rate'])
        null.append(stage(g, h[..., None]*sign*eps*wave[..., None]*transverse))
    measured = np.sum((pressure[1]-pressure[0])/(2*eps)*mode[..., None], axis=(0, 1))/np.sum(mode*mode)
    np.testing.assert_allclose(measured, -9.81*depth*k*response(depth*norm), atol=1e-7, rtol=0)
    measured = np.sum((mass[1]-mass[0])/(2*eps)*mode)/np.sum(mode*mode)
    assert abs(measured+depth*norm) < 1e-7
    for key in ('depth_rate', 'physical_momentum_rate'):
        np.testing.assert_allclose((null[1][key]-null[0][key])/(2*eps), 0., atol=1e-7)


def test_full_turning_terrain_reference_refines_without_energy_shortcut():
    from audit_rational_terrain_metric_transport import compare
    rows = [compare(2401, n) for n in (8, 16, 32)]
    errors = [row['potential_rms']['full'] for row in rows]
    assert all(errors[i]/errors[i+1] > 3 for i in (0, 1))
    assert all(row['canonical_vorticity_rms'] > .08 for row in rows)
    for row in rows:
        assert max(abs(value) for value in row['energy_rates'].values()) < 1e-10
        assert row['local_momentum_ledger_error'] < 1e-10
        assert row['maximum_roundtrip_error'] < 1e-10
        assert not row['nonlinear_model_or_dry_or_history_or_gameplay_accepted']
    # Conservation cannot discriminate this incomplete model; its persistent
    # force discrepancy already exceeds the full model's truncation error.
    assert rows[-1]['omitted_term_rms']['no-commutator'] > errors[-1]
    assert rows[-1]['potential_rms']['no-commutator'] > errors[-1]
