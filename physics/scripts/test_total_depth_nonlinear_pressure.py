import numpy as np
import pytest
from total_depth_pressure import wet_pairs
from total_depth_nonlinear_pressure import gradient, divergence, AccelerationSystem, nonlinear_pressure_force, depth_weights
from finite_depth_pressure_reference import response, LENGTHS, WEIGHTS


@pytest.mark.parametrize('periodic', [False, True])
def test_gradient_divergence_are_negative_adjoints(periodic):
    rng = np.random.default_rng(9301)
    h = np.ones((7, 9)); h[2:5, 4] = 0
    pairs = wet_pairs(h, np.zeros_like(h), periodic)
    scalar, vector = rng.normal(size=h.shape), rng.normal(size=(*h.shape, 2))
    a = np.sum(vector*gradient(scalar, pairs, .5))
    b = np.sum(scalar*divergence(vector, pairs, .5))
    assert abs(a+b) < 1e-13
    np.testing.assert_array_equal(gradient(np.ones_like(h), pairs, .5), np.zeros_like(vector))


def test_variable_bottom_operator_is_spd_and_matches_dense_solve():
    rng = np.random.default_rng(303)
    h = rng.uniform(.4, 2, (5, 7)); h[:, 3] = 0
    bed = rng.uniform(0, .25, h.shape)
    pairs = wet_pairs(h, bed)
    system = AccelerationSystem(h, bed, pairs, .5, 1/3)
    size = h.size*2
    basis = np.eye(size).reshape(size, *h.shape, 2)
    matrix = np.stack([system.apply(v).ravel() for v in basis], axis=-1)
    np.testing.assert_allclose(matrix, matrix.T, atol=1e-13, rtol=0)
    assert np.linalg.eigvalsh(matrix).min() >= 1-1e-12
    rhs = rng.normal(size=(*h.shape, 2))
    actual, stats = system.solve(rhs)
    expected = np.linalg.solve(matrix, rhs.ravel()).reshape(rhs.shape)
    np.testing.assert_allclose(actual, expected, atol=1e-8, rtol=0)
    assert stats['relative_residual'] < 1e-8


@pytest.mark.parametrize('periodic', [False, True])
def test_block_preconditioner_matches_operator_cell_blocks(periodic):
    rng = np.random.default_rng(604)
    h = rng.uniform(.01, 4, (5, 7)); h[2, 3] = 0
    bed = rng.uniform(0, 3, h.shape)
    system = AccelerationSystem(h, bed, wet_pairs(h, bed, periodic), .5, 1/3)
    rhs = rng.normal(size=(*h.shape, 2))
    actual = system.precondition(rhs, 'block')
    for y, x in np.ndindex(h.shape):
        basis = np.zeros((2, *h.shape, 2))
        basis[0, y, x, 0] = 1; basis[1, y, x, 1] = 1
        block = np.stack([system.apply(v)[y, x] for v in basis], axis=-1)
        np.testing.assert_allclose(block@actual[y, x], rhs[y, x], atol=1e-12, rtol=0)
        assert np.linalg.eigvalsh(block).min() >= 1-1e-12


def test_block_and_diagonal_solve_same_spd_equation():
    rng = np.random.default_rng(804)
    h = rng.uniform(.4, 2, (5, 7)); h[:, 3] = 0
    bed = rng.uniform(0, .25, h.shape)
    system = AccelerationSystem(h, bed, wet_pairs(h, bed), .5, 1/3)
    rhs = rng.normal(size=(*h.shape, 2))
    size = h.size*2
    basis = np.eye(size).reshape(size, *h.shape, 2)
    matrix = np.stack([system.apply(v).ravel() for v in basis], axis=-1)
    expected = np.linalg.solve(matrix, rhs.ravel()).reshape(rhs.shape)
    actual, stats = system.solve(rhs, preconditioner='block')
    np.testing.assert_allclose(actual, expected, atol=1e-8, rtol=0)
    assert stats['iterations'] <= 40
    assert stats['relative_residual'] < 1e-8


