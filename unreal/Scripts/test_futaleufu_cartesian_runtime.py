import unittest
import numpy as np
from export_futaleufu_cartesian_runtime import intersections


class RuntimePacketTests(unittest.TestCase):
    def test_shared_tile_rows_are_not_transposed_or_shifted(self):
        tiles = np.arange(18).reshape(6, 3)
        packet = np.full((4, 5), -1)
        for _, dest, src in intersections([1.5, .5], packet.shape, [[.5, .5], [3.5, .5]], 3):
            packet[dest] = tiles[src]
        np.testing.assert_array_equal(packet[:3], np.c_[tiles[:3, 1:], tiles[3:]])
        np.testing.assert_array_equal(packet[3], [-1]*5)

    def test_negative_offset_crops_correct_native_tile_rows(self):
        rows = intersections([.5, 1.5], (2, 2), [[-.5, -.5]], 3)
        self.assertEqual(len(rows), 1)
        a = np.arange(9).reshape(3, 3)
        np.testing.assert_array_equal(a[rows[0][2]], [[7, 8]])

    def test_half_cell_misalignment_rejected(self):
        with self.assertRaises(ValueError): intersections([0., 0.], (4, 4), [[.5, .5]], 3)


if __name__ == '__main__': unittest.main()
