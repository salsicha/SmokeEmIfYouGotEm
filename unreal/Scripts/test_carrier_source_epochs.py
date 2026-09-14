import unittest
import numpy as np
from audit_carrier_source_epochs import exact_cells, common_triangles


class CarrierSourceEpochTest(unittest.TestCase):
    def test_exact_seam_and_missing_or_fractional_source(self):
        points = np.array([[1., 0.], [2., 0.], [3., 1.], [4., 0.], [1.25, 0.]])
        result = exact_cells(points, [[0., 0.], [2., 0.]], (2, 2), 1.)
        np.testing.assert_array_equal(result, [[0, 0, 1], [1, 0, 0], [1, 1, 1], [-1]*3, [-1]*3])

    def test_duplicate_or_invalid_sources_fail(self):
        for origins in ([[0., 0.], [0., 0.]], [[np.nan, 0.]]):
            with self.assertRaises(ValueError):
                exact_cells([[0., 0.]], origins, (2, 2), 1.)
        with self.assertRaises(ValueError):
            exact_cells([[0., 0.]], [[0., 0.]], (2, 2), 0.)

    def test_common_domain_excludes_dry_missing_and_unavailable(self):
        source = np.zeros((4, 8)); source[:, 0] = np.arange(4)
        source[:, 1:3] = [[0., 0.], [1., 0.], [0., 1.], [1., 1.]]
        source[:, 3] = 1
        wet = np.ones(4)
        self.assertEqual(len(common_triangles(source, 2, 2, wet, wet, [.5, .5], 2)), 2)
        for depth in (0., np.nan, 1e-5):
            changed = wet.copy(); changed[0] = depth
            np.testing.assert_array_equal(common_triangles(source, 2, 2, wet, changed, [.5, .5], 2), [[1, 3, 2]])
        source[0, 3] = 0
        np.testing.assert_array_equal(common_triangles(source, 2, 2, wet, wet, [.5, .5], 2), [[1, 3, 2]])


if __name__ == '__main__':
    unittest.main()
