import unittest
import numpy as np
from plan_south_fork_normal_segment import sample_atlas, oriented_clearance, require_endpoint_rejoin, distance_to_axis
from plan_south_fork_guided_review import plan


class NormalSegmentPlannerTest(unittest.TestCase):
    def test_direction_and_cross_current_margin_do_not_expand_paddle_capability(self):
        depth = np.full((8, 8), 2.)
        flow = (np.zeros_like(depth), np.full_like(depth, 1.7))
        path, _ = plan(depth, (3, 0), 7, clearance=depth, velocity=flow, allowed_steps=[(0, 1)])
        self.assertEqual(path[-1], (3, 7))
        with self.assertRaisesRegex(ValueError, 'No connected route'):
            plan(depth, (3, 0), 7, clearance=depth, velocity=flow,
                allowed_steps=[(0, 1)], maximum_cross_current=1.5)
        with self.assertRaisesRegex(ValueError, 'eight-neighbor'):
            plan(depth, (3, 0), 7, clearance=depth, allowed_steps=[(0, 0)])
        with self.assertRaisesRegex(ValueError, 'capability'):
            plan(depth, (3, 0), 7, clearance=depth, maximum_cross_current=3.)

    def test_axis_distance_uses_segments_and_corners(self):
        result = distance_to_axis(np.array([2., 5., -1.]), np.array([2., 3., 0.]),
            np.array([[0., 0.], [4., 0.], [4., 4.]]))
        np.testing.assert_allclose(result, [2., 1., 1.])

    def test_endpoint_rejoins_river_without_mutating_source_clearance(self):
        source = np.ones((21, 3))
        constrained = require_endpoint_rejoin(source, np.arange(21.), 2, 10.)
        self.assertTrue(np.array_equal(source, np.ones((21, 3))))
        self.assertTrue(np.array_equal(constrained[:, :2], source[:, :2]))
        self.assertEqual(np.flatnonzero(constrained[:, 2]).tolist(), list(range(5, 16)))

    def test_seam_bilinear_plane_and_reflected_north(self):
        manifest = dict(tile_shape=[2, 2], grid_spacing_m=1.,
            tiles=[dict(origin_m=[-4., -2.]), dict(origin_m=[-2., -2.])])
        data = np.array([[-14., -12.], [-11., -9.], [-10., -8.], [-7., -5.]])
        result, valid = sample_atlas(manifest, {'bed': data}, np.array([-2.5]), np.array([-1.5]))
        self.assertTrue(valid.all())
        self.assertAlmostEqual(result['bed'][0], 2*(-2.5)+3*(-1.5))

    def test_missing_nonzero_corner_rejected_even_tiny_weight(self):
        manifest = dict(tile_shape=[2, 2], grid_spacing_m=1., tiles=[dict(origin_m=[0., 0.])])
        _, valid = sample_atlas(manifest, {'h': np.ones((2, 2))}, np.array([1., 1.+1e-13]), np.array([0., 0.]))
        self.assertEqual(valid.tolist(), [True, False])

    def test_tile_gap_never_bridged(self):
        manifest = dict(tile_shape=[2, 2], grid_spacing_m=1.,
            tiles=[dict(origin_m=[0., 0.]), dict(origin_m=[4., 0.])])
        _, valid = sample_atlas(manifest, {'h': np.ones((4, 2))}, np.array([2.5]), np.array([.5]))
        self.assertFalse(valid.any())

    def test_oriented_envelope_respects_width_and_rotation(self):
        depth = np.full((41, 41), 2.)
        depth[20, 24] = 0.
        forward = oriented_clearance(depth, .5, 0.)
        transverse = oriented_clearance(depth, .5, np.pi/2)
        self.assertLess(forward[20, 20], .55)
        self.assertGreater(transverse[20, 20], .55)
        self.assertEqual(forward[0, 0], 0.)


if __name__ == '__main__':
    unittest.main()
