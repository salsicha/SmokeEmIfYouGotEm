import numpy as np
import pytest

from finite_depth_pressure_reference import LENGTHS, WEIGHTS, response
from subcell_geometry_patch import SubcellGeometryPatch
from subcell_wet_pool_partition import WetPoolPartition
from subcell_gravity_wave_stage import GravityWaveStage
from subcell_wet_pool_primal_energy import evaluate
from test_triangle_face_section import sampler


def lake(height=lambda x, y: .2*x+.1*y, stages=.73, shape=(2, 2), spacing=(.5, .5),
         origin=(-.25, -.25), periodic=(False, False), exact=True):
    source = sampler(height)
    patch = SubcellGeometryPatch(source, origin, shape, spacing, periodic,
                                relative_stages=True, exact_sources=exact)
    v, p = patch.state_from_stages(stages, [0., 0.])
    return WetPoolPartition(patch, source, origin, v, p)


@pytest.mark.parametrize('exact', [False, True])
def test_transport_is_conservative_and_its_true_adjoint_cancels_pressure_work(exact):
    s = GravityWaveStage(lake(exact=exact))
    rng = np.random.default_rng(2750)
    a, p = rng.normal(size=len(s.volume))*.001, rng.normal(size=(len(s.volume), 2))*.001
    np.testing.assert_allclose(np.dot(a, s.transport(p)), np.sum(p*s.transport_transpose(a)), atol=1e-14)
    assert abs(s.transport(p).sum()) < 1e-14
    adot, pdot = s.rates(a, p)
    canonical = evaluate(s.partition, p[:, None, :])['canonical_velocity'][:, 0]
    assert abs(np.dot(s.hessian*a, adot)+np.sum(canonical*pdot)) < 1e-12
    assert max(s.residuals) < 2e-5


@pytest.mark.parametrize('mode', [(1, 0), (1, 1)])
def test_original_two_pole_wave_frequency_on_flat_periodic_terrain(mode):
    n, dx, depth = 4, .4, 1.5
    s = GravityWaveStage(lake(lambda x, y: 0*x, depth, (n, n), (dx, dx), (-.6, -.6), (True, True)))
    y, x = np.indices((n, n))
    phase = 2*np.pi*(mode[0]*x+mode[1]*y)/n
    k = np.sin(2*np.pi*np.array(mode)/n)/dx
    a = (.001*dx**2*np.cos(phase)).ravel()
    adot, pdot = s.rates(a, np.zeros((n*n, 2)))
    np.testing.assert_array_equal(adot, 0.)
    omega2 = 9.81*depth*np.dot(k, k)*response(depth*np.linalg.norm(k))
    np.testing.assert_allclose(s.transport(pdot), -omega2*a, atol=2e-13, rtol=0)
    expected_pdot = (.001*depth*dx**2*9.81*response(depth*np.linalg.norm(k))
                     *np.sin(phase)[..., None]*k).reshape(-1, 2)
    np.testing.assert_allclose(pdot, expected_pdot, atol=2e-13, rtol=0)


def test_closed_disconnected_pools_cannot_exchange_water_or_pressure_waves():
    s = GravityWaveStage(lake(lambda x, y: 1-abs(x), .37, (1, 1), (2., 2.), (0., 0.)))
    assert len(s.volume) == 2
    adot, pdot = s.rates(np.array([.001, 0.]), np.array([[.002, -.001], [0., 0.]]))
    np.testing.assert_array_equal(adot, 0.)
    np.testing.assert_array_equal(pdot, 0.)


