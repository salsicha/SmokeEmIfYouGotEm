import sys
import unittest
from pathlib import Path
import numpy as np

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from audit_liquid_parent_exterior import compare


class ParentExteriorTest(unittest.TestCase):
    def setUp(self):
        rows=np.zeros((40,3),dtype=np.float32)
        rows[4]=[1,1,1];rows[5]=[4,4,4]
        for f,speed in enumerate([2,-2,3,-3]):
            rows[8+4*f:12+4*f]=[0,2.5,speed]
            rows[24+4*f:28+4*f]=[2,3,0]
        self.parent=dict(packed_vectors=rows.tolist())
        self.region=dict(id=1,cell_bounds_xy=[[2,2],[4,4]],computational_cells=[6,6,4])
        self.boundary=np.zeros((4,6,6,4),dtype='<f2')
        self.pressure=np.zeros((4,6,6),dtype='<f4')
        # Actual parent north and east only, not each region's other local edges.
        for y,x in [(y,x) for y in range(2) for x in range(4)]+[(y,x) for y in range(2,6) for x in (4,5)]:
            self.boundary[:,y,x,3]=3
            self.pressure[:,y,x]=[1960,980,0,0]

    def check(self): return compare(self.region,self.parent,self.boundary,self.pressure)

    def test_parent_outlet_and_region_corners(self):
        r=self.check()
        self.assertEqual(r['outlet_cells'],64)
        self.assertEqual(r['boundary_mismatches'],0)
        self.assertEqual(r['pressure_mismatches'],0)
        self.assertEqual(r['parent_face_columns'],16)

    def test_wrong_pressure_and_outlet_type_detected(self):
        self.pressure[0,0,0]=0
        self.boundary[0,1,1,3]=1
        r=self.check()
        self.assertEqual(r['pressure_mismatches'],1)
        self.assertEqual(r['boundary_mismatches'],1)

    def test_inflow_reflects_lateral_velocity(self):
        region=dict(id=0,cell_bounds_xy=[[0,0],[2,2]],computational_cells=[6,6,4])
        boundary=np.zeros_like(self.boundary)
        for y,x in [(y,x) for y in range(4) for x in (0,1)]+[(y,x) for y in (4,5) for x in range(2,6)]:
            boundary[:2,y,x,:]=[2,-3,0,1]
        r=compare(region,self.parent,boundary,np.zeros_like(self.pressure))
        self.assertEqual(r['inlet_cells'],32)
        self.assertEqual(r['boundary_mismatches'],0)
        boundary[0,0,0,1]=3
        self.assertEqual(compare(region,self.parent,boundary,np.zeros_like(self.pressure))['boundary_mismatches'],1)

    def test_nonfinite_or_truncated_rejected(self):
        with self.assertRaises(ValueError): compare(self.region,self.parent,self.boundary[:,:,:-1],self.pressure)
        self.pressure[0,0,0]=np.nan
        with self.assertRaises(ValueError): self.check()

    def test_internal_reservoir_or_force_detected(self):
        self.boundary[0,2,2,:]=[1,2,3,3]
        self.pressure[0,2,2]=10
        r=self.check()
        self.assertEqual(r['unexpected_outlet_cells'],1)
        self.assertEqual(r['unforced_velocity_cells'],1)
        self.assertEqual(r['unprescribed_pressure_cells'],1)


if __name__=='__main__': unittest.main()
