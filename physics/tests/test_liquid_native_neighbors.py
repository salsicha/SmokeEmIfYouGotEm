import sys
import unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from audit_liquid_native_neighbors import verify_neighbors


class NativeNeighborTest(unittest.TestCase):
    def buffers(self):
        # Sparse source slots, unordered scatter within a cell, signed tags.
        return [np.array(a) for a in ([2,0,2,-1],[8,4,7,0],[-9,3,2,0],
                [1,0,2],[1,1,3],[4,7,8,0],[3,2,-9,0],[[8,-9],[7,2],[4,3]])]

    def test_exact_membership(self):
        self.assertEqual(verify_neighbors(*self.buffers())['particles'],3)

    def test_empty_owner(self):
        self.assertEqual(verify_neighbors([-1],[0],[0],[0],[0],[0],[0],np.empty((0,2)))['particles'],0)

    def test_corrupt_histogram_prefix_or_scatter(self):
        for i in (3,4,5,6):
            b=self.buffers();b[i][0]+=1
            with self.assertRaises(ValueError):verify_neighbors(*b)

    def test_stale_storage(self):
        b=self.buffers()
        for i in (0,1,2,5,6):b[i][:]=0
        with self.assertRaisesRegex(ValueError,'histogram'):verify_neighbors(*b)

    def test_duplicate_or_missing_live_identity(self):
        b=self.buffers();b[-1][0]=b[-1][1]
        with self.assertRaises(ValueError):verify_neighbors(*b)


if __name__=='__main__':unittest.main()
