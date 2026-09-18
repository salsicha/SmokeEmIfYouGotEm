"""Independent inverse-coordinate checks; no force/energy projection allowed."""
import numpy as np
import pytest

from rational_physical_momentum_rate import canonical_rate, physical_rate
from rational_primal_energy import evaluate
from smooth_rational_velocity_stage import make


@pytest.mark.parametrize('shape', ((1, 7), (5, 1), (3, 4)))
@pytest.mark.parametrize('sloped', (False, True))
def test_inverse_direction_matches_finite_difference_and_forward_bridge(shape, sloped):
    rng = np.random.default_rng(28193)
    h = 1.4+.2*rng.random(shape)
    b = .03*rng.random(shape) if sloped else np.zeros(shape)
    p = .2*rng.normal(size=(*shape, 2))
    ht = .1*rng.normal(size=shape)
    pt = .3*rng.normal(size=p.shape)
    saved = [a.copy() for a in (h, b, p, ht, pt)]
    g = make(h, b, .5)
    r = canonical_rate(g, p, ht, pt)
    eps = 1e-5
    sides = [evaluate(make(h+sign*eps*ht, b, .5), p+sign*eps*pt)['canonical_velocity']
             for sign in (-1, 1)]
    np.testing.assert_allclose(r['canonical_velocity_rate'], (sides[1]-sides[0])/(2*eps), rtol=0, atol=2e-9)
    forward = physical_rate(g, r['canonical_velocity'], ht, r['canonical_velocity_rate'],
                            derivative_preconditioner='patch', primal_preconditioner='patch')
    np.testing.assert_allclose(forward['momentum_rate'], pt, rtol=0, atol=1e-10)
    np.testing.assert_allclose(forward['momentum'], p, rtol=0, atol=1e-10)
    assert r['maximum_solve_residual'] <= 2e-5
    for current, original in zip((h, b, p, ht, pt), saved):
        np.testing.assert_array_equal(current, original)


def test_inverse_direction_validates_state_and_mode():
    h = np.ones((1, 4)); p = np.zeros((1, 4, 2)); g = make(h, np.zeros_like(h), .5)
    for bad in (p[..., 0], np.full_like(p, np.nan)):
        with pytest.raises(ValueError):
            canonical_rate(g, p, h, bad)
    with pytest.raises(ValueError, match='Unknown'):
        canonical_rate(g, p, h, p, preconditioner='invented')
