import copy
import json
import unittest

from project_futaleufu_rapid_evidence import BASE, build, project


class RapidEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.chart = dict(points=[[0., 0., 0., 0., 1.], [10000., 10000., 5000., 0., 1.]],
                          horizontal_origin_m=[740000., 5195000.], world_y_sign=-1,
                          horizontal_crs='EPSG:32718 WGS 84 / UTM zone 18S')

    def test_uses_distance_from_confluence_not_catalog_order(self):
        p = project(self.chart, 2000., 32.5, 35.5, 1000.)
        self.assertEqual(p['route_station_m'], 5000.)
        self.assertEqual(p['local_east_north_m'], [5000., 2500.])
        self.assertEqual(p['unreal_xy_cm'], [500000., -250000.])

    def test_miles_convert_without_arbitrary_end_anchor_scaling(self):
        p = project(self.chart, 2000., 15.5, 17., 1609.344)
        self.assertAlmostEqual(p['route_station_m'], 4414.016)

    def test_outside_route_or_on_tributary_is_rejected_not_clamped(self):
        for value in (30., 32.5, 50., float('nan')):
            with self.subTest(value=value), self.assertRaises(ValueError):
                project(self.chart, 2000., 32.5, value, 1000.)

    def test_invalid_frames_and_nonmonotone_charts_refused(self):
        for field, value in [('world_y_sign', 1), ('horizontal_crs', 'EPSG:3157'),
                             ('points', [[0., 0., 0., 0., 1.], [0., 1., 2., 0., 1.]])]:
            chart = copy.deepcopy(self.chart)
            chart[field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                project(chart, 2000., 32.5, 35.5, 1000.)

    def test_real_full_route_covers_all_five_without_inventing_bounds(self):
        report = build()
        self.assertEqual(len(report['rapids']), 5)
        self.assertFalse(report['runtime_modified'])
        self.assertFalse(report['rapid_boundaries_verified'])
        asleep = report['rapids'][0]
        self.assertTrue(asleep['superseded_order_slot_on_tributary'])
        self.assertAlmostEqual(asleep['source_disagreement_m'], 585.984)
        for row in report['rapids']:
            self.assertIsNone(row['rapid_start_m'])
            self.assertIsNone(row['rapid_end_m'])
            self.assertIsNone(row['chosen_runtime_station_m'])
            for point in row['estimates']:
                self.assertGreater(point['route_station_m'], report['confluence_route_station_m'])
                self.assertLess(point['route_station_m'], report['route_length_m'])

    def test_committed_evidence_matches_current_chart_and_source_pins(self):
        stored = json.loads((BASE/'review/guide_distance_locations_2026_10_08.json').read_text())
        self.assertEqual(stored, build())


if __name__ == '__main__':
    unittest.main()
