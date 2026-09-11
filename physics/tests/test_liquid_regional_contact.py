import sys
from pathlib import Path
import unittest
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from audit_liquid_regional_contact import compare,query_centres


class RegionalContactAuditTest(unittest.TestCase):
    def setUp(self):
        self.region=dict(id=0,computational_cells=[8,8,8],computational_extents_m=[.08,.08,.08],
            origin_canonical_cm=[0,0,100],axis_x_canonical=[1,0],axis_y_canonical=[0,1])
        self.contact=dict(packed_vectors=[[-100,100,200],[200,1,1],[0,0,0],
            [0,0,104],[200,0,104],[0,-200,104],[200,0,104],[200,-200,104],[0,-200,104]])
        self.values=np.zeros((8,8,8,4),dtype=np.float16)
        self.values[2:4,2:-2,2:-2,3]=1
        self.values[4:6,2:-2,2:-2,3]=2

    def test_exact_solid_empty_classification(self):
        result=compare(self.region,self.contact,self.values)
        self.assertEqual(result['checked_cells'],64)
        self.assertEqual(result['solid_cells'],32)
        self.assertEqual(result['empty_cells'],32)
        self.assertEqual(result['mismatches'],0)

    def test_single_wrong_cell_is_not_hidden_by_averages(self):
        self.values[2,2,2,3]=2
        result=compare(self.region,self.contact,self.values)
        self.assertEqual(result['mismatches'],1)
        self.assertEqual(result['mismatch_examples'][0]['clearance_cm'],-1.5)

    def test_explicit_reflected_rotated_coordinates(self):
        self.region.update(origin_canonical_cm=[100,200,300],axis_x_canonical=[0,1],axis_y_canonical=[-1,0])
        xy,z=query_centres(self.region)
        np.testing.assert_array_equal(xy[0],[98.5,198.5])
        np.testing.assert_array_equal(xy[1],[98.5,199.5])
        np.testing.assert_array_equal(xy[4],[99.5,198.5])
        np.testing.assert_array_equal(z,[302.5,303.5,304.5,305.5])

    def test_nonfinite_or_partial_readback_rejected(self):
        with self.assertRaises(ValueError): compare(self.region,self.contact,self.values[:-1])
        self.values[0,0,0,0]=np.nan
        with self.assertRaises(ValueError): compare(self.region,self.contact,self.values)


if __name__=='__main__': unittest.main()
