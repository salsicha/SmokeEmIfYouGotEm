import unittest
import numpy as np
from water_feature_rt0_step import tank_mesh
from water_feature_moving_tetra import MovingLiquid
from water_feature_quadratic_surface import surface_weights, triangle_volume


class QuadraticSurfaceTests(unittest.TestCase):
    def test_flat_boundary_welding_volume_and_partition(self):
        v, t = tank_mesh(2); m = MovingLiquid(v, t)
        for resolution in (1, 2, 4):
            w, faces = surface_weights(m.vertex_cells, m.cells, len(m.positions), resolution)
            self.assertEqual(len(faces), 48*resolution**2)
            self.assertAlmostEqual(triangle_volume(w@m.positions, faces), .3, places=14)
            np.testing.assert_allclose(w.sum(axis=1), 1., atol=1e-15)

    def test_true_curved_positions_not_heightfield(self):
        v, t = tank_mesh(1); m = MovingLiquid(v, t)
        curved = m.positions.copy(); edge_id = m.edges[(4, 6)]
        curved[edge_id] += [.04, .02, -.01]
        w, faces = surface_weights(m.vertex_cells, m.cells, len(curved), 2)
        samples = w@curved
        self.assertLess(np.min(np.linalg.norm(samples-curved[edge_id], axis=1)), 1e-15)
        moved = w@curved-w@m.positions
        self.assertGreater(np.max(np.abs(moved[:, 0])), .02)
        self.assertGreater(np.max(np.abs(moved[:, 1])), .01)

    def test_orientation_reversal_is_not_hidden(self):
        v, t = tank_mesh(1); m = MovingLiquid(v, t); w, faces = surface_weights(m.vertex_cells, m.cells, len(m.positions), 2)
        self.assertAlmostEqual(triangle_volume(w@m.positions, faces[:, ::-1]), -.3, places=14)

    def test_bad_topology_rejected(self):
        v, t = tank_mesh(1); m = MovingLiquid(v, t)
        with self.assertRaises(ValueError):
            surface_weights(m.vertex_cells, m.cells[:, :9], len(m.positions))
        with self.assertRaises(ValueError):
            surface_weights(m.vertex_cells, m.cells, len(m.positions), 0)


if __name__ == '__main__':
    unittest.main()
