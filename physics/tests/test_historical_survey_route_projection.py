import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from screen_south_fork_historical_survey_locations import project_to_route


class RouteProjectionTests(unittest.TestCase):
    def test_interpolates_instead_of_snapping_to_vertex(self):
        r = project_to_route([3, 4], [[0, 0], [10, 0]], [20, 30])
        self.assertEqual(r['station_m'], 23)
        self.assertEqual(r['distance_to_route_m'], 4)

    def test_endpoints_are_clamped(self):
        self.assertEqual(project_to_route([-5, 0], [[0, 0], [10, 0]], [0, 10])['station_m'], 0)
        self.assertEqual(project_to_route([15, 0], [[0, 0], [10, 0]], [0, 10])['station_m'], 10)

    def test_bend_and_degenerate_segment(self):
        r = project_to_route([9, 6], [[0, 0], [10, 0], [10, 0], [10, 10]], [0, 10, 10, 20])
        self.assertEqual(r['station_m'], 16)
        self.assertEqual(r['distance_to_route_m'], 1)
        self.assertEqual(r['segment'], 2)

    def test_rejects_invalid_routes(self):
        for xy, stations in [([[0, 0], [0, 0]], [0, 0]), ([[0, 0], [10, 0]], [10, 0]),
                             ([[0, 0], [float('nan'), 0]], [0, 10])]:
            with self.assertRaises(ValueError):
                project_to_route([0, 0], xy, stations)


if __name__ == '__main__':
    unittest.main(verbosity=2)
