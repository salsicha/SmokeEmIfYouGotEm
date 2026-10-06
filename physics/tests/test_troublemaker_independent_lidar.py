import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from audit_troublemaker_independent_lidar import summarize_neighbours
from audit_troublemaker_survey_alignment import fit_offset
import numpy as np


class IndependentSurveyTests(unittest.TestCase):
    def test_known_offset_recovery(self):
        gradients = np.array([(x,y) for x in [-.4,0,.4] for y in [-.3,-.1,.1,.3]])
        offset = np.array([.2,-.15,.08])
        residuals = gradients @ offset[:2] + offset[2]
        actual, condition = fit_offset(gradients,residuals)
        np.testing.assert_allclose(actual,offset,atol=1e-14)
        self.assertTrue(np.isfinite(condition))

    def test_flat_ground_cannot_register_xy(self):
        with self.assertRaises(ValueError):
            fit_offset(np.zeros((12,2)), np.zeros(12))
        with self.assertRaises(ValueError):
            fit_offset(np.zeros((2,2)), np.zeros(2))

    def test_empty_is_missing_not_zero_height(self):
        actual = summarize_neighbours([], 100, .3)
        self.assertEqual(actual['count'], 0)
        self.assertEqual(actual['classes'], {})
        self.assertIsNone(actual['height_delta_quantiles_m'])

    def test_radius_boundary_and_signed_difference(self):
        points = [(10, .3, 98, 1), (11, .1, 104, 2), (12, .300001, 900, 7)]
        actual = summarize_neighbours(points, 100, .3)
        self.assertEqual(actual['count'], 2)
        self.assertEqual(actual['classes'], {'1': 1, '2': 1})
        self.assertEqual(actual['height_delta_quantiles_m'], [-2, 1, 4])
        self.assertEqual(summarize_neighbours(points, 100, .5)['classes'], {'1': 1, '2': 1, '7': 1})

    def test_no_automatic_class_filter(self):
        points = [(1, 0, 1, 7), (2, .1, 2, 18), (3, .2, 3, 9)]
        self.assertEqual(summarize_neighbours(points, 0, 1)['count'], 3)

    def test_reject_invalid_inputs(self):
        for z, radius in [(float('nan'), 1), (0, 0), (0, -1), (0, float('inf'))]:
            with self.assertRaises(ValueError):
                summarize_neighbours([], z, radius)
        for distance, height in [(-1, 0), (float('nan'), 0), (0, float('inf'))]:
            with self.assertRaises(ValueError):
                summarize_neighbours([(0, distance, height, 1)], 0, 1)


if __name__ == '__main__':
    unittest.main()