def test_flat_periodic_nonlinear_pressure_conserves_momentum():
    x = np.arange(128)*.5
    h = (1.5+.45/np.cosh((x-24)/4)**2)[None]
    bed = np.zeros_like(h)
    velocity = np.zeros((*h.shape, 2)); velocity[..., 0] = 4*(h-1.5)/h
    pairs = wet_pairs(h, bed, True)
    hydro = -9.81*h[..., None]*gradient(h, pairs, .5)
    force, stats = nonlinear_pressure_force(h, bed, velocity, hydro, pairs, .5)
    np.testing.assert_allclose(force.sum(axis=(0, 1)), 0, atol=1e-13, rtol=0)
    assert max(s['relative_residual'] for s in stats) < 1e-7


def test_emergent_lake_has_no_nonlinear_pressure_force():
    bed = np.broadcast_to(np.arange(13)*.25, (5, 13)).copy()
    h = np.maximum(0, 2-bed)
    pairs = wet_pairs(h, bed)
    force, stats = nonlinear_pressure_force(h, bed, np.zeros((*h.shape, 2)),
        np.zeros((*h.shape, 2)), pairs, .5)
    np.testing.assert_array_equal(force, np.zeros_like(force))
    assert all(s['relative_residual'] == 0 for s in stats)


def test_nonlinear_pressure_budget_is_not_silently_increased():
    h = np.ones((3, 5)); bed = np.zeros_like(h)
    system = AccelerationSystem(h, bed, wet_pairs(h, bed), .5, 1/3)
    with pytest.raises(ValueError): system.solve(np.ones((*h.shape, 2)), iterations=80)


@pytest.mark.parametrize('interpolation', ['centered', 'depth_weighted'])
def test_rational_closure_retains_linear_response_and_sgn_long_wave_moment(interpolation):
    assert abs(np.sum(LENGTHS*WEIGHTS)-1/3) < 1e-14
    count, dx, depth = 128, .25, 1.5
    x = np.arange(count)*dx
    h = np.full((1, count), depth); bed = np.zeros_like(h)
    pairs = wet_pairs(h, bed, True)
    for mode in (2, 8, 20):
        k = 2*np.pi*mode/(count*dx)
        eta = (1e-5*np.cos(k*x))[None]
        hydro = -9.81*h[..., None]*gradient(eta, pairs, dx)
        force, stats = nonlinear_pressure_force(h, bed, np.zeros((*h.shape, 2)), hydro, pairs, dx, interpolation=interpolation)
        np.testing.assert_allclose(hydro+force, response(depth*np.sin(k*dx)/dx)*hydro, atol=1e-13, rtol=0)
        assert max(s['relative_residual'] for s in stats) < 1e-10


@pytest.mark.parametrize('model', ['sgn', 'rational_sgn'])
@pytest.mark.parametrize('interpolation', ['centered', 'depth_weighted'])
def test_coupled_nonlinear_pressure_preserves_flat_periodic_momentum(model, interpolation):
    from total_depth_bank_replay import advance
    from audit_total_depth_dispersion import solitary
    x = (np.arange(192)+.5)*.5
    state, _ = solitary(x, 0)
    final, stats = advance(state[None], np.zeros((1, x.size)), .5, .2,
        second_order=True, periodic=True, dispersive=True, pressure_model=model, pressure_interpolation=interpolation)
    assert abs(np.sum(final[0, :, 1]-state[:, 1])*.5) < 1e-12
    assert abs(stats['volume_error_m3']) < 1e-12
    assert stats['pressure_solver']['worst_relative_residual'] < 1e-7


@pytest.mark.parametrize('model', ['sgn', 'rational_sgn'])
@pytest.mark.parametrize('interpolation', ['centered', 'depth_weighted'])
def test_coupled_nonlinear_pressure_keeps_emergent_lake_at_rest(model, interpolation):
    from total_depth_bank_replay import advance
    bed = np.broadcast_to(np.arange(13)*.25, (5, 13)).copy()
    state = np.zeros((*bed.shape, 3)); state[..., 0] = np.maximum(0, 2-bed)
    final, stats = advance(state, bed, .5, .2,
        second_order=True, dispersive=True, pressure_model=model, pressure_interpolation=interpolation)
    np.testing.assert_allclose(final, state, atol=2e-14, rtol=0)
    assert abs(stats['volume_error_m3']) < 1e-12


