import unittest
import numpy as np
from qualify_futaleufu_water_resolution import summarize


class ResolutionControlTests(unittest.TestCase):
    def test_native_diagonal_is_not_face_connected(self):
        h=np.eye(3);z=np.zeros_like(h)
        r=summarize(h,z,z,[[.5,.5],[2.5,2.5]],[0,0],1.)
        self.assertFalse(r['connected']);self.assertEqual(r['volume_m3'],3.)
        h[0,:]=1;h[:,-1]=1
        self.assertTrue(summarize(h,z,z,[[.5,.5],[2.5,2.5]],[0,0],1.)['connected'])

    def test_invalid_native_state_is_not_accepted(self):
        z=np.zeros((3,3));h=np.ones_like(z)
        for bad in (-1.,11.,np.nan,np.inf):
            a=h.copy();a[0,0]=bad
            with self.assertRaises(ValueError):summarize(a,z,z,[[.5,.5],[2.5,2.5]],[0,0],1.)
        with self.assertRaises(ValueError):summarize(h,z+21,z,[[.5,.5],[2.5,2.5]],[0,0],1.)


if __name__=='__main__':unittest.main()
