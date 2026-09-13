import sys
from pathlib import Path
import unittest
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from liquid_bed_contour_intervals import quadratic_roots,bed_contour_intervals


class BedContourIntervalsTest(unittest.TestCase):
    def test_stable_quadratic_linear_and_double_roots(self):
        a=np.array([1.,0,1,1,0]);b=np.array([-1e10,2,0,0,0]);c=np.array([1.,-1,0,1,0])
        r=quadratic_roots(a,b,c)
        np.testing.assert_allclose(np.sort(r[0]),[1e-10,1e10],rtol=1e-15)
        self.assertEqual(r[1,0],.5);np.testing.assert_array_equal(r[2],[0,0])
        self.assertTrue(np.isinf(r[3:]).all())

    def test_linear_surface_contacts_are_explicit_boundaries(self):
        # phi=z-y; fixed bed at .37 intersects the surface at ray y=.37.
        z=np.array([0.,1.,2.]);a=z[None,:];b=a-1
        parent,lo,hi=bed_contour_intervals(a,b,z,np.array([.37]),np.array([.37]))
        self.assertTrue(np.any(lo==.37));self.assertAlmostEqual((hi-lo).sum(),1)
        self.assertTrue((parent==0).all())

    def test_two_bed_contacts_inside_one_vertical_slab(self):
        # phi(t,bed(t))=(t-.2)(t-.8), with bed=t and phi=z*t-t+.16.
        a=np.array([[.16,.16]]);b=np.array([[-.84,.16]])
        parent,lo,hi=bed_contour_intervals(a,b,[0,1],np.array([0.]),np.array([1.]))
        self.assertTrue(np.any(abs(lo-.2)<1e-14));self.assertTrue(np.any(abs(lo-.8)<1e-14))
        self.assertAlmostEqual((hi-lo).sum(),1)
        mid=(lo+hi)/2
        # Every returned open interval has constant contact sign.
        for f in (.001,.999):
            q=lo+f*(hi-lo)
            np.testing.assert_array_equal((q-.2)*(q-.8)<0,(mid-.2)*(mid-.8)<0)

    def test_bed_crosses_z_levels_without_surface_modification(self):
        left=np.array([[-1.,-.5,1.]]);right=left.copy()
        _,lo,hi=bed_contour_intervals(left,right,[0,1,2],np.array([-.2]),np.array([2.3]))
        self.assertTrue(np.any(abs(lo-.48)<1e-14));self.assertAlmostEqual((hi-lo).sum(),1)
        np.testing.assert_array_equal(left,right)


if __name__=='__main__':unittest.main()
