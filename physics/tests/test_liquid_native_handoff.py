import sys
import unittest
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from audit_liquid_native_handoff import compare_native_steps, verify_empty_receiver


class NativeHandoffTest(unittest.TestCase):
    def setUp(self):
        # Planes: xyz, birth owner/sequence, local index/tag.
        self.before = {0: np.array([[10], [20], [30], [0], [16777217], [2], [8]], dtype='<u4'),
                       1: np.empty((7, 0), dtype='<u4')}
        self.after = {0: np.empty((7, 0), dtype='<u4'), 1: self.before[0].copy()}
        self.after[1][5:, 0] = [4, 0x80000001]
        self.later = {k: v.copy() for k, v in self.after.items()}
        self.later[1][0, 0] = 11

    def check(self):
        return compare_native_steps(self.before, self.after, self.later, [3, 4], [5, 6], [0, 1, 2])

    def test_real_owner_change_and_following_motion(self):
        result = self.check()
        self.assertTrue(result['bounded_native_handoff_verified'])
        self.assertEqual(result['native_owner_changes'], 1)

    def test_missing_or_duplicated_native_particle_rejected(self):
        self.later[1] = np.empty((7, 0), dtype='<u4')
        with self.assertRaises(ValueError): self.check()
        self.later[1] = np.repeat(self.after[1], 2, axis=1)
        with self.assertRaises(ValueError): self.check()

    def test_staging_only_or_changed_local_handle_rejected(self):
        self.later[1][5, 0] = 5
        with self.assertRaises(ValueError): self.check()
        with self.assertRaises(ValueError):
            compare_native_steps(self.before, self.before, self.before, [3, 4], [5, 6], [0, 1, 2])

    def test_subsequent_commit_can_retain_owners_but_must_preserve_motion(self):
        result = compare_native_steps(self.after, self.after, self.later, [3, 4], [5, 6], [0, 1, 2],
                                      require_change=False)
        self.assertEqual(result['native_owner_changes'], 0)
        self.assertEqual(result['particles_moving_on_following_step'], 1)
        with self.assertRaises(ValueError):
            compare_native_steps(self.after, self.after, self.after, [3, 4], [5, 6], [0, 1, 2],
                                 require_change=False)

    def test_subsequent_commit_cannot_hide_lost_particle_or_changed_receiving_handle(self):
        self.later[1][6, 0] += 1
        with self.assertRaises(ValueError):
            compare_native_steps(self.after, self.after, self.later, [3, 4], [5, 6], [0, 1, 2],
                                 require_change=False)

    def test_actual_empty_receiver_requires_empty_birth_and_conserved_particles(self):
        records = [dict(region_id=i, birth_particle_count=1 if i in (1, 4, 5) else 0,
                        expected_count=1 if i in (1, 4, 5) else 0) for i in range(12)]
        before = {i: np.zeros((7, r['birth_particle_count']), dtype='<u4') for i, r in enumerate(records)}
        later = {i: np.zeros((7, 3 if i == 0 else 0), dtype='<u4') for i in range(12)}
        self.assertEqual(verify_empty_receiver(records, before, later, 1)['received_particles'], 3)
        records[0]['birth_particle_count'] = 1
        with self.assertRaises(ValueError): verify_empty_receiver(records, before, later, 1)
        records[0]['birth_particle_count'] = 0
        before[0] = np.zeros((7, 1), dtype='<u4')
        with self.assertRaises(ValueError): verify_empty_receiver(records, before, later, 1)
        before[0] = np.zeros((7, 0), dtype='<u4')
        later[0] = np.zeros((7, 2), dtype='<u4')
        with self.assertRaises(ValueError): verify_empty_receiver(records, before, later, 1)


if __name__ == '__main__': unittest.main()
