import sys
from pathlib import Path
import unittest
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from audit_liquid_ray_hits import compare,camera_rays


class RayHitTest(unittest.TestCase):
    def plane(self,scale=1):
        phi=np.broadcast_to((np.arange(32)+.5)[:,None,None]/32-.5,(32,4,4))*scale
        return compare(phi,np.array([.5,.5,2.]),np.array([[.001,.001,-1.]])/np.sqrt(1.000002),
                       np.zeros(3),np.ones(3),.01)

    def test_true_distance_plane(self):
        report,old,reference=self.plane()
        self.assertEqual(report['inherited_missed_hits'],0)
        self.assertAlmostEqual(old[0],reference[0],delta=.002)

    def test_nonconservative_plane_can_be_missed(self):
        report,old,reference=self.plane(3)
        self.assertEqual(report['dense_first_hits'],1)
        self.assertTrue(np.isfinite(reference[0]))
        self.assertTrue(np.isnan(old[0]))

    def test_camera_and_invalid_step(self):
        origin,rays=camera_rays(3,3)
        np.testing.assert_allclose(np.linalg.norm(rays,axis=1),1)
        expected=np.array([0,0,2.5])-origin;expected/=np.linalg.norm(expected)
        np.testing.assert_allclose(rays[4],expected)
        with self.assertRaises(ValueError):
            compare(np.zeros((2,2,2)),origin,rays,np.zeros(3),np.ones(3),0)


if __name__=='__main__':unittest.main()
