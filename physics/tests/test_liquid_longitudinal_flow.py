import sys
from pathlib import Path
import unittest
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from analyze_liquid_longitudinal_flow import top_crossings


class LongitudinalFlowTest(unittest.TestCase):
    def test_uses_highest_crossing_and_exact_interpolation(self):
        surface=np.zeros((6,2,3,4))
        surface[...,0]=np.array([-1,1,1,-3,1,2])[:,None,None]
        points=top_crossings(surface)
        self.assertEqual(len(points),6)
        np.testing.assert_allclose(points[:,2],4.25/6)
        np.testing.assert_allclose(np.unique(points[:,0]),[1/6,.5,5/6])

    def test_dry_and_submerged_columns_have_no_crossing(self):
        surface=np.ones((4,2,2,4));surface[:,0,0,0]=-1
        self.assertEqual(top_crossings(surface).shape,(0,3))

    def test_nonfinite_surface_rejected(self):
        surface=np.zeros((4,2,2,4));surface[0,0,0,0]=np.nan
        with self.assertRaises(ValueError):top_crossings(surface)


if __name__=='__main__':unittest.main()
