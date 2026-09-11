import sys
import unittest
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from audit_liquid_particle_handles import verify_handles


class NativeHandlesTest(unittest.TestCase):
    def setUp(self):
        self.words = np.array([[1, 0, 0, 0], [17, 0, 23, 0]], dtype='<u4')
        self.refs = np.array([[0, 0], [0xffffffff, 0xffffffff], [0, 1], [0xffffffff, 0xffffffff]], dtype='<u4')
        self.handles = np.array([[1, 17], [0xffffffff, 0xffffffff], [0, 0x80000001], [0xffffffff, 0xffffffff]], dtype='<u4')
        self.table = np.array([0xffffffff, 0, 0, 0xffffffff], dtype='<u4')
        self.free = np.array([0, 0xffffffff, 1, 0xffffffff], dtype='<u4')
        self.counts = np.array([1, 1], dtype='<u4')

    def check(self):
        return verify_handles([2, 2], self.counts, self.words, self.refs, self.handles,
                              self.table, self.free, self.counts, 0, 1)

    def test_stayer_preserved_import_rekeyed_and_free_list_complete(self):
        self.assertEqual(self.check()['staying_handles_unchanged'], 1)
        self.assertEqual(self.check()['imported_handles'], 1)

    def test_staying_or_imported_tag_change_rejected(self):
        self.handles[0, 1] = 18
        with self.assertRaises(ValueError): self.check()
        self.handles[0, 1] = 17;self.handles[2, 1] = 23
        with self.assertRaises(ValueError): self.check()

    def test_live_id_in_free_list_and_bad_lookup_rejected(self):
        self.free[0] = 1
        with self.assertRaises(ValueError): self.check()
        self.free[0] = 0;self.table[1] = 1
        with self.assertRaises(ValueError): self.check()

    def test_native_id_namespace_can_exceed_particle_storage(self):
        self.words[0, 0] = self.handles[0, 0] = 3
        table = np.array([0xffffffff, 0xffffffff, 0xffffffff, 0, 0, 0xffffffff, 0xffffffff, 0xffffffff], dtype='<u4')
        free = np.array([0, 1, 2, 0xffffffff, 1, 2, 3, 0xffffffff], dtype='<u4')
        free_counts = np.array([3, 3], dtype='<u4')
        result = verify_handles([2, 2], self.counts, self.words, self.refs, self.handles,
                                table, free, free_counts, 0, 1, [4, 4])
        self.assertEqual(result['staying_handles_unchanged'], 1)
        with self.assertRaises(ValueError):
            verify_handles([2, 2], self.counts, self.words, self.refs, self.handles,
                           table, free, free_counts, 0, 1, [2, 2])


if __name__ == '__main__': unittest.main()