def dense_matrices(s):
    """Independent dense Gram and face assembly, only a small-test oracle."""
    n = len(s.volume)
    b = np.zeros((n, 2*n))
    for left, right, weight in s.faces:
        for owner in (left, right):
            b[left, 2*owner:2*owner+2] -= weight/s.volume[owner]
            b[right, 2*owner:2*owner+2] += weight/s.volume[owner]
    system = s.systems[0]
    q = np.zeros((2*n, 2*n))
    for index, pool in enumerate(s.partition.pools):
        jet = np.zeros((3, 2*n))
        for col, value in system.row_maps[index].items():
            jet[0, col] = value/s.root[col//2]
        jet[1, 2*index] = jet[2, 2*index+1] = 1/s.root[index]
        q += jet.T@pool['form']['gram']@jet
    eye = np.eye(2*n)
    inverse = (1-float(sum(WEIGHTS)))*eye
    for length, weight in zip(LENGTHS, WEIGHTS):
        inverse += weight*np.linalg.solve(eye+length*q, eye)
    root = np.repeat(s.root, 2)
    m = root[:, None]*inverse*root[None, :]
    generator = np.block([[np.zeros((n, n)), b], [-m@b.T@np.diag(s.hessian), np.zeros((2*n, 2*n))]])
    return b, m, generator


def test_terrain_midpoint_matches_independent_coupled_system_and_conserves_energy():
    s = GravityWaveStage(lake())
    b, m, generator = dense_matrices(s)
    rng = np.random.default_rng(2751)
    a, p = rng.normal(size=len(s.volume))*.001, rng.normal(size=(len(s.volume), 2))*.001
    dt = .12
    original = np.r_[a, p.ravel()]
    identity = np.eye(len(original))
    expected = np.linalg.solve(identity-.5*dt*generator, (identity+.5*dt*generator)@original)
    result = s.midpoint(a, p, dt)
    np.testing.assert_allclose(result['volume_perturbation'], expected[:len(a)], atol=2e-13, rtol=0)
    np.testing.assert_allclose(result['physical_momentum'].ravel(), expected[len(a):], atol=2e-13, rtol=0)
    energy = .5*p.ravel()@np.linalg.solve(m, p.ravel())+.5*np.dot(s.hessian*a, a)
    np.testing.assert_allclose(result['energy_before'], energy, atol=2e-13, rtol=0)
    assert abs(result['energy_change']) < 1e-12
    assert result['mass_error'] < 1e-12
    assert result['equation_error'] < 1e-12
    assert result['schur_solve']['iterations'] <= 40
    assert not result['nonlinear_or_topology_or_native_or_gameplay_accepted']


def test_finite_linear_wave_phase_refines_without_changing_physical_horizon():
    n, dx, depth, horizon = 4, .4, 1.5, .2
    s = GravityWaveStage(lake(lambda x, y: 0*x, depth, (1, n), (dx, dx), (-.6, 0.), (True, True)))
    phase = 2*np.pi*np.arange(n)/n
    original_a = .001*dx**2*np.cos(phase)
    k = np.sin(2*np.pi/n)/dx
    omega = np.sqrt(9.81*depth*k*k*response(depth*k))
    expected_a = original_a*np.cos(omega*horizon)
    _, initial_pdot = s.rates(original_a, np.zeros((n, 2)))
    expected_p = initial_pdot*np.sin(omega*horizon)/omega
    errors = []
    for steps in (2, 4, 8):
        a, p = original_a.copy(), np.zeros((n, 2))
        initial_energy = s.energy(a, p)
        for _ in range(steps):
            result = s.midpoint(a, p, horizon/steps)
            a, p = result['volume_perturbation'], result['physical_momentum']
        assert abs(s.energy(a, p)-initial_energy) < 1e-12
        errors.append(max(np.max(abs(a-expected_a)), np.max(abs(p-expected_p))))
    assert all(3.8 < x/y < 4.2 for x, y in zip(errors, errors[1:]))


def test_moving_or_non_equilibrium_reference_is_not_silently_linearized_as_lake():
    pools = lake()
    moving = pools.with_regions([dict(p, momentum=np.array([.1, 0.])) for p in pools.pools])
    with pytest.raises(ValueError, match='lake at rest'):
        GravityWaveStage(moving)
    with pytest.raises(ValueError, match='hydrostatic balance'):
        GravityWaveStage(lake(lambda x, y: 0*x, [[.7, .9], [.7, .9]]))


def test_midpoint_rejects_negative_water_instead_of_clipping_linear_perturbation():
    s = GravityWaveStage(lake())
    with pytest.raises(ValueError, match='positive finite volume'):
        s.midpoint(-2*s.volume, np.zeros((len(s.volume), 2)), .02)


def test_oblique_internal_source_faces_use_same_transport_pressure_pair():
    pools = lake(shape=(1, 1), spacing=(.5, .5), origin=(0., 0.))
    cell = pools.patch.cells[0]
    form = pools.pools[0]['form']
    volumes, _ = cell._triangle_volume_and_wet_area(form['stage_offset'], cell.relative_levels)
    states = [dict(parent=0, source_triangle_indices=[int(source)],
                   volume=float(volumes[cell.source_triangle_indices == source].sum()), momentum=np.zeros(2))
              for source in sorted(set(cell.source_triangle_indices))]
    separated = pools.with_regions(states)
    s = GravityWaveStage(separated)
    assert any(f['axis'] is None and np.count_nonzero(f['normal']) == 2 for f in s.systems[0].connections)
    b, m, _ = dense_matrices(s)
    rng = np.random.default_rng(2753)
    a, p = rng.normal(size=len(s.volume))*1e-5, rng.normal(size=(len(s.volume), 2))*1e-5
    adot, pdot = s.rates(a, p)
    np.testing.assert_allclose(adot, b@p.ravel(), atol=1e-14)
    np.testing.assert_allclose(pdot.ravel(), -m@b.T@(s.hessian*a), atol=1e-14)
    result = s.midpoint(a, p, .02)
    assert abs(result['energy_change']) < 1e-12


def test_flat_pressure_wave_matches_linearization_of_full_two_dimensional_stage():
    from rational_metric_transport_2d import stage
    from smooth_rational_velocity_stage import make
    n, dx, depth = 4, .4, 1.5
    s = GravityWaveStage(lake(lambda x, y: 0*x, depth, (n, n), (dx, dx), (-.6, -.6), (True, True)))
    y, x = np.indices((n, n))
    shape = np.cos(2*np.pi*x/n)+.3*np.sin(2*np.pi*y/n)
    errors = []
    for amplitude in (.002, .001, .0005):
        h = depth+amplitude*shape
        full = stage(make(h, np.zeros_like(h), dx), np.zeros((n, n, 2)))
        _, linear = s.rates((amplitude*dx**2*shape).ravel(), np.zeros((n*n, 2)))
        errors.append(np.max(abs(full['physical_momentum_rate'].reshape(-1, 2)*dx**2-linear)))
    assert all(3.8 < x/y < 4.2 for x, y in zip(errors, errors[1:]))


def test_constant_stage_shift_has_independent_hydrostatic_bed_and_wall_reactions():
    s = GravityWaveStage(lake())
    potential = np.full(len(s.volume), .02)
    ledger = s.pressure_force(potential)
    np.testing.assert_allclose(ledger['physical_momentum_rate'], 0., atol=1e-14)
    assert np.max(abs(ledger['bed_force'])) > 0
    assert np.max(abs(ledger['wall_force'])) > 0
    for index, pool in enumerate(s.partition.pools):
        storage, h = pool['storage'], pool['form']['stage_offset']
        eps = 1e-4
        delta = eps*potential[index]/s.gravity
        expected = (storage.hydrostatic_bed_force(h+delta, s.gravity, True)
                    -storage.hydrostatic_bed_force(h-delta, s.gravity, True))/(2*eps)
        np.testing.assert_allclose(ledger['bed_force'][index], expected, atol=1e-11, rtol=0)


def test_flat_periodic_pressure_has_no_invented_bed_or_wall_force():
    s = GravityWaveStage(lake(lambda x, y: 0*x, 1.5, (2, 4), (.4, .4), (-.6, -.2), (True, True)))
    ledger = s.pressure_force(np.arange(len(s.volume))*.001)
    np.testing.assert_array_equal(ledger['bed_force'], 0.)
    np.testing.assert_array_equal(ledger['wall_force'], 0.)
    np.testing.assert_allclose(ledger['physical_momentum_rate'].sum(axis=0), 0., atol=1e-14)
