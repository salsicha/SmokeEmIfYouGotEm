import sys
import unittest
from pathlib import Path
import numpy as np

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from audit_liquid_regional_pressure_marker import compare,expected_marker


class RegionalPressureMarkerTest(unittest.TestCase):
    def setUp(self):
        self.region=dict(id=5,computational_cells=[10,8,6],cell_bounds_xy=[[4,0],[10,4]])
        self.boundary=dict(shared_halo_columns=[[x,y,1,2,2] for x in (0,1) for y in range(2,6)])
        self.parent=[14,10,6]
        self.values,self.color,self.shared=expected_marker(self.region,self.boundary,self.parent)

    def check(self,values):
        return compare(self.region,self.boundary,self.parent,values)

    def test_exact_and_single_corruption(self):
        self.assertEqual(self.check(self.values)['mismatches'],0)
        bad=self.values.copy();bad[2,3,1]=0
        self.assertEqual(self.check(bad)['mismatches'],1)

    def test_zero_only_cannot_pass(self):
        self.assertGreater(self.check(np.zeros_like(self.values))['mismatches'],0)

    def test_opposite_local_phase_rejected(self):
        z,y,x=np.indices(self.values.shape)
        bad=np.full(self.values.shape,1005,dtype=np.float32)
        bad[((x//2+y//2+z//2)%2==0)&~self.shared[None,:,:]]=0
        self.assertGreater(self.check(bad)['mismatches'],0)

    def test_nonfinite_or_partial_rejected(self):
        bad=self.values.copy();bad[0,0,0]=np.nan
        with self.assertRaises(ValueError): self.check(bad)
        with self.assertRaises(ValueError): self.check(self.values[:,:,:-1])


if __name__=='__main__': unittest.main()
