import unittest
import numpy as np
from build_colorado_catalog_scenario import frame,sample_grid,checked_roughness,registered_rapid_station,covered_source_slice


class ScenarioFrameTests(unittest.TestCase):
    def test_coverage_trims_only_exterior_halo_and_preserves_complete_core(self):
        take=covered_source_slice([False,True,True,True,False],[8000,8200,8400,8600,8800],[8200,8600])
        self.assertEqual((take.start,take.stop),(1,4))
        with self.assertRaisesRegex(ValueError,'complete required core'):
            covered_source_slice([False,True,True,True,False],[8000,8200,8400,8600,8800],[8100,8600])
        with self.assertRaisesRegex(ValueError,'complete required core'):
            covered_source_slice([False,True,True,True,False],[8000,8200,8400,8600,8800],[8200,8700])

    def test_internal_coverage_gap_reports_source_interval_and_never_bridges(self):
        with self.assertRaisesRegex(ValueError,'between 9225.000 and 9373.000'):
            covered_source_slice([True,False,False,True],[9200,9225,9373,9400],[9200,9400])
        with self.assertRaisesRegex(ValueError,'No completely source-backed'):
            covered_source_slice([False,False],[0,2])

    def test_coverage_rejects_invalid_axes_and_core_bounds(self):
        for axis in ([0,0],[2,0],[0,float('nan')],[0],[[0,2]]):
            with self.assertRaises(ValueError):covered_source_slice([True,True],axis)
        for core in ([2,0],[0,float('inf')],[0]):
            with self.assertRaises(ValueError):covered_source_slice([True,True],[0,2],core)

    def test_continuous_tile_does_not_invent_a_rapid_point(self):
        p=dict(schema='raftsim.colorado_continuous_source_window.v1',rapid_point_local_station_m=None)
        self.assertIsNone(registered_rapid_station(p,[0,100],[0,98]))
        with self.assertRaises(ValueError):registered_rapid_station({},[0,100],[0,98])
        with self.assertRaises(ValueError):
            registered_rapid_station(dict(rapid_point_local_station_m=101),[0,100],[0,98])
        self.assertEqual(registered_rapid_station(dict(rapid_point_local_station_m=50),[0,100],[0,98]),49)

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
