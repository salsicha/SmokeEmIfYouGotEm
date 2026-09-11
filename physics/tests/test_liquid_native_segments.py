import sys
import unittest
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from audit_liquid_native_segments import verify_origins


class NativeSegmentsTest(unittest.TestCase):
    def setUp(self):
        self.before = {0: np.zeros((8, 2), dtype='<u4'), 1: np.zeros((8, 0), dtype='<u4')}
        self.before[0][0:3] = np.array([[1, 2], [3, 4], [5, 6]], dtype='<f4').view('<u4')
        self.before[0][6:] = [[1, 1], [0, 1]]
        self.after = {o: w.copy() for o, w in self.before.items()}
        self.after[0][3:6] = self.before[0][0:3]
        self.after[0][0:3] = (self.before[0][0:3].view('<f4')+1).view('<u4')

    def verify(self):
        return verify_origins(self.before, self.after, [6, 7], 0, 3, 6)

    def test_actual_origins_survive_compaction_and_new_births(self):
        self.after[0] = self.after[0][:, ::-1].copy()
        newborn = np.zeros((8, 1), dtype='<u4');newborn[6:, 0] = [1, 2]
        self.after[1] = newborn
        self.assertEqual(self.verify(), dict(verified_segments=2, moving_segments=2))

    def test_stale_origin_rejected(self):
        self.after[0][3:6, 0] = 0
        with self.assertRaisesRegex(ValueError, 'actual previous'):
            self.verify()

    def test_current_position_cannot_masquerade_as_origin(self):
        self.after[0][3:6] = self.after[0][0:3]
        with self.assertRaisesRegex(ValueError, 'actual previous'):
            self.verify()

    def test_lost_and_duplicated_particles_rejected(self):
        self.after[0] = self.after[0][:, :1]
        with self.assertRaisesRegex(ValueError, 'missing'):
            self.verify()
        self.after[1] = self.after[0].copy()
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            self.verify()

    def test_nonfinite_origin_rejected(self):
        self.after[0][3, 0] = np.array(np.nan, dtype='<f4').view('<u4')
        with self.assertRaisesRegex(ValueError, 'Nonfinite'):
            self.verify()

    def test_wrong_owner_and_aliased_layout_rejected(self):
        self.after[1], self.after[0] = self.after[0], self.after[1]
        with self.assertRaisesRegex(ValueError, 'ownership'):
            self.verify()
        with self.assertRaisesRegex(ValueError, 'distinct'):
            verify_origins(self.before, self.after, [6, 7], 0, 0, 6)


if __name__ == '__main__':
    unittest.main()
