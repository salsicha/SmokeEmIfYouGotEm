import unittest
import numpy as np
from water_feature_rt0_step import tank_mesh
from water_feature_moving_tetra import MovingLiquid, quadrature, basis, geometry_jacobian


class MovingTetraTests(unittest.TestCase):
    def test_reference_quadrature_and_basis(self):
        b, w = quadrature(); n, grad = basis(b)
        self.assertAlmostEqual(w.sum(), 1/6, places=15)
        np.testing.assert_allclose(n.sum(axis=1), 1., atol=1e-15)
        np.testing.assert_allclose(grad.sum(axis=1), 0., atol=1e-15)
        for i in range(4):
            self.assertAlmostEqual(np.sum(w*b[:, i]**4), 1/210, places=15)

    def test_mass_and_global_volume_gradient(self):
        v, t = tank_mesh(1); m = MovingLiquid(v, t); B = m.divergence_matrix(m.positions)
        rng = np.random.default_rng(644); displacement = rng.normal(size=m.positions.shape)*.001
        epsilon = 1e-5
        actual = (m.volume(m.positions+epsilon*displacement)-m.volume(m.positions-epsilon*displacement))/(2*epsilon)
        self.assertAlmostEqual(actual, float(np.sum(B@displacement.ravel())), delta=2e-11)
        self.assertAlmostEqual(m.material_mass, 300., places=11)
        np.linalg.cholesky(m.M)

    def test_swept_volume_identity_for_nonuniform_displacement(self):
        v, t = tank_mesh(1); m = MovingLiquid(v, t); old = m.positions
        delta = np.random.default_rng(333).normal(size=old.shape)*.004; end = old+delta
        B = (m.divergence_matrix(old)+4*m.divergence_matrix((old+end)/2)+m.divergence_matrix(end))/6
        self.assertAlmostEqual(m.volume(end)-m.volume(old), float(np.sum(B@delta.ravel())), delta=2e-15)

    def test_flat_hydrostatic_no_motion(self):
        v, t = tank_mesh(2); m = MovingLiquid(v, t); m.tank_slip_walls(); original = m.positions.copy()
        p, proof = m.step(.004)
        np.testing.assert_allclose(m.positions, original, atol=2e-14)
        np.testing.assert_allclose(m.velocities, 0., atol=2e-12)
        exact_p = (1000*9.80665*(.5-v[m.vertex_cells, 2])).ravel()
        B = m.divergence_matrix(m.positions)[:, ~m.fixed.ravel()]
        np.testing.assert_allclose(B.T@p, B.T@exact_p, atol=2e-8)
        self.assertLess(abs(proof['energy_change_j']), 1e-10)

    def test_ballistic_material_transport(self):
        v, t = tank_mesh(1); m = MovingLiquid(v, t); old = m.positions.copy(); initial = np.array([.1, .2, -.3]); m.velocities[:] = initial
        dt = .01; g = np.array([0., 0., -9.80665]); p, proof = m.step(dt, g)
        np.testing.assert_allclose(m.positions, old+dt*initial+.5*dt*dt*g, atol=5e-14)
        np.testing.assert_allclose(m.velocities, np.broadcast_to(initial+dt*g, m.velocities.shape), atol=1e-11)
        np.testing.assert_allclose(p, 0., atol=2e-8)
        self.assertLess(abs(proof['volume_change_m3']), 1e-13)

    def test_nonuniform_free_surface_and_wall_contact(self):
        v, t = tank_mesh(2); m = MovingLiquid(v, t); m.tank_slip_walls()
        curved = m.positions.copy(); curved[:, 2] += (curved[:, 2]/.5)*.02*np.cos(np.pi*curved[:, 0])
        m.initialize_material(curved)
        old = m.positions.copy(); p, proof = m.step(.004)
        self.assertGreater(np.max(np.abs(m.positions-old)), 1e-8)
        np.testing.assert_array_equal(m.positions[m.fixed], old[m.fixed])
        self.assertLess(abs(proof['volume_change_m3']), 2e-12)
        self.assertLess(abs(proof['energy_change_j']), 2e-9)

    def test_curved_cell_certification_rejects_inversion(self):
        v, t = tank_mesh(1); m = MovingLiquid(v, t); bad = m.positions.copy(); bad[:, 2] = -bad[:, 2]
        with self.assertRaises(ValueError):
            m.certify(bad)

    def test_invalid_step_preserves_state(self):
        v, t = tank_mesh(1); m = MovingLiquid(v, t); old = m.positions.copy()
        with self.assertRaises(ValueError):
            m.step(-.01)
        np.testing.assert_array_equal(m.positions, old)


if __name__ == '__main__':
    unittest.main()
