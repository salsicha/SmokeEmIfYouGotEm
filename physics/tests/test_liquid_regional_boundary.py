import sys
import unittest
from pathlib import Path
import numpy as np

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from audit_liquid_regional_boundary import compare


class RegionalBoundaryTest(unittest.TestCase):
    def setUp(self):
        self.volumes={0:np.zeros((4,8,10,4),dtype='<f2'),1:np.zeros((4,10,8,4),dtype='<f2')}
        self.columns=[(0,1,2,2,0,2),(1,0,3,3,9,7)]
        self.volumes[0][:,2,2,:]=[[1,2,-3,z] for z in range(4)]
        self.volumes[1][:,3,3,:]=[[5,-7,11,z] for z in range(4)]
        self.volumes[1][:,2,0,:]=self.volumes[0][:,2,2,:]
        self.volumes[0][:,7,9,:]=self.volumes[1][:,3,3,:]

    def test_all_components_and_types_preserved(self):
        result=compare(self.volumes,self.columns)
        self.assertEqual(result['checked_cells'],8)
        self.assertEqual(result['mismatches'],0)
        self.volumes[1][2,2,0,1]=-4
        self.assertEqual(compare(self.volumes,self.columns)['mismatches'],1)

    def test_stale_solid_type_rejected(self):
        self.volumes[1][0,2,0,3]=1
        self.assertEqual(compare(self.volumes,self.columns)['mismatches'],1)

    def test_bad_ownership_rejected(self):
        for columns in (self.columns*2,[(0,1,0,0,0,2)],[(0,1,2,2,2,2)]):
            with self.assertRaises(ValueError): compare(self.volumes,columns)

    def test_invalid_data_rejected(self):
        self.volumes[0][0,0,0,0]=np.nan
        with self.assertRaises(ValueError): compare(self.volumes,self.columns)


if __name__=='__main__': unittest.main()
