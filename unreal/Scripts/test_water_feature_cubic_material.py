import unittest
import numpy as np
from water_feature_rt0_step import tank_mesh
from water_feature_cubic_material import CubicMaterial, lattice, cubic_basis, barycentric_split


class CubicMaterialTests(unittest.TestCase):
    def test_nodal_kronecker_and_partition(self):
        nodes = lattice(3)/3; N, d = cubic_basis(nodes)
        np.testing.assert_allclose(N, np.eye(20), atol=2e-15)
        np.testing.assert_allclose(N.sum(axis=1), 1., atol=2e-15)
        np.testing.assert_allclose(d.sum(axis=1), 0., atol=4e-15)

    def test_analytic_gradient_by_finite_difference(self):
        l = np.array([[.12, .21, .31, .36]]); N, d = cubic_basis(l); e = 1e-6
        for j in range(3):
            delta = np.zeros_like(l); delta[:, 0] = -e; delta[:, j+1] = e
            plus, _ = cubic_basis(l+delta); minus, _ = cubic_basis(l-delta)
            np.testing.assert_allclose((plus-minus)/(2*e), d[:, :, j], atol=2e-10)

    def test_shared_topology_and_mass(self):
        v, t = tank_mesh(2); m = CubicMaterial(v, t)
        self.assertEqual(m.cells.shape, (48, 20)); self.assertEqual(len(m.positions), 343)
        self.assertAlmostEqual(m.material_mass, 300., places=10)
        self.assertAlmostEqual(m.volume(m.positions), .3, places=13)
        np.linalg.cholesky(m.scalar_mass)

    def test_hydrostatic_stays_still(self):
        v, t = tank_mesh(1); m = CubicMaterial(v, t); m.tank_slip_walls(); x = m.positions.copy()
        p, proof = m.step(.004)
        np.testing.assert_allclose(m.positions, x, atol=2e-14)
        np.testing.assert_allclose(m.velocities, 0., atol=3e-12)
        exact = (1000*9.80665*(.5-v[m.vertex_cells, 2])).ravel()
        B = m.divergence_matrix(x)[:, ~m.fixed.ravel()]
        np.testing.assert_allclose(B.T@p, B.T@exact, atol=2e-8)

    def test_ballistic_material_translation(self):
        v, t = tank_mesh(1); m = CubicMaterial(v, t); x = m.positions.copy()
        initial = np.array([.1, -.2, .3]); m.velocities[:] = initial
        g = np.array([0., 0., -9.80665]); dt = .01; p, proof = m.step(dt)
        np.testing.assert_allclose(m.positions, x+dt*initial+.5*dt*dt*g, atol=3e-14)
        np.testing.assert_allclose(p, 0., atol=2e-8)

    def test_swept_cubic_volume_identity(self):
        v, t = tank_mesh(1); m = CubicMaterial(v, t); x = m.positions.copy()
        delta = np.random.default_rng(513).normal(size=x.shape)*.002
        B = (m.divergence_matrix(x)+4*m.divergence_matrix(x+delta/2)+m.divergence_matrix(x+delta))/6
        self.assertAlmostEqual(m.volume(x+delta)-m.volume(x), float(np.sum(B@delta.ravel())), delta=3e-15)

    def test_positive_mapping_and_atomic_failure(self):
        v, t = tank_mesh(1); m = CubicMaterial(v, t); old = m.positions.copy()
        bad = old.copy(); bad[:, 2] *= -1
        with self.assertRaises(ValueError):
            m.certify(bad)
        with self.assertRaises(ValueError):
            m.step(-.004)
        np.testing.assert_array_equal(old, m.positions)

    def test_barycentric_pressure_quadratic_hydrostatic(self):
        v, t = tank_mesh(1); v, t = barycentric_split(v, t)
        m = CubicMaterial(v, t, pressure_degree=2); m.tank_slip_walls(); old = m.positions.copy()
        self.assertEqual(len(t), 24); self.assertEqual(m.pressure_nodes, 240)
        p, proof = m.step(.004)
        np.testing.assert_allclose(m.positions, old, atol=3e-14)
        np.testing.assert_allclose(m.velocities, 0., atol=3e-12)
        self.assertEqual(m.pressure_mode, 'discontinuous_p2')
        self.assertEqual(proof['pressure_mode'], 'discontinuous_p2')
        self.assertEqual(proof['pressure_degree'], 2)

    def test_quadratic_pressure_failed_mode_restored(self):
        v, t = tank_mesh(1); m = CubicMaterial(v, t, pressure_degree=2)
        with self.assertRaises(ValueError):
            m.step(-.004)
        self.assertEqual(m.pressure_mode, 'discontinuous_p2')


if __name__ == '__main__':
    unittest.main()
