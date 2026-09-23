"""Geometry tests for the engine foot-contact diagnostic, not crew acceptance."""
import importlib.util
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch


script = Path(__file__).resolve().parents[2] / 'unreal/Scripts/review_crew_foot_contact.py'
spec = importlib.util.spec_from_file_location('foot_contact_review', script)
review = importlib.util.module_from_spec(spec)
with patch.dict(sys.modules, {'unreal': types.ModuleType('unreal')}):
    spec.loader.exec_module(review)


class FootContactProjectionTests(unittest.TestCase):
    def test_slope_and_winding(self):
        triangle = [[0., 0., 3.], [2., 0., 5.], [0., 2., 7.]]
        for winding in (triangle, list(reversed(triangle))):
            self.assertAlmostEqual(review.top_at([0.5, 0.5, -20.], [winding]), 4.5)

    def test_top_surface_not_bottom_or_nearby_vertex(self):
        lower = [[0., 0., -2.], [2., 0., -2.], [0., 2., -2.]]
        upper = [[0., 0., 4.], [2., 0., 4.], [0., 2., 4.]]
        adjacent = [[3., 0., 100.], [4., 0., 100.], [3., 1., 100.]]
        self.assertEqual(review.top_at([0.5, 0.5, 0.], [lower, adjacent, upper]), 4.)

    def test_absent_support_and_vertical_degenerate_face(self):
        triangle = [[0., 0., 3.], [2., 0., 5.], [0., 2., 7.]]
        self.assertIsNone(review.top_at([1.5, 1.5, 0.], [triangle]))
        self.assertIsNone(review.top_at([0., 0., 0.], [[[0., 0., 0.], [0., 0., 3.], [0., 1., 0.]]]))
        self.assertIsNone(review.top_at([0., 0., 0.], []))

    def test_edge_and_translation(self):
        triangle = [[0., 0., 3.], [2., 0., 5.], [0., 2., 7.]]
        self.assertEqual(review.top_at([1., 1., 0.], [triangle]), 6.)
        offset = [10300., -7400., 2300.]
        shifted = [[v+d for v, d in zip(point, offset)] for point in triangle]
        point = [v+d for v, d in zip([0.5, 0.5, 0.], offset)]
        self.assertAlmostEqual(review.top_at(point, [shifted]), 2304.5)


if __name__ == '__main__':
    unittest.main()