def test_standard_sgn_includes_uniform_slope_bottom_reaction():
    # Away from the ends, a constant-thickness layer on b=s*x has
    # (1+s*s)*a_x=-g*s. The bottom-normal reaction must not be omitted.
    h = np.ones((1, 101))
    slope, dx = .1, .5
    bed = (slope*dx*np.arange(101))[None]
    pairs = wet_pairs(h, bed)
    hydro = np.zeros((*h.shape, 2)); hydro[..., 0] = -9.81*slope
    force, _ = nonlinear_pressure_force(h, bed, np.zeros_like(hydro), hydro, pairs, dx, rational=False)
    np.testing.assert_allclose((hydro+force)[0, 50, 0], -9.81*slope/(1+slope*slope), atol=1e-10, rtol=0)


def test_progress_observation_does_not_change_evolution():
    from total_depth_bank_replay import advance
    state = np.zeros((3, 7, 3)); state[..., 0] = 1
    bed = np.zeros((3, 7)); events = []
    expected, _ = advance(state, bed, .5, .03, second_order=True, dispersive=True, pressure_model='rational_sgn')
    actual, _ = advance(state, bed, .5, .03, second_order=True, dispersive=True,
        pressure_model='rational_sgn', progress_every_seconds=.01, on_progress=events.append)
    np.testing.assert_array_equal(actual, expected)
    assert events[-1]['elapsed_s'] == .03
    assert all(a['elapsed_s'] < b['elapsed_s'] for a, b in zip(events, events[1:]))


def test_checkpoint_observer_cannot_modify_evolving_state():
    from total_depth_bank_replay import advance
    state = np.zeros((3, 7, 3)); state[..., 0] = 1
    bed = np.zeros((3, 7)); events = []
    def capture(value, progress):
        events.append((value.copy(), progress.copy()))
        value[:] = -100
    expected, _ = advance(state, bed, .5, .03, second_order=True)
    actual, _ = advance(state, bed, .5, .03, second_order=True,
        progress_every_seconds=.01, on_checkpoint=capture)
    np.testing.assert_array_equal(actual, expected)
    np.testing.assert_array_equal(events[-1][0], expected)
    assert events[-1][1]['elapsed_s'] == .03


def test_step_observer_cannot_modify_evolving_states():
    from total_depth_bank_replay import advance
    state = np.zeros((3, 7, 3)); state[..., 0] = 1
    bed = np.zeros((3, 7)); events = []
    def capture(previous, current, progress):
        events.append(progress.copy())
        previous[:] = -100; current[:] = -100
    expected, _ = advance(state, bed, .5, .03, second_order=True)
    actual, stats = advance(state, bed, .5, .03, second_order=True, on_step=capture)
    np.testing.assert_array_equal(actual, expected)
    assert len(events) == stats['steps']
    assert events[-1]['elapsed_s'] == .03


@pytest.mark.parametrize('periodic', [False, True])
def test_depth_weighted_derivatives_are_adjoint_and_preserve_constants(periodic):
    rng = np.random.default_rng(9302)
    h = 10**rng.uniform(-25, 1, (7, 9)); h[3, 3] = 0
    pairs = wet_pairs(h, np.zeros_like(h), periodic)
    weights = depth_weights(h)
    scalar, vector = rng.normal(size=h.shape), rng.normal(size=(*h.shape, 2))
    assert abs(np.sum(vector*gradient(scalar, pairs, .5, weights))
        +np.sum(scalar*divergence(vector, pairs, .5, weights))) < 1e-12
    np.testing.assert_array_equal(gradient(np.ones_like(h), pairs, .5, weights), 0)


def test_depth_weighted_gradient_retains_flat_periodic_momentum():
    rng = np.random.default_rng(9303)
    h = 10**rng.uniform(-25, 1, (7, 9))
    scalar = rng.normal(size=h.shape)
    result = gradient(scalar, wet_pairs(h, np.zeros_like(h), True), .5, depth_weights(h))
    np.testing.assert_allclose(result.sum(axis=(0, 1)), 0, atol=1e-13, rtol=0)


def test_depth_weights_do_not_cancel_nonzero_thin_fraction():
    h = np.array([[1., 1e-50]])
    own, other = depth_weights(h)[0]
    assert other[0, 0] == 1e-50
    assert own[0, 1] == 1e-50
    assert 1-own[0, 0] == 0  # The tempting complement would lose the mass.


