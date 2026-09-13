import sys
import unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from diagnose_liquid_inlet_neighborhood import connected


class InletNeighborhoodTest(unittest.TestCase):
    def test_transitive_connection_not_only_seed_distance(self):
        p=[[0,0,0],[0,0,30],[0,0,60],[0,0,120]]
        np.testing.assert_array_equal(connected(p,0,35),[True,True,True,False])
        np.testing.assert_array_equal(connected(p,3,35),[False,False,False,True])

    def test_shuffling_does_not_change_component(self):
        p=np.array([[0,0,0],[0,0,30],[0,0,60],[0,0,120]])
        order=[3,1,0,2];mask=connected(p[order],2,35)
        self.assertEqual(sorted(np.array(order)[mask].tolist()),[0,1,2])

    def test_invalid_input_rejected(self):
        for p,i,r in [([[np.nan,0,0]],0,35),([[0,0,0]],1,35),([[0,0,0]],0,0),([[0,0,0]],0,np.nan)]:
            with self.assertRaises(ValueError):connected(p,i,r)


if __name__=='__main__':unittest.main()
