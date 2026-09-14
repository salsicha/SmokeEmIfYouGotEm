import numpy as np
import pytest
from reconstructed_damped_polynomial_reference import DampedPolynomialSystem
from test_reconstructed_polynomial_sweep_reference import system
from diagnose_reconstructed_pressure_convergence import assembled_matrix


@pytest.mark.parametrize('degree', [0, 1, 2, 4, 8])
def test_damped_polynomial_spd_spectral_bound_and_unchanged_fine_action(degree):
    original = system(); wrapper = DampedPolynomialSystem(original, degree)
    a = assembled_matrix(original).toarray(); r = np.diag(1/np.sqrt(np.diag(a)))
    s = r@a@r; spectrum = np.linalg.eigvalsh(s)
    assert spectrum.min() > 0 and spectrum.max() <= wrapper.bound
    b = np.eye(a.shape[0])-wrapper.omega*s
    f = np.eye(a.shape[0]); power = f.copy()
    for _ in range(degree): power = b@power; f += power
    p = wrapper.omega*r@f@r
    rng = np.random.default_rng(293); x = rng.normal(size=(*original.h.shape, 2))
    y = rng.normal(size=x.shape); x.flags.writeable = False
    result = wrapper.precondition(x)
    np.testing.assert_allclose(result.ravel(), p@x.ravel(), atol=2e-15)
    assert np.linalg.eigvalsh(p).min() > 0
    assert np.sum(x*wrapper.precondition(y)) == pytest.approx(np.sum(result*y), abs=1e-14)
    np.testing.assert_array_equal(wrapper.apply(x), original.apply(x))
    value, report = wrapper.solve(x)
    assert report['relative_residual'] < 1e-12
    np.testing.assert_allclose(value.ravel(), np.linalg.solve(a, x.ravel()), atol=2e-12)


@pytest.mark.parametrize('degree', [-1, 9, 1., True])
def test_invalid_polynomial_degrees_rejected(degree):
    with pytest.raises(ValueError): DampedPolynomialSystem(system(), degree)


def test_two_dimensional_actual_rhs_rejects_short_triangular_but_accepts_bounded_polynomial():
    from audit_reconstructed_polynomial_sweep import source_fields, capture_systems
    from reconstructed_pressure_adapter import reconstructed_pressure
    from reconstructed_polynomial_sweep_reference import PolynomialSweepSystem
    import total_depth_bank_replay as bank
    state, bed, dx, kwargs, _ = source_fields('wet_2d', None)
    original_state = state.copy(); captured = []
    with capture_systems(captured), reconstructed_pressure():
        bank.rate(state, bed, dx, second_order=True, **kwargs, dispersive=True,
            pressure_model='rational_sgn', pressure_interpolation='depth_weighted',
            pressure_formulation='kinematic', pressure_bed_slope='geometry', shoreline_limiter='unscaled')
    original, rhs, _, _, _ = captured[0]
    _, rejected = PolynomialSweepSystem(original, 1).solve(rhs)
    _, candidate = DampedPolynomialSystem(original, 1).solve(rhs)
    assert rejected['relative_residual'] > 2e-5
    assert candidate['relative_residual'] < 2e-5
    np.testing.assert_array_equal(state, original_state)
