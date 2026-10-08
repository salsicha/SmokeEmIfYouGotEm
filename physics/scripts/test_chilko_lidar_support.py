import unittest
import numpy as np
from chilko_lidar_support import ground_support, summarize_support


class LidarSupport(unittest.TestCase):
    def test_only_unflagged_ground_can_support_terrain(self):
        points=np.array([[0,0,999],[1,0,10],[0,0,999],[0,0,999]],float)
        result=ground_support(points,np.array([1,2,2,12]),np.array([False,False,True,False]),[[0,0]])
        self.assertEqual(result['eligible_ground_points'],1)
        np.testing.assert_array_equal(result['distance_m'],[1])
        np.testing.assert_array_equal(result['nearest_ground_z_m'],[10])

    def test_absent_ground_stays_unsupported(self):
        result=ground_support([[0,0,10]],np.array([1]),np.array([False]),[[0,0]])
        self.assertTrue(np.isinf(result['distance_m']).all())
        stats=summarize_support(result,np.array([10.]),np.array([11.]),np.array([True]))
        self.assertEqual(stats['nearest_ground_distance_threshold_counts']['5.0'],0)
        self.assertNotIn('within_half_metre',stats)

    def test_close_point_summary_does_not_claim_measured_water(self):
        result=ground_support([[.1,0,10],[2,0,12]],np.array([2,2]),np.array([False,False]),[[0,0],[2,0]])
        stats=summarize_support(result,np.array([10.,12.]),np.array([11.,11.]),np.array([True,True]))
        self.assertEqual(stats['within_half_metre']['point_below_inferred_stage_by_over_5cm'],1)
        self.assertEqual(stats['within_half_metre']['point_minus_dem_m'],[0,0,0])
        self.assertFalse(stats['measured_water_level'])
        self.assertFalse(stats['terrain_modified'])

    def test_invalid_frames_and_missing_flags_refused(self):
        with self.assertRaises(ValueError):
            ground_support([[0,0,float('nan')]],np.array([2]),np.array([False]),[[0,0]])
        with self.assertRaises(ValueError):
            ground_support([[0,0,1]],np.array([2]),np.array([0]),[[0,0]])


if __name__=='__main__':unittest.main()
