import unittest
import numpy as np
from triangle_section_clearance import section_knots, supported_intervals, evaluate_section
from export_colorado_catalog_runtime import landscape_sample


class TriangleSectionClearanceTests(unittest.TestCase):
    def test_crossing_and_disconnected_width(self):
        self.assertEqual(supported_intervals([0, 2, 4], [0, 2, 0], 1), [[0., 1.], [3., 4.]])

    def test_flat_threshold_and_merging(self):
        self.assertEqual(supported_intervals([0, 1, 2, 3], [1, 1, 0, 1], 1), [[0., 3.]])

    def test_isolated_touch_has_zero_width(self):
        self.assertEqual(supported_intervals([0, 1, 2], [2, 1, 2], 1), [])

    def test_missing_cannot_pass(self):
        with self.assertRaises(ValueError):
            supported_intervals([0, 1], [0, np.nan], 1)

    def test_invalid_geometry(self):
        for direction, bounds, spacing in (([0, 0], [-1, 1], 2), ([1, 0], [1, -1], 2), ([1, 0], [-1, 1], 0)):
            with self.assertRaises(ValueError):
                section_knots([0, 0], direction, bounds, [0, 0], spacing)

    def test_diagonal_knots_are_included(self):
        knots = section_knots([.2, .2], [1, 0], [0, 1], [0, 0], 1)
        np.testing.assert_allclose(knots, [0, .6, .8, 1])

    def test_real_native_diagonal_and_reverse(self):
        height = np.array([[0., 2., 3.], [4., 0., 6.], [5., 7., 1.]])
        def sample(xy):
            return landscape_sample(height, 2-xy[:, 1], xy[:, 0])
        direction = np.array([.8, .6])
        result = evaluate_section(sample, [1, 1], direction, [-1, 1], [0, 0], 1, 2)
        reverse = evaluate_section(sample, [1, 1], -direction, [-1, 1], [0, 0], 1, 2)
        self.assertAlmostEqual(result['continuous_width_m'], reverse['continuous_width_m'], places=10)
        knots = np.asarray(result['knots_m'])
        for a, b in zip(knots[:-1], knots[1:]):
            s = np.linspace(a, b, 11)
            np.testing.assert_allclose(sample([1, 1]+s[:, None]*direction),
                                       np.interp(s, knots, result['bed_m']), atol=1e-12)

    def test_coarse_point_sampling_can_miss_clear_width(self):
        result = evaluate_section(lambda xy: np.abs(xy[:, 0]), [0, 0], [1, 0], [-4, 4], [0, 0], 2, 2.8)
        self.assertAlmostEqual(result['continuous_width_m'], 5.)

    def test_wrong_sampler_is_rejected(self):
        with self.assertRaises(ValueError):
            evaluate_section(lambda xy: xy[:, 0]**2, [0, 0], [1, 0], [-2, 2], [0, 0], 2, 1)


if __name__ == '__main__':
    unittest.main()