def test_subnormal_depth_uses_finite_force_depth_quotient_without_reciprocal_overflow():
    h = np.array([[1., 1e-310, .5]])
    bed = np.zeros_like(h); velocity = np.zeros((*h.shape, 2))
    hydro = np.zeros_like(velocity); hydro[..., 0] = -.75*h
    with np.errstate(over='raise', invalid='raise', divide='raise'):
        force, stats = nonlinear_pressure_force(h, bed, velocity, hydro, wet_pairs(h, bed, True), .5,
            interpolation='depth_weighted')
    assert np.all(np.isfinite(force))
    assert all(np.isfinite(s['relative_residual']) for s in stats)
    acceleration = np.divide(hydro+force, h[..., None])
    assert np.linalg.norm(acceleration[0, 1]) < 2


def test_depth_weighted_pressure_has_no_singular_thin_cell_acceleration():
    # A bounded velocity field at a draining, vanishing-depth cell must not
    # acquire unbounded acceleration merely from interpolating its velocity.
    for tiny in (1e-6, 1e-12, 1e-25, 1e-50):
        h = np.array([[.2, .1, tiny, .3, .1]])
        bed = np.zeros_like(h); pairs = wet_pairs(h, bed, True)
        velocity = np.zeros((*h.shape, 2)); velocity[..., 0] = [1, 2, 1, .5, 1]
        force, stats = nonlinear_pressure_force(h, bed, velocity, np.zeros_like(velocity), pairs, .5,
            interpolation='depth_weighted')
        assert np.linalg.norm(force[0, 2]/tiny) < 1
        assert max(s['relative_residual'] for s in stats) < 1e-10
        np.testing.assert_allclose(force.sum(axis=(0, 1)), 0, atol=1e-14, rtol=0)


def test_depth_weighted_operator_and_block_match_dense_matrix():
    rng = np.random.default_rng(9304)
    h = 10**rng.uniform(-8, .2, (5, 7)); h[2, 3] = 0
    bed = rng.uniform(0, .25, h.shape)
    system = AccelerationSystem(h, bed, wet_pairs(h, bed, True), .5, 1/3, interpolation='depth_weighted')
    size = h.size*2
    basis = np.eye(size).reshape(size, *h.shape, 2)
    matrix = np.stack([system.apply(v).ravel() for v in basis], axis=-1)
    np.testing.assert_allclose(matrix, matrix.T, atol=1e-13, rtol=0)
    assert np.linalg.eigvalsh(matrix).min() >= 1-1e-12
    rhs = rng.normal(size=(*h.shape, 2))
    actual, stats = system.solve(rhs)
    expected = np.linalg.solve(matrix, rhs.ravel()).reshape(rhs.shape)
    np.testing.assert_allclose(actual, expected, atol=1e-8, rtol=0)
    assert stats['relative_residual'] < 1e-8
    preconditioned = system.precondition(rhs, 'block')
    for i in range(h.size):
        np.testing.assert_allclose(matrix[2*i:2*i+2, 2*i:2*i+2]@preconditioned.reshape(-1, 2)[i],
            rhs.reshape(-1, 2)[i], atol=1e-12, rtol=0)


@pytest.mark.parametrize('interpolation', ['centered', 'depth_weighted'])
def test_kinematic_terms_match_direct_time_differentiation(interpolation):
    from total_depth_nonlinear_pressure import kinematic_terms
    rng = np.random.default_rng(9741)
    h = rng.uniform(.3, 1.2, (5, 7)); bed = rng.uniform(0, .1, h.shape)
    u = rng.uniform(-.5, .5, (*h.shape, 2))
    ht = rng.uniform(-.2, .2, h.shape); ut = rng.uniform(-.3, .3, u.shape)
    pairs = wet_pairs(h, bed, True); dx = .5
    weights = depth_weights(h) if interpolation == 'depth_weighted' else None
    q, c, advective = kinematic_terms(h, bed, u, ht, pairs, dx, weights)
    a = ut+advective; b = gradient(bed, pairs, dx, weights)
    eps = 1e-6
    values = []
    for sign in (-1, 1):
        hs, us = h+sign*eps*ht, u+sign*eps*ut
        ws = depth_weights(hs) if weights is not None else None
        values.append((divergence(us, pairs, dx, ws), np.sum(us*gradient(bed, pairs, dx, ws), axis=-1)))
    div = divergence(u, pairs, dx, weights)
    direct_q = div**2-(values[1][0]-values[0][0])/(2*eps) \
        -np.sum(u*gradient(div, pairs, dx, weights), axis=-1)
    direct_c = (values[1][1]-values[0][1])/(2*eps) \
        +np.sum(u*gradient(np.sum(u*b, axis=-1), pairs, dx, weights), axis=-1)
    np.testing.assert_allclose(q-divergence(a, pairs, dx, weights), direct_q, atol=2e-10, rtol=0)
    np.testing.assert_allclose(c+np.sum(b*a, axis=-1), direct_c, atol=2e-10, rtol=0)


