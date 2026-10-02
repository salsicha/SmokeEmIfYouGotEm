import unittest
import numpy as np
from water_feature_rt0_step import tank_mesh
from water_feature_cubic_material import CubicMaterial
from water_feature_cubic_fast import CubicMaterialFast, cholesky_vector_solve


class CubicFastTests(unittest.TestCase):
    def test_triangular_factor_solve(self):
        rng = np.random.default_rng(591); a = rng.normal(size=(21, 21)); system = a@a.T+np.eye(21)
        rhs = rng.normal(size=21); actual = cholesky_vector_solve(np.linalg.cholesky(system), rhs)
        np.testing.assert_allclose(system@actual, rhs, atol=4e-14)

    def test_matches_full_svd_all_rows_over_ten_steps(self):
        v, t = tank_mesh(1); old = CubicMaterial(v, t, pressure_degree=2); new = CubicMaterialFast(v, t, pressure_degree=2)
        for m in (old, new):
            x = m.positions.copy(); x[:, 2] += x[:, 2]/.5*.02*np.cos(np.pi*x[:, 0]); m.initialize_material(x); m.tank_slip_walls()
        for i in range(10):
            p, _ = old.step(.004); q, proof = new.step(.004)
            np.testing.assert_allclose(new.positions, old.positions, atol=2e-12)
            np.testing.assert_allclose(new.velocities, old.velocities, atol=2e-10)
            np.testing.assert_allclose(q, p, rtol=3e-8, atol=3e-6)
            self.assertLess(proof['maximum_weak_flux_residual_m3_s'], 2e-11)
            self.assertIsNone(proof['pressure_rank'])

    def test_hydrostatic_and_atomic_failure(self):
        v, t = tank_mesh(1); m = CubicMaterialFast(v, t, pressure_degree=2); m.tank_slip_walls(); old = m.positions.copy()
        m.step(.004); np.testing.assert_allclose(m.positions, old, atol=4e-14)
        m.velocities[m.fixed] = 1.
        before = m.positions.copy()
        with self.assertRaises(ValueError):
            m.step(.004)
        np.testing.assert_array_equal(before, m.positions)


if __name__ == '__main__':
    unittest.main()
