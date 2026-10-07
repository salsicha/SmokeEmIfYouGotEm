import unittest
import numpy as np
from plan_lidarbc_corridor_capture import corridor_cells,capture_window,route_header_gaps


class CorridorPlanTests(unittest.TestCase):
    def test_covered_endpoints_do_not_hide_interior_gap(self):
        self.assertEqual(route_header_gaps([[0,0],[10,0]],
            [[-1,-1,2,1],[8,-1,11,1]]),[[2.,8.]])

    def test_touching_overlapping_headers_and_diagonal_clip(self):
        self.assertEqual(route_header_gaps([[0,0],[10,0]],
            [[-1,-1,6,1],[5,-1,8,1],[8,-1,11,1]]),[])
        np.testing.assert_allclose(route_header_gaps([[0,0],[10,10]],
            [[2,2,8,8]]),[[0,2*np.sqrt(2)],[8*np.sqrt(2),10*np.sqrt(2)]])

    def test_gaps_merge_across_vertices_and_parallel_exclusions(self):
        self.assertEqual(route_header_gaps([[0,0],[2,0],[5,0]],[]),[[0.,5.]])
        self.assertEqual(route_header_gaps([[0,0],[2,0],[5,0]],[[0,1,5,2]]),[[0.,5.]])
        with self.assertRaises(ValueError):route_header_gaps([[0,0],[0,0]],[])

    def test_every_segment_and_buffer_are_covered(self):
        route=np.array([[442123.,5749765.],[443555.,5751999.],[441911.,5753134.]])
        cells={tuple(c['cell']) for c in corridor_cells(route,350,1024)}
        for a,b in zip(route[:-1],route[1:]):
            for t in np.linspace(0,1,101):
                for x,y in [(-350,-350),(-350,350),(350,-350),(350,350),(0,0)]:
                    self.assertIn(tuple(np.floor(((1-t)*a+t*b+[x,y])/1024).astype(int)),cells)

    def test_deterministic_independent_of_travel_direction(self):
        points=[[4090,100],[2050,800],[10,4100]]
        self.assertEqual(corridor_cells(points),corridor_cells(points[::-1]))

    def test_all_requests_fit_native_tile_and_budget(self):
        self.assertEqual(capture_window([0,0,2048,2048],[100,-10,3000,1500]),[100,0,2048,1500])
        self.assertIsNone(capture_window([0,0,2048,2048],[2048,0,4096,2048]))
        for bounds in ([0.1,0,100,100],[0,0,float('nan'),100],[100,0,0,100]):
            with self.assertRaises(ValueError):capture_window([0,0,100,100],bounds)

    def test_invalid_or_unbounded_inputs_refused(self):
        for route in ([],[[0,0]],[[0,0],[float('nan'),2]],[[0,0],[1e9,1e9]]):
            with self.assertRaises(ValueError):corridor_cells(route)
        for size in (0,-1,3000,True):
            with self.assertRaises(ValueError):corridor_cells([[0,0],[10,10]],size=size)
        with self.assertRaises(ValueError):corridor_cells([[0,0],[10,10]],buffer_m=0)


if __name__=='__main__':unittest.main()
