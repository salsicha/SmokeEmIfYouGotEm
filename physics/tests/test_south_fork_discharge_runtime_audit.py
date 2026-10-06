import sys
import unittest
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from audit_south_fork_discharge_runtime import preserved_packet


class PreservationTests(unittest.TestCase):
    def setUp(self):
        self.owner = np.array([[1, 2, 3], [4, 5, 6]])
        self.bed = np.full((2, 3), 225.)
        self.mask = np.array([[0, 1, 1], [1, 0, 0]], dtype=np.uint8)
        self.runtime = self.bed - 220
        self.runtime[:, 0] -= 1

    def check(self, mask=None):
        return preserved_packet(self.bed, self.mask, self.owner, self.runtime,
                                self.mask if mask is None else mask, 220)

    def test_only_inferred_owners_may_change(self):
        self.assertEqual(self.check(), (4, 6))
        for row, col in ((0, 1), (0, 2), (1, 1), (1, 2)):
            with self.subTest(owner=self.owner[row, col]):
                self.runtime[row, col] += .001
                with self.assertRaisesRegex(ValueError, 'Registered/protected bed changed'):
                    self.check()
                self.runtime[row, col] = 5

    def test_mask_and_nonfinite_changes_rejected(self):
        changed = self.mask.copy()
        changed[0, 0] = 1
        with self.assertRaisesRegex(ValueError, 'Captured water mask changed'):
            self.check(changed)
        self.runtime[0, 0] = np.nan
        with self.assertRaisesRegex(ValueError, 'Nonfinite runtime bed'):
            self.check()


if __name__ == '__main__':
    unittest.main()
