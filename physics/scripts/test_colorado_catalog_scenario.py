import unittest
import numpy as np
from build_colorado_catalog_scenario import frame,sample_grid,checked_roughness


class ScenarioFrameTests(unittest.TestCase):
    def test_roughness_sensitivity_is_bounded_and_finite(self):
        self.assertEqual(checked_roughness(.03),.03)
        for value in (0,-.03,.081,float('nan'),float('inf')):
            with self.assertRaises(ValueError):checked_roughness(value)

    def profile(self):
        return dict(samples=[dict(local_arc_station_m=s,easting=100+s,northing=200)
                             for s in range(0,321,16)])

    def test_straight_frame_is_metric_and_left_positive(self):
        s,xy,n,k,source=frame(self.profile())
        np.testing.assert_allclose(np.diff(s),2)
        np.testing.assert_allclose(np.diff(xy,axis=0),np.tile([2,0],(len(s)-1,1)),atol=1e-10)
        np.testing.assert_allclose(n,np.tile([0,1],(len(s),1)),atol=1e-10)
        np.testing.assert_allclose(k,0,atol=1e-10)
        self.assertTrue(np.all(np.diff(source)>0))

    def test_grid_sampling_refuses_extrapolation(self):
        a=np.arange(9).reshape(3,3)
        result=sample_grid(a,np.array([[.5,2.5],[1.5,1.5],[-1,1.5]]),[0,3])
        np.testing.assert_allclose(result[:2],[0,4]);self.assertTrue(np.isnan(result[-1]))

    def test_bad_source_frame_refused(self):
        p=self.profile();p['samples'][1]['local_arc_station_m']=0
        with self.assertRaises(ValueError):frame(p)
        with self.assertRaises(ValueError):frame(self.profile(),smoothing_m=float('nan'))


if __name__=='__main__':unittest.main()
