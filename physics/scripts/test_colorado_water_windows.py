import unittest
from shapely.geometry import Polygon, box
from extract_colorado_water_windows import width_observation, valid_polygon


class WaterWidths(unittest.TestCase):
    def test_straight_channel(self):
        result=width_observation(box(-100,-20,100,20),0,0,1,0)
        self.assertEqual(result['center_channel_width_m'],40)
        self.assertEqual(result['classified_water_intervals_lateral_m'],[[-20,20]])

    def test_island_is_not_a_continuous_navigable_width(self):
        water=Polygon([(-100,-20),(100,-20),(100,20),(-100,20)],
                      [[(-5,-4),(-5,4),(5,4),(5,-4)]])
        result=width_observation(water,0,0,1,0)
        self.assertFalse(result['center_in_classified_water'])
        self.assertIsNone(result['center_channel_width_m'])
        self.assertEqual(result['total_classified_water_width_m'],32)
        self.assertEqual(result['classified_water_intervals_lateral_m'],[[-20,-4],[4,20]])

    def test_truncated_channel_refuses_width(self):
        result=width_observation(box(-1000,-1000,1000,1000),0,0,1,0)
        self.assertTrue(result['transect_truncated'])
        self.assertIsNone(result['center_channel_width_m'])

    def test_degenerate_tangent_refused(self):
        with self.assertRaises(ValueError): width_observation(box(0,0,1,1),0,0,0,0)

    def test_area_changing_repair_is_refused(self):
        bowtie=Polygon([(0,0),(2,2),(0,2),(2,0)])
        with self.assertRaises(ValueError): valid_polygon(bowtie)

    def test_valid_island_not_repaired(self):
        water=box(0,0,10,10).difference(box(4,4,6,6))
        fixed,receipt=valid_polygon(water)
        self.assertIsNone(receipt)
        self.assertTrue(fixed.equals(water))


if __name__=='__main__': unittest.main()