@pytest.mark.parametrize('interpolation', ['centered', 'depth_weighted'])
def test_kinematic_sgn_solved_acceleration_matches_actual_transport_update(monkeypatch, interpolation):
    from total_depth_nonlinear_pressure import kinematic_terms
    rng = np.random.default_rng(9742)
    h = rng.uniform(.3, 1.2, (5, 7)); bed = rng.uniform(0, .1, h.shape)
    u = rng.uniform(-.5, .5, (*h.shape, 2))
    ht = rng.uniform(-.2, .2, h.shape); mt = rng.uniform(-.3, .3, u.shape)
    pairs = wet_pairs(h, bed, True); weights = depth_weights(h) if interpolation == 'depth_weighted' else None
    solved = []; original = AccelerationSystem.solve
    def capture(system, rhs, *args, **kwargs):
        result = original(system, rhs, *args, **kwargs)
        solved.append(result[0]*system.inv_root[..., None])
        return result
    monkeypatch.setattr(AccelerationSystem, 'solve', capture)
    force, stats = nonlinear_pressure_force(h, bed, u, np.zeros_like(u), pairs, .5,
        rational=False, interpolation=interpolation, formulation='kinematic', mass_rate=ht, momentum_rate=mt)
    _, _, advective = kinematic_terms(h, bed, u, ht, pairs, .5, weights)
    actual = (mt+force-u*ht[..., None])/h[..., None]+advective
    base = (mt-u*ht[..., None])/h[..., None]+advective
    np.testing.assert_allclose(actual, base+solved[0], atol=1e-9, rtol=0)
    assert stats[0]['relative_residual'] < 1e-9


def test_kinematic_formulation_requires_transport_rates():
    h = np.ones((3, 5)); bed = np.zeros_like(h); u = np.zeros((*h.shape, 2))
    with pytest.raises(ValueError, match='actual finite-volume'):
        nonlinear_pressure_force(h, bed, u, u, wet_pairs(h, bed), .5, formulation='kinematic')


def test_kinematic_thin_inflow_keeps_finite_conservative_rate():
    from total_depth_bank_replay import rate
    h = np.array([[.2, 1e-310, .3]])
    u = np.array([[1., 0., .5]])
    state = np.stack((h, h*u, np.zeros_like(h)), axis=-1)
    with np.errstate(over='raise', invalid='raise', divide='raise'):
        actual, bound = rate(state, np.zeros_like(h), .5, periodic=True, second_order=True,
            dispersive=True, pressure_model='rational_sgn', pressure_interpolation='depth_weighted',
            pressure_formulation='kinematic')
    assert np.all(np.isfinite(actual)) and bound > 0
    assert actual[0, 1, 0] > 0
    np.testing.assert_allclose(actual.sum(axis=(0, 1)), 0, atol=1e-14, rtol=0)
    assert abs(actual).max() < 2  # Physical flux scale, not a repaired rate.


def test_pressure_pcg_normalization_does_not_overflow_large_finite_rhs():
    h = np.ones((3, 5)); bed = np.zeros_like(h)
    system = AccelerationSystem(h, bed, wet_pairs(h, bed, True), .5, 1/3, interpolation='depth_weighted')
    rhs = np.arange(30, dtype=float).reshape(3, 5, 2)*1e153
    with np.errstate(over='raise', invalid='raise', divide='raise'):
        value, stats = system.solve(rhs)
    np.testing.assert_allclose(system.apply(value)/1e153, rhs/1e153, atol=1e-10, rtol=0)
    assert stats['relative_residual'] < 1e-10


