import sys
import unittest
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from audit_liquid_particle_identity import compare_identity_sets


class NativeIdentityTest(unittest.TestCase):
    def setUp(self):
        self.birth = {0: np.array([[0, 16777217, 16777217, 7],
                                   [0, -2147483648, -2147483648, 3]], dtype='<i4'),
                      1: np.array([[1, 16777217, 16777217, 7]], dtype='<i4')}

    def test_int32_identity_survives_reordering_and_recycled_local_ids(self):
        current = {k: v[::-1].copy() for k, v in self.birth.items()}
        current[0][:, 3] = [1, 0]
        result = compare_identity_sets(self.birth, current)
        self.assertEqual(result['distinct_particles'], 3)
        self.assertFalse(result['particle_handoff_verified'])

    def test_birth_owner_not_rewritten_at_new_owner(self):
        current = {0: self.birth[0][:1], 1: np.concatenate([self.birth[1], self.birth[0][1:]])}
        self.assertEqual(compare_identity_sets(self.birth, current)['observed_owner_changes'], 1)

    def test_duplicate_or_lost_identity_rejected(self):
        with self.assertRaises(ValueError): compare_identity_sets(self.birth, {0: self.birth[0]})
        with self.assertRaises(ValueError):
            compare_identity_sets(self.birth, {0: np.concatenate([self.birth[0], self.birth[0]]), 1: self.birth[1]})

    def test_float_ids_and_native_birth_mismatch_rejected(self):
        with self.assertRaises(ValueError):
            compare_identity_sets({0: self.birth[0].astype('f4')}, {0: self.birth[0]})
        invalid = {k: v.copy() for k, v in self.birth.items()}
        invalid[0][0, 2] = 0
        with self.assertRaises(ValueError): compare_identity_sets(invalid, self.birth)


if __name__ == '__main__': unittest.main()
