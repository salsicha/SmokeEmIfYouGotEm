import sys
import unittest
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from audit_liquid_native_emission import verify_birth_growth


class NativeEmissionTest(unittest.TestCase):
    def setUp(self):
        def sample(keys):
            out = {o: np.empty((3, 0), dtype='<u4') for o in range(12)}
            for owner, rows in keys.items():
                out[owner] = np.asarray([[b, n, n] for b, n in rows], dtype='<u4').T
            return out
        self.samples = [(1, sample({1: [(1, 16777217)]})),
                        (2, sample({0: [(1, 16777217)], 1: [(1, 16777218)]})),
                        (3, sample({0: [(1, 16777217), (1, 16777218)], 1: [(1, 16777219)]}))]
        self.planned = {s: {1: 1} for s in (1, 2, 3)}

    def check(self):
        return verify_birth_growth(self.samples, self.planned, [0, 1], 2)

    def test_native_births_can_migrate_without_losing_identity(self):
        self.assertEqual(self.check(), dict(initial_particles=1, verified_new_births=2, particles=3))

    def test_lost_particle_is_not_explained_by_new_birth(self):
        self.samples[2][1][0] = self.samples[2][1][0][:, 1:]
        with self.assertRaises(ValueError): self.check()

    def test_configured_source_is_not_proof_of_native_birth(self):
        self.planned[2][1] = 2
        with self.assertRaises(ValueError): self.check()

    def test_relabelled_sequence_and_wrong_birth_owner_rejected(self):
        self.samples[2][1][1][2, 0] += 1
        with self.assertRaises(ValueError): self.check()

    def test_duplicate_particle_rejected(self):
        self.samples[2][1][2] = self.samples[2][1][1].copy()
        with self.assertRaises(ValueError): self.check()


if __name__ == '__main__': unittest.main()
