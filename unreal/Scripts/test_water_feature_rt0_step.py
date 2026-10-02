import unittest
import numpy as np
from water_feature_rt0_step import LiquidTetrahedra, tank_mesh


def tank(n=1, rise=0.):
    v, t = tank_mesh(n, bed_rise=rise); m = LiquidTetrahedra(v, t)
    wall = {int(i): 0. for i in np.flatnonzero(m.boundary & (m.face_centroids[:, 2] != .5))}
    return m, wall


class LiquidRT0Tests(unittest.TestCase):
    def test_volume_tilted_geometry(self):
        for n in (1, 2, 3):
            m, _ = tank(n, .2)
            self.assertAlmostEqual(m.volumes.sum(), .6*(.5-.2/2), places=14)
            self.assertTrue(np.all(m.volumes > 0))

    def test_internal_face_opposite_and_exact_basis(self):
        m, _ = tank(2, .18)
        for fi, owners in enumerate(m.owners):
            self.assertEqual(m.B[:, fi].sum(), 1 if len(owners) == 1 else 0)
        q = m.uniform_flux([.8, -.7, .4]); xyz = m.velocity_at_vertices(q)
        np.testing.assert_allclose(xyz, np.broadcast_to([.8, -.7, .4], xyz.shape), atol=3e-15)
        np.testing.assert_allclose(m.B@q, 0., atol=5e-17)

    def test_mass_matrix_positive_and_constant_energy(self):
        m, _ = tank(2, .15); q = m.uniform_flux([.4, -.2, .1])
        np.testing.assert_allclose(m.M, m.M.T, atol=1e-13)
        np.linalg.cholesky(m.M)
        self.assertAlmostEqual(q@m.M@q/2, .5*1000*m.volumes.sum()*.21, places=12)

    def test_hydrostatic_gravity_and_pressure(self):
        for rise in (0., .2):
            m, walls = tank(2, rise)
            q, pressure, proof = m.step(np.zeros(len(m.faces)), .01, [0., 0., -9.80665], walls)
            np.testing.assert_allclose(q, 0., atol=2e-14)
            np.testing.assert_allclose(pressure, 1000*9.80665*(.5-m.centroids[:, 2]), atol=5e-10)
            self.assertLess(proof['maximum_cell_vertex_speed_m_s'], 1e-12)

    def test_ballistic_all_free_gravity(self):
        m, _ = tank(2, .1); u = np.array([.7, .2, -.5]); dt = .03; g = np.array([0., 0., -9.80665])
        q, p, proof = m.step(m.uniform_flux(u), dt, g, {})
        np.testing.assert_allclose(q, m.uniform_flux(u+dt*g), atol=2e-14)
        np.testing.assert_allclose(p, 0., atol=1e-9)
        self.assertLess(proof['maximum_cell_flux_residual_m3_s'], 1e-13)

    def test_divergent_input_projection_energy_and_wall_contact(self):
        m, walls = tank(2, .2); old = np.random.default_rng(954).normal(0, .003, len(m.faces))
        q, p, proof = m.step(old, .01, [0., 0., 0.], walls)
        self.assertLess(proof['kinetic_after_j'], proof['kinetic_before_j'])
        self.assertLess(abs(proof['energy_identity_error_j']), 1e-12)
        self.assertLess(np.max(np.abs(m.B@q)), 1e-14)
        self.assertEqual(proof['maximum_prescribed_flux_error_m3_s'], 0.)

    def test_prescribed_inflow_free_surface_ledger(self):
        m, walls = tank(2, .1)
        for i in np.flatnonzero(m.boundary & (m.face_centroids[:, 0] == 0)):
            walls[int(i)] = -.02*m.areas[i]
        q, _, proof = m.step(np.zeros(len(m.faces)), .01, [0., 0., 0.], walls)
        self.assertAlmostEqual(proof['free_surface_flux_m3_s'], .02*.6*.5, places=14)
        self.assertAlmostEqual(proof['prescribed_flux_m3_s'], -.02*.6*.5, places=14)
        self.assertLess(abs(proof['domain_boundary_flux_m3_s']), 1e-14)
        self.assertLess(abs(proof['energy_identity_error_j']), 1e-12)

    def test_tiny_tetra_not_deleted(self):
        v = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1e-10]], float)
        m = LiquidTetrahedra(v, [[0, 1, 2, 3]])
        self.assertAlmostEqual(m.volumes[0], 1e-10/6, delta=1e-24)
        self.assertGreater(m.local_mass.max(), 1e10)

    def test_closed_component_rejected_without_gauge_fit(self):
        m, _ = tank()
        with self.assertRaisesRegex(ValueError, 'Closed pressure component'):
            m.step(np.zeros(len(m.faces)), .01, [0, 0, 0], {int(i): 0. for i in np.flatnonzero(m.boundary)})

    def test_reversed_tetra_orientation(self):
        v, t = tank_mesh(1); t[:, 2:4] = t[:, 3:1:-1]
        m = LiquidTetrahedra(v, t); q = m.uniform_flux([1, 2, 3])
        # The cancellation sums four independently evaluated metric fluxes.
        allowance = 16*np.finfo(float).eps*np.max(np.abs(q))
        np.testing.assert_allclose(m.B@q, 0., atol=allowance)
        speed = m.velocity_at_vertices(q)
        np.testing.assert_allclose(speed, np.broadcast_to([1, 2, 3], speed.shape), atol=3e-15)

    def test_invalid_topology_and_boundary(self):
        v, t = tank_mesh(1)
        for cells in (np.concatenate([t, t[:1]]), [[0, 0, 1, 2]]):
            with self.assertRaises(ValueError):
                LiquidTetrahedra(v, cells)
        m, _ = tank(); inside = int(np.flatnonzero(~m.boundary)[0])
        with self.assertRaises(ValueError):
            m.step(np.zeros(len(m.faces)), .01, [0, 0, 0], {inside: 0})

    def test_dense_size_guard(self):
        v, t = tank_mesh(2)
        with self.assertRaisesRegex(ValueError, 'size bound'):
            LiquidTetrahedra(v, t, maximum_faces=5)


if __name__ == '__main__':
    unittest.main()
