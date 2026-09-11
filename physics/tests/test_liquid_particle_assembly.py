import sys
import unittest
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from audit_liquid_particle_assembly import verify_assembly


class NativeAssemblyTest(unittest.TestCase):
    def setUp(self):
        self.sources = {0: np.array([[0x80000000, 0x7fc01234], [16777217, 0xffffffff]], dtype='<u4'),
                        1: np.array([[0, 0], [0, 0]], dtype='<u4')}
        self.routes = {0: np.array([[1, 0, 0, 1], [0, 0, 1, 1]], dtype='<u4'),
                       1: np.empty((0, 4), dtype='<u4')}
        self.words = np.zeros((2, 4), dtype='<u4')
        self.words[:, 0] = self.sources[0][:, 1]
        self.words[:, 2] = self.sources[0][:, 0]
        self.refs = np.array([[0, 1], [0xffffffff, 0xffffffff], [0, 0], [0xffffffff, 0xffffffff]], dtype='<u4')
        self.counts = np.array([1, 1], dtype='<u4')
        self.control = np.array([1, 0, 2, 0], dtype='<u4')

    def check(self):
        return verify_assembly(self.sources, self.routes, [2, 2], self.words, self.refs, self.counts, self.control)

    def test_exact_all_word_planes_into_previously_empty_owner(self):
        result = self.check()
        self.assertEqual(result['assembled_particles'], 2)
        self.assertEqual(result['cross_owner_particles'], 1)
        self.assertFalse(result['native_particle_handoff_verified'])

    def test_dropped_duplicated_and_wrong_owner_rejected(self):
        self.counts[1] = 0
        with self.assertRaises(ValueError): self.check()
        self.counts[1] = 1
        self.refs[2] = self.refs[0]
        with self.assertRaises(ValueError): self.check()
        self.refs[[0, 2]] = [[0, 0], [0, 1]]
        with self.assertRaises(ValueError): self.check()

    def test_payload_bit_change_and_stale_tail_rejected(self):
        self.words[0, 2] ^= 1
        with self.assertRaises(ValueError): self.check()
        self.words[0, 2] ^= 1
        self.words[0, 3] = 1
        with self.assertRaises(ValueError): self.check()

    def test_failed_gpu_transaction_not_accepted(self):
        self.control[0] = 0;self.control[1] = 4
        with self.assertRaises(ValueError): self.check()


if __name__ == '__main__': unittest.main()
