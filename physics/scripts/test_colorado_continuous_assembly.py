import copy
import unittest

import numpy as np

from build_colorado_continuous_assembly import native_progress_points, rebase_chart, uncovered_intervals


class ContinuousAssemblyTests(unittest.TestCase):
    def test_native_densification_preserves_polyline_and_bounds_edge_steps(self):
        xy = np.array([[0., 0.], [16.1, 0.], [20., 15.]])
        station = np.r_[0., np.cumsum(np.linalg.norm(np.diff(xy, axis=0), axis=1))]
        normal = np.array([[0., 1.], [-.6, .8], [-1., 0.]])
        rows = np.asarray(native_progress_points(station, xy, normal, np.array([0., 0.])))
        self.assertGreater(len(rows), len(xy))
        for s, p in zip(station, xy):
            np.testing.assert_allclose(rows[rows[:, 0] == s, 1:3], [p])
        self.assertAlmostEqual(np.linalg.norm(np.diff(rows[:, 1:3], axis=0), axis=1).sum(), station[-1])
        for sign in (-1, 1):
            self.assertLessEqual(np.linalg.norm(np.diff(rows[:, 1:3]+sign*256*rows[:, 3:5], axis=0), axis=1).max(), 15.5)

    def chart(self):
        return dict(schema='raftsim.curved_river_coordinate_map.v1', world_y_sign=-1,
                    vertical_reference='NAD83(2011) ellipsoid heights',
                    vertical_datum_m=910., horizontal_origin_epsg6404_m=[236190., 640364.],
                    points=[[0., 980., 620., .8, .6], [2., 981.2, 618.4, .8, .6]])

    def test_preserves_geography_surface_and_sides(self):
        chart = self.chart()
        before = copy.deepcopy(chart)
        common, delta = rebase_chart(chart, [242600., 650500.], 310.)
        for side in (-20., 0., 20.):
            for old, new in zip(chart['points'], common['points']):
                old_xy = np.array(old[1:3])+side*np.array(old[3:5])
                new_xy = np.array(new[1:3])+side*np.array(new[3:5])
                old_world = np.r_[old_xy*[100, -100], (921.2-chart['vertical_datum_m'])*100]
                new_world = np.r_[new_xy*[100, -100], (921.2-common['vertical_datum_m'])*100]
                np.testing.assert_allclose(old_world+delta, new_world, atol=1e-8)
                self.assertEqual(old[0], new[0])
                self.assertEqual(old[3:5], new[3:5])
        self.assertEqual(before, chart)

    def test_wrong_datum_and_handedness_refused(self):
        for key, value in [('world_y_sign', 1), ('vertical_reference', 'NAVD88')]:
            chart = self.chart()
            chart[key] = value
            with self.assertRaises(ValueError): rebase_chart(chart, [0, 0], 0)

    def test_nonfinite_and_bad_chart_refused(self):
        for col, value in [(0, -1), (1, float('nan')), (3, 0.)]:
            chart = self.chart()
            chart['points'][1][col] = value
            with self.assertRaises(ValueError): rebase_chart(chart, [0, 0], 0)
        with self.assertRaises(ValueError): rebase_chart(self.chart(), [0, float('nan')], 0)
        with self.assertRaises(ValueError): rebase_chart(self.chart(), [0, 0], float('inf'))

    def test_gaps_include_putin_exit_and_small_internal_gap(self):
        self.assertEqual(uncovered_intervals(0, 100, [(10, 20), (20.01, 70), (60, 90)]),
                         [[0, 10], [20, 20.01], [90, 100]])

    def test_overlap_is_not_counted_twice(self):
        self.assertEqual(uncovered_intervals(0, 100, [(50, 110), (-10, 60), (30, 40)]), [])
        self.assertEqual(uncovered_intervals(0, 100, []), [[0, 100]])

    def test_invalid_interval_refused(self):
        for interval in [(20, 10), (10, 10), (0, float('nan'))]:
            with self.assertRaises(ValueError): uncovered_intervals(0, 100, [interval])


if __name__ == '__main__':
    unittest.main()
