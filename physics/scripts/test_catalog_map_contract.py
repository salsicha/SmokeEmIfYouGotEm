import unittest
import numpy as np
from build_catalog_map_contract import launch


class CatalogLaunchTests(unittest.TestCase):
    def setUp(self):
        self.mapping = dict(points=[[i*2, 100+i*2, 300, 0, 1] for i in range(20)],
                            world_y_sign=-1, vertical_datum_m=910)
        self.bed = np.full((11,20), 912.)
        self.h = np.full((11,20), 2.)
        self.wet = np.ones((11,20), dtype=bool)
        self.grid = dict(origin_x_m=0, origin_y_m=-10, dx_m=2, dy_m=2)

    def call(self, station=12, lateral=0):
        return launch(self.mapping,self.bed,self.h,self.wet,self.grid,station,lateral)

    def test_launch_uses_geographic_transform_and_vertical_datum(self):
        r = self.call(lateral=2)
        self.assertEqual(r['location_cm'][:2], [11200, -30200])
        self.assertAlmostEqual(r['location_cm'][2], 400-56/3.4)
        self.assertEqual(r['yaw_deg'], 0)

    def test_full_raft_footprint_must_be_wet(self):
        self.wet[3,3] = False
        with self.assertRaises(ValueError): self.call()

    def test_shallow_or_source_edge_launch_refused(self):
        with self.assertRaises(ValueError): self.call(station=2)
        self.h[7,9] = .5
        with self.assertRaises(ValueError): self.call()


if __name__ == '__main__': unittest.main()
