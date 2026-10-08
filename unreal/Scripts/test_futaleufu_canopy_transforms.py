import math
import unittest

from futaleufu_canopy_transforms import transform_row


class CanopyTransforms(unittest.TestCase):
    bounds = dict(min=[-400, -300, -5], max=[400, 300, 995])

    def test_tree_uses_native_ground_and_bottom_pivot(self):
        result = transform_row([10,20,99999,4,20,0,1,40], self.bounds, 500)
        self.assertEqual(result['scale'], [1,1,1.8])
        self.assertEqual(result['location_cm'], [10,20,479])
        self.assertEqual(result['root_cm'], 470)
        self.assertEqual(result['yaw_degrees'], 40)

    def test_tree_lower_clamp_and_form_b(self):
        result = transform_row([10,20,-900,4,1,1,1,0], self.bounds, -50)
        self.assertEqual(result['scale'], [1,1,.8])
        self.assertEqual(result['location_cm'][2]+self.bounds['min'][2]*.8, -80)

    def test_shrub_has_no_tree_height_clamp(self):
        result = transform_row([10,20,3,4,95], self.bounds, 500, understory=True)
        self.assertEqual(result['scale'], [.5,.5,.3])
        self.assertEqual(result['location_cm'], [10,20,481.5])

    def test_reject_invalid_rows(self):
        for row in ([10,20,0,4,20,2,1,0], [10,20,0,4,20,0,0,0],
                    [10,20,0,-4,20,0,1,0], [10,20,0,4,20,0,1,math.nan], [0]*7):
            with self.assertRaises(ValueError):
                transform_row(row, self.bounds, 0)

    def test_reject_implicit_mesh_scale_and_bad_ground(self):
        row = [10,20,0,4,20,0,1,0]
        for bounds, ground in ((dict(min=[0,0,0],max=[1,1,1]), 0), (self.bounds, math.inf)):
            with self.assertRaises(ValueError):
                transform_row(row, bounds, ground)


if __name__ == '__main__':
    unittest.main()
