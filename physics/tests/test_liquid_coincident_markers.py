import sys
from pathlib import Path
import unittest
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from diagnose_liquid_coincident_markers import duplicate_groups


class CoincidentMarkersTest(unittest.TestCase):
    def test_only_exact_positions_grouped_and_indices_preserved(self):
        p=np.array([[1.,2,3],[3,2,1],[1,2,3.0000001],[1,2,3],[3,2,1],[1,2,3]])
        groups=duplicate_groups(p)
        self.assertEqual([g.tolist() for g in groups],[[0,3,5],[1,4]])
        self.assertEqual(len(p),6)

    def test_no_groups_empty_or_separate(self):
        self.assertEqual(duplicate_groups(np.empty((0,3))),[])
        self.assertEqual(duplicate_groups(np.eye(3)),[])
        with self.assertRaises(ValueError):duplicate_groups([[1,2,np.nan]])


if __name__=='__main__':unittest.main()
