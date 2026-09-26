import sys
import unittest
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from audit_south_fork_canopy_channel import sample_mask


class ContextWaterMaskTests(unittest.TestCase):
    def test_grid_origin_axis_and_water_classes(self):
        mask = np.array([[0, 1, 255], [1, 0, 0]], dtype=np.uint8)
        np.testing.assert_array_equal(sample_mask(mask, [[10, 20], [12, 20], [14, 20], [10, 18]],
                                                [10, 20], 2), [0, 1, 255, 1])

    def test_outside_never_clamps_to_dry_edge(self):
        mask = np.zeros((3, 3), dtype=np.uint8)
        xy = [[-2, 0], [6, 0], [0, 2], [0, -6], [0, 0]]
        np.testing.assert_array_equal(sample_mask(mask, xy, [0, 0], 2), [255, 255, 255, 255, 0])

    def test_extended_grid_does_not_reuse_old_origin(self):
        # Same retained data shifted two columns by a larger westward context.
        old = np.array([[0, 1, 0]], dtype=np.uint8)
        extended = np.array([[255, 255, 0, 1, 0, 1]], dtype=np.uint8)
        xy = [[100, 20], [102, 20], [104, 20]]
        np.testing.assert_array_equal(sample_mask(old, xy, [100, 20], 2),
                                      sample_mask(extended, xy, [96, 20], 2))
        self.assertEqual(sample_mask(old, [[106, 20]], [100, 20], 2)[0], 255)
        self.assertEqual(sample_mask(extended, [[106, 20]], [96, 20], 2)[0], 1)


if __name__ == '__main__':
    unittest.main(verbosity=2)