def test_factored_weighted_operator_matches_independent_derivative_form():
    rng = np.random.default_rng(9743)
    h = 10**rng.uniform(-25, .3, (5, 7)); h[2, 3] = 0
    bed = rng.uniform(0, .1, h.shape); pairs = wet_pairs(h, bed, True)
    system = AccelerationSystem(h, bed, pairs, .5, 1/3, interpolation='depth_weighted')
    value = rng.normal(size=(*h.shape, 2)); scalar = rng.normal(size=h.shape)
    expected_w = system.h32*divergence(value*system.inv_root[..., None], pairs, .5, system.weights) \
        -1.5*np.sum(system.b*value, axis=-1)
    expected_transpose = -system.inv_root[..., None]*gradient(system.h32*scalar, pairs, .5, system.weights) \
        -1.5*system.b*scalar[..., None]
    np.testing.assert_allclose(system.w(value), expected_w, atol=1e-14, rtol=2e-14)
    np.testing.assert_allclose(system.transpose_w(scalar), expected_transpose, atol=1e-14, rtol=2e-14)


@pytest.mark.parametrize('model', ['sgn', 'rational_sgn'])
@pytest.mark.parametrize('bed_slope', ['weighted', 'geometry'])
def test_kinematic_coupling_keeps_lake_and_flat_periodic_momentum(model, bed_slope):
    from total_depth_bank_replay import advance
    from audit_total_depth_dispersion import solitary
    bed = np.broadcast_to(np.arange(13)*.25, (5, 13)).copy()
    state = np.zeros((*bed.shape, 3)); state[..., 0] = np.maximum(0, 2-bed)
    final, _ = advance(state, bed, .5, .1, second_order=True, dispersive=True,
        pressure_model=model, pressure_interpolation='depth_weighted', pressure_formulation='kinematic', pressure_bed_slope=bed_slope)
    np.testing.assert_allclose(final, state, atol=2e-14, rtol=0)
    x = (np.arange(192)+.5)*.5; state, _ = solitary(x, 0)
    final, stats = advance(state[None], np.zeros((1, x.size)), .5, .2, second_order=True,
        periodic=True, dispersive=True, pressure_model=model,
        pressure_interpolation='depth_weighted', pressure_formulation='kinematic', pressure_bed_slope=bed_slope)
    np.testing.assert_allclose(np.sum(final[0]-state, axis=0), 0, atol=2e-12, rtol=0)
    assert abs(stats['volume_error_m3']) < 1e-12


def test_fixed_bed_slope_does_not_accelerate_when_depth_weights_change():
    from total_depth_nonlinear_pressure import geometric_bed_slope, kinematic_terms
    h = np.array([[.1, 1e-14, 1e-18, .1]])
    bed = (np.arange(4)*.5*.01)[None]
    pairs = [np.array([[True, True, True, False]]), np.zeros_like(h, dtype=bool)]
    u = np.zeros((*h.shape, 2)); u[..., 0] = 1
    ht = np.array([[0., 0., 1e-4, 0.]])
    weights = depth_weights(h)
    _, old_curvature, _ = kinematic_terms(h, bed, u, ht, pairs, .5, weights)
    slope = geometric_bed_slope(bed, .5)
    _, curvature, _ = kinematic_terms(h, bed, u, ht, pairs, .5, weights, slope)
    assert abs(old_curvature).max() > 1e6
    np.testing.assert_allclose(slope[..., 0], .01, atol=1e-17, rtol=0)
    np.testing.assert_allclose(curvature, 0, atol=1e-16, rtol=0)


def test_physical_bed_slope_operator_is_spd_and_has_dry_identity_rows():
    from total_depth_nonlinear_pressure import geometric_bed_slope
    rng = np.random.default_rng(9745)
    h = rng.uniform(.2, 1., (3, 5)); h[1, 2] = 0
    bed = rng.uniform(-.1, .1, h.shape)
    system = AccelerationSystem(h, bed, wet_pairs(h, bed), .5, 1/3,
        interpolation='depth_weighted', bed_slope=geometric_bed_slope(bed, .5))
    size = h.size*2; basis = np.eye(size).reshape(size, *h.shape, 2)
    matrix = np.stack([system.apply(v).ravel() for v in basis], axis=-1)
    np.testing.assert_allclose(matrix, matrix.T, atol=1e-14, rtol=0)
    assert np.linalg.eigvalsh(matrix).min() >= 1-1e-12
    i = 2*(1*5+2)
    np.testing.assert_array_equal(matrix[i:i+2], np.eye(size)[i:i+2])
