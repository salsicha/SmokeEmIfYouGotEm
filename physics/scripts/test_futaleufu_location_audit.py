import unittest
import numpy as np
from audit_futaleufu_terminator_location import count_box,bin_centres
import test_futaleufu_imagery as fixtures


class LocationAuditTests(unittest.TestCase):
    def test_sparse_vertices_do_not_erase_interior_river_bins(self):
        bins=np.arange(0.,1000.,100.)
        x,y=bin_centres([0.,1000.],[200.,1200.],[300.,300.],bins)
        np.testing.assert_array_equal(x,bins+250.)
        np.testing.assert_array_equal(y,np.full(10,300.))
        dense=np.arange(0.,1001.,10.)
        dx,dy=bin_centres(dense,dense+200.,np.full(len(dense),300.),bins)
        np.testing.assert_array_equal(x,dx);np.testing.assert_array_equal(y,dy)

    def test_interpolation_keeps_source_bends_instead_of_averaging_vertices(self):
        x,y=bin_centres([0.,100.,200.],[0.,100.,100.],[0.,0.,100.],[0.,100.])
        np.testing.assert_array_equal(x,[50.,100.]);np.testing.assert_array_equal(y,[0.,50.])

    def test_bins_must_be_finite_ordered_and_fully_inside_source_route(self):
        for bins in ([-1.],[950.],[0.,0.],[100.,0.],[float('nan')],[]):
            with self.assertRaises(ValueError):bin_centres([0.,1000.],[0.,1000.],[0.,0.],bins)
        with self.assertRaises(ValueError):bin_centres([0.,0.],[0.,1.],[0.,0.],[0.])

    def setUp(self):
        self.item = fixtures.ImageryTests().item()
        self.valid = np.ones((4, 5), dtype=bool)
        self.water = self.valid.copy()
        self.white = np.zeros((4, 5), dtype=bool)
        self.white[1, 2] = True

    def test_native_grid_not_requested_rectangle(self):
        self.assertEqual(count_box(self.water, self.white, self.valid,
            733165., 5215155., self.item, radius=1), (9, 1, 0))
        self.item['window_utm_m'] = dict(xmin=-1e9, ymax=1e9)
        self.assertEqual(count_box(self.water, self.white, self.valid,
            733165., 5215155., self.item, radius=1), (9, 1, 0))

    def test_partial_box_is_not_counted(self):
        self.assertEqual(count_box(self.water, self.white, self.valid,
            733145., 5215165., self.item, radius=1), (None, None, None))

    def test_nodata_is_not_dry_land(self):
        self.valid[0, 1] = False
        self.assertEqual(count_box(self.water, self.white, self.valid,
            733165., 5215155., self.item, radius=1), (None, None, 1))


if __name__ == '__main__': unittest.main()
