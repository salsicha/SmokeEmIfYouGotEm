"""Do not turn sparse returns into invented barriers across real channels."""
from pathlib import Path
import runpy
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tmp/south-fork-geospatial-deps'))
import numpy as np

repair = runpy.run_path(str(ROOT / 'physics/scripts/repair_captured_rock_gaps.py'))['repair_gaps']


class CapturedRockGapTests(unittest.TestCase):
    def fixture(self):
        authority = np.full((9, 9), 2, dtype=np.uint8)
        authority[2:7, 2:7] = 3
        bed = np.where(authority == 3, 8., 4.).astype(np.float32)
        authority[4, 4] = 2
        bed[4, 4] = 4.
        return bed, authority

    def test_enclosed_pixel_is_inferred_without_changing_measured_rock(self):
        bed, authority = self.fixture()
        result, tags, stats = repair(bed, authority, .5)
        self.assertEqual(result[4, 4], 8.)
        self.assertEqual(tags[4, 4], 4)
        self.assertEqual(stats['filled_cells'], 1)
        self.assertTrue(np.array_equal(result[authority == 3], bed[authority == 3]))
        self.assertEqual(authority[4, 4], 2)  # no in-place source mutation

    def test_diagonal_connection_is_open_not_a_hole(self):
        bed, authority = self.fixture()
        authority[2, 2] = authority[3, 3] = 2
        result, tags, stats = repair(bed, authority, .5)
        self.assertEqual(stats['filled_cells'], 0)
        self.assertTrue(np.array_equal(result, bed))

    def test_large_gap_and_dry_ground_are_not_filled(self):
        bed, authority = self.fixture()
        authority[3:6, 3:6] = 2
        self.assertEqual(repair(bed, authority, .5)[2]['filled_cells'], 0)
        bed, authority = self.fixture()
        authority[4, 4] = 1
        self.assertEqual(repair(bed, authority, .5)[2]['filled_cells'], 0)

    def test_high_relief_rim_is_not_bridged(self):
        bed, authority = self.fixture()
        bed[3, 4] = 10.
        self.assertEqual(repair(bed, authority, .5)[2]['filled_cells'], 0)

    def test_invalid_inputs_fail_closed(self):
        bed, authority = self.fixture()
        for cell in (0, -1, float('nan')):
            with self.assertRaises(ValueError): repair(bed, authority, cell)
        bed[0, 0] = np.nan
        with self.assertRaises(ValueError): repair(bed, authority, .5)


if __name__ == '__main__':
    unittest.main()
