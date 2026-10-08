import unittest

import numpy as np
import shapely

from futaleufu_corridor_bed import FutaleufuBed, NAMES, initial_cut, source_heights
from chilko_triangle_ownership import preserve_triangle_support


def fixture():
    bed = FutaleufuBed.__new__(FutaleufuBed)
    bed.grid = np.full((101, 101), 12.)
    bed.transform = [10, 0, -505, 0, -10, 505]
    bed.lines = [shapely.LineString([(0, 100), (0, 0)]),
                 shapely.LineString([(-100, 0), (0, 0)]),
                 shapely.LineString([(0, 0), (100, 0)])]
    bed.junction = np.array([0., 0.])
    bed.arrays = {n: dict(station_m=np.array([0., 50., 100.]),
                         stage_m=np.array([11., 10.5, 10.]) if i < 2 else np.array([10., 9.5, 9.]),
                         left_m=np.full(3, -10.), right_m=np.full(3, 10.))
                  for i, n in enumerate(NAMES)}
    bed.islands = shapely.box(35, -3, 45, 3)
    bed.polygon = shapely.difference(shapely.box(-110, -10, 110, 10), bed.islands)
    bed.parameters = dict(depth_m=1.8, bank_taper_m=5., max_cut_m=25.)
    return bed


class BedTests(unittest.TestCase):
    def test_pixel_centres_and_half_cells(self):
        grid = np.array([[0., 10.], [20., 30.]])
        t = [10, 0, 0, 0, -10, 20]
        np.testing.assert_equal(source_heights([[5, 15], [10, 10], [15, 5]], grid, t), [0, 15, 30])

    def test_no_extrapolation(self):
        for xy in ([[-.001, 0]], [[0, 10.001]], [[np.nan, 0]]):
            with self.assertRaises(ValueError):
                source_heights(xy, np.zeros((2, 2)), [10, 0, -5, 0, -10, 15])

    def test_cuts_only_owned_never_raises(self):
        result = initial_cut([20., 20., 0., 20.], [10.]*4, [True, False, True, True],
                             [10., 10., 10., 0.], [20.]*4,
                             depth_m=2, bank_taper_m=5, max_cut_m=25)
        np.testing.assert_equal(result['height_m'], [8, 20, 0, 20])

    def test_cut_limit_reported_not_hidden(self):
        result = initial_cut([100.], [10.], [True], [10.], [20.],
                             depth_m=2, bank_taper_m=5, max_cut_m=25)
        self.assertEqual(result['height_m'][0], 75)
        self.assertTrue(result['cut_limit_reached'][0])
        self.assertTrue(result['unresolved_above_stage'][0])

    def test_bounds_rejected(self):
        for key, value in [('depth_m', 0), ('depth_m', 11), ('max_cut_m', 26),
                           ('bank_taper_m', 0), ('depth_m', np.nan)]:
            p = dict(depth_m=2, bank_taper_m=5, max_cut_m=25); p[key] = value
            with self.assertRaises(ValueError):
                initial_cut([20.], [10.], [True], [10.], [20.], **p)

    def test_islands_banks_and_endcaps_unchanged(self):
        bed = fixture()
        result = bed.sample([[40, 0], [40, 3], [50, 11], [105, 0], [0, 105]])
        np.testing.assert_equal(result['height_m'], [12]*5)
        self.assertFalse(result['bed_owned'].any())

    def test_azul_explicitly_inferred(self):
        result = fixture().sample([[0, 70], [70, 0]])
        np.testing.assert_equal(result['inferred_planform'], [True, False])
        np.testing.assert_equal(result['mapped_water'], [False, True])
        self.assertTrue(result['inferred_bed'].all())

    def test_junction_common_stage_and_nearby_continuity(self):
        result = fixture().sample([[0, 0], [1e-5, 0], [-1e-5, 0], [0, 1e-5]])
        self.assertEqual(result['reference_m'][0], 10.)
        self.assertLess(np.ptp(result['height_m']), 1e-5)
        self.assertTrue(result['inferred_bed'].all())

    def test_tile_order_independent(self):
        bed = fixture(); xy = np.array([[0, 70], [-70, 0], [70, 0], [40, 0]])
        together = bed.sample(xy)
        for key in together:
            separate = np.concatenate([bed.sample(xy[i:i+1])[key] for i in range(len(xy))])
            np.testing.assert_equal(together[key], separate)
            np.testing.assert_equal(together[key], bed.sample(xy[::-1])[key][::-1])

    def test_stage_continuous_across_unequal_branch_grades(self):
        bed = fixture(); bed.arrays['rio_azul']['stage_m'] = np.array([13., 11.5, 10.])
        for distance in (10., 40., 70.):
            xy = [[-distance-1e-6, distance], [-distance+1e-6, distance]]
            self.assertLess(np.ptp(bed.sample(xy)['reference_m']), 1e-6)

    def test_bed_continuous_across_different_branch_widths(self):
        bed = fixture()
        bed.arrays['rio_azul']['left_m'][:] = -5
        bed.arrays['rio_azul']['right_m'][:] = 5
        xy = [[-5-1e-6, 5], [-5+1e-6, 5]]
        self.assertLess(np.ptp(bed.sample(xy)['height_m']), 1e-5)

    def test_triangle_guard_preserves_island_support(self):
        bed = fixture(); xy = np.array([[40., 3.25], [70., 0.]])
        result = preserve_triangle_support(bed, xy, bed.sample(xy), spacing_m=1.)
        self.assertTrue(result['inference_support_veto'][0])
        self.assertFalse(result['inference_support_veto'][1])
        self.assertEqual(result['height_m'][0], 12.)


if __name__ == '__main__':
    unittest.main()
