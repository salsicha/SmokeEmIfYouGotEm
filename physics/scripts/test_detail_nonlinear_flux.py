import numpy as np
import pytest
from detail_nonlinear_flux import G, relative_flux, mean_strain_source, advance_periodic, simple_wave


def test_relative_flux_equals_full_conservation_laws():
    rng = np.random.default_rng(431)
    depth = rng.uniform(.1, 5, 400)
    velocity = rng.uniform(-7, 7, (400, 2))
    state = rng.uniform(-1, 1, (400, 3))
    state[:, 0] *= .8 * depth
    h = depth + state[:, 0]
    m0 = depth[:, None] * velocity
    m = h[:, None] * velocity + state[:, 1:]
    for axis in (0, 1):
        mass = m[:, axis] - m0[:, axis]
        momentum = m[:, axis, None] * m / h[:, None] - m0[:, axis, None] * m0 / depth[:, None]
        momentum[:, axis] += .5 * G * (h * h - depth * depth)
        momentum -= velocity * mass[:, None]
        expected = np.column_stack((mass, momentum))
        np.testing.assert_allclose(relative_flux(state, depth, velocity, axis), expected, atol=2e-13, rtol=2e-13)


def test_nonlinear_characteristics_and_mean_strain():
    state = np.array([.5, 1.2, -.7])
    depth, velocity = 1.5, np.array([.4, -.3])
    for axis in (0, 1):
        jac = np.column_stack([(relative_flux(state + np.eye(3)[j] * 1e-5, depth, velocity, axis)
            - relative_flux(state - np.eye(3)[j] * 1e-5, depth, velocity, axis)) / 2e-5 for j in range(3)])
        speed = velocity[axis] + state[axis + 1] / (depth + state[0])
        c = np.sqrt(G * (depth + state[0]))
        np.testing.assert_allclose(np.sort(np.linalg.eigvals(jac)), [speed-c, speed, speed+c], atol=2e-9)
    gradient = np.array([[.3, -.1], [.7, .2]])
    np.testing.assert_allclose(mean_strain_source(state, gradient), -gradient @ state[1:])
    np.testing.assert_array_equal(mean_strain_source(np.array([.5, 0, 0]), gradient), np.zeros(2))


def test_finite_amplitude_simple_wave_converges_and_conserves():
    errors = []
    for count in (200, 400):
        dx = 40 / count
        x = (np.arange(count) + .5) * dx
        initial = simple_wave(x, 0)
        actual, report = advance_periodic(initial, 1.5, [.4, 0], dx, 1.2)
        exact = simple_wave(x, 1.2)
        errors.append(float(np.mean(abs(actual[:, 0] - exact[:, 0]))))
        np.testing.assert_allclose(actual.sum(axis=0), initial.sum(axis=0), atol=1e-11, rtol=0)
        assert report['elapsed_s'] == 1.2
        assert np.min(1.5 + actual[:, 0]) > 0
    assert errors[1] < .4 * errors[0]
    assert errors[1] < .001


def test_no_silent_negative_depth_or_post_breaking_formula():
    with pytest.raises(ValueError):
        relative_flux(np.array([-2., 0, 0]), 1., np.array([0., 0.]))
    with pytest.raises(ValueError):
        simple_wave(np.arange(5.), 100.)
    zero = np.zeros((31, 3))
    actual, _ = advance_periodic(zero, 1.5, [.4, -.2], .5, .31)
    np.testing.assert_array_equal(actual, zero)
