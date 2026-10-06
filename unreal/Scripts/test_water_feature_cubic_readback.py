import unittest
import numpy as np
from water_feature_cubic_material import CubicMaterial, cubic_basis, lattice
from water_feature_moving_tetra import basis
from water_feature_rt0_step import tank_mesh
from qualify_water_feature_cubic_material import nodes, polynomial_basis, reference_data, divergence, metric, bernstein_certificate


class CubicReadbackTests(unittest.TestCase):
    def test_independent_cubic_basis(self):
        bary, w = reference_data(); N, d = polynomial_basis(bary, nodes(3), 3)
        expected, grad = cubic_basis(bary)
        np.testing.assert_allclose(N, expected, atol=1e-14)
        np.testing.assert_allclose(d, grad, atol=4e-14)
        self.assertAlmostEqual(w.sum(), 1/6, places=14)
        self.assertAlmostEqual(np.sum(w*bary[:, 1]**12), 1/(13*14*15), places=14)

    def test_independent_pressure_basis(self):
        from itertools import combinations
        bary, _ = reference_data()
        p2 = np.array([*np.eye(4), *[(np.eye(4)[a]+np.eye(4)[b])/2 for a, b in combinations(range(4), 2)]])
        actual, _ = polynomial_basis(bary, p2, 2); expected, _ = basis(bary)
        np.testing.assert_allclose(actual, expected, atol=2e-14)

    def test_independent_curved_pressure_matrix(self):
        from itertools import combinations
        v, t = tank_mesh(1); m = CubicMaterial(v, t, pressure_degree=2)
        x = m.positions.copy(); x[:, 2] += x[:, 2]/.5*.02*np.cos(np.pi*x[:, 0]); m.initialize_material(x)
        bary, w = reference_data(); _, d = polynomial_basis(bary, nodes(3), 3)
        p2 = np.array([*np.eye(4), *[(np.eye(4)[a]+np.eye(4)[b])/2 for a, b in combinations(range(4), 2)]])
        q, _ = polynomial_basis(bary, p2, 2)
        actual = divergence(x, m.cells, m.pressure_cells, q, d, w, m.pressure_nodes)
        np.testing.assert_allclose(actual, m.divergence_matrix(x), atol=3e-14)

    def test_degree_six_certificate_matches_volume(self):
        v, t = tank_mesh(1); m = CubicMaterial(v, t)
        x = m.positions.copy(); x += np.random.default_rng(781).normal(size=x.shape)*.001
        points, matrix = bernstein_certificate(); _, grad = polynomial_basis(points, nodes(3), 3)
        determinant, _ = metric(x, m.cells, grad); coeff = np.linalg.solve(matrix, determinant.T).T
        # Each degree-six tetrahedral Bernstein polynomial has integral 1/504.
        self.assertEqual(coeff.shape, (6, 84))
        self.assertAlmostEqual(float(coeff.sum()/504), m.volume(x), delta=5e-14)


if __name__ == '__main__':
    unittest.main()
