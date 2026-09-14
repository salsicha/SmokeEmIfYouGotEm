import unittest
import numpy as np
from finite_depth_pressure_reference import response, chebyshev_potentials


class FiniteDepthPressureTest(unittest.TestCase):
    def test_independent_continued_fraction_and_accuracy(self):
        x = np.linspace(0, 8, 1001)
        denominator = np.full_like(x, 9)
        for odd in (7, 5, 3, 1):
            denominator = odd + x * x / denominator
        np.testing.assert_allclose(response(x), 1 / denominator, rtol=1e-14)
        exact = np.ones_like(x)
        exact[1:] = np.tanh(x[1:]) / x[1:]
        self.assertLess(np.max(abs(np.sqrt(response(x) / exact) - 1)), .03)
        self.assertTrue(np.all(np.diff(response(x)) <= 0))
        self.assertAlmostEqual(response(0), 1)

    def test_varying_wet_graph_matches_direct_linear_solve(self):
        y, x = np.mgrid[:7, :9]
        depth = .4 + .25 * x + .1 * y
        depth[:, 4] = 0
        eta = .01 * np.cos(x + 2 * y)
        for periodic in (False, True):
            actual, direct = chebyshev_potentials(depth, eta, .5, 40, periodic)
            np.testing.assert_allclose(actual, direct, atol=3e-5, rtol=0)
            refined, _ = chebyshev_potentials(depth, eta, .5, 64, periodic)
            self.assertLess(np.max(abs(refined - direct)), np.max(abs(actual - direct)))

    def test_constant_rest_and_disconnected_bank(self):
        depth = np.ones((5, 7)); depth[:, 3] = 0
        eta = np.zeros_like(depth); eta[:, :3] = .02
        actual, direct = chebyshev_potentials(depth, eta, .5)
        np.testing.assert_allclose(actual, np.broadcast_to(eta.ravel(), actual.shape), atol=1e-15)
        np.testing.assert_allclose(actual, direct, atol=1e-15)

    def test_invalid_state_and_iterations(self):
        for depth, eta, iterations in (([[-1]], [[0]], 32), ([[1]], [[np.nan]], 32),
                                      ([[1]], [[0]], 0), ([[1]], [[0]], 129)):
            with self.assertRaises(ValueError):
                chebyshev_potentials(depth, eta, .5, iterations)


if __name__ == "__main__":
    unittest.main()
