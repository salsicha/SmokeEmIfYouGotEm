import unittest
import numpy as np
from water_feature_rt0_step import tank_mesh
from water_feature_moving_tetra import MovingLiquid
from analyze_water_feature_moving_surface import top_faces, triangle_data, mode_readback


class MovingObservableTests(unittest.TestCase):
    def setup_mesh(self, n=2):
        v, t = tank_mesh(n); m = MovingLiquid(v, t)
        initial = m.positions.copy()
        initial[:, 2] += initial[:, 2]/.5*.02*np.cos(np.pi*initial[:, 0])
        return m, top_faces(m.vertex_cells, m.cells, initial)

    def test_triangle_measure(self):
        l, w = triangle_data(8)
        np.testing.assert_allclose(l.sum(axis=1), 1., atol=2e-15)
        self.assertAlmostEqual(w.sum(), .5, places=15)
        self.assertAlmostEqual(np.sum(w*l[:, 1]**4), 1/30, places=15)

    def test_complete_top_face_coverage(self):
        for n in (1, 2, 3):
            m, faces = self.setup_mesh(n)
            self.assertEqual(len(faces), 2*n*n)
            coefficients, areas, orientation = mode_readback(m.positions[None], m.cells, faces, 8)
            np.testing.assert_allclose(coefficients, 0., atol=2e-15)
            self.assertAlmostEqual(areas[0], .6, places=14)
            self.assertGreater(orientation, 0.)

    def test_constant_eulerian_height(self):
        m, faces = self.setup_mesh(2); pos = m.positions.copy()
        pos[:, 2] *= 1.02
        coefficients, _, _ = mode_readback(pos[None], m.cells, faces, 12)
        np.testing.assert_allclose(coefficients, [[.01, 0., 0., 0.]], atol=2e-15)

    def test_reversed_top_surface_rejected(self):
        m, faces = self.setup_mesh(1)
        reversed_faces = [(ci, [c[0], c[2], c[1]]) for ci, c in faces]
        with self.assertRaises(ValueError):
            mode_readback(m.positions[None], m.cells, reversed_faces, 8)


if __name__ == '__main__':
    unittest.main()
