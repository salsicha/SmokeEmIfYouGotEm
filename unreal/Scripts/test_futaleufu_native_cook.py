import unittest
import numpy as np
from prepare_futaleufu_native_cook import discharge_profiles


class NativeCookTests(unittest.TestCase):
    def test_discharge_is_conserved_across_faces_and_oblique_normals(self):
        faces=[dict(depth=np.array([0.,1.,2.]),tangent=[.6,.8],inward=[1.,0.]),
               dict(depth=np.array([3.,.01,0.]),tangent=[.6,.8],inward=[0.,1.])]
        uv,q=discharge_profiles(faces,30.)
        self.assertAlmostEqual(q,30.,places=12)
        self.assertAlmostEqual(sum(float(np.sum(f['depth']*(v@f['inward']))) for f,v in zip(faces,uv)),30.,places=12)
        np.testing.assert_array_equal(uv[0][0],[0.,0.])

    def test_invalid_or_excessive_flow_is_not_clipped(self):
        face=dict(depth=np.ones(3),tangent=[1.,0.],inward=[1.,0.])
        for q in (0.,-1.,np.nan,True,100.):
            with self.assertRaises(ValueError):discharge_profiles([face],q)

    def test_dry_or_outward_profiles_refused(self):
        for depth,tangent in ((np.zeros(3),[1.,0.]),(np.ones(3),[-1.,0.])):
            with self.assertRaises(ValueError):discharge_profiles([dict(depth=depth,tangent=tangent,inward=[1.,0.])],10.)


if __name__=='__main__':unittest.main()
