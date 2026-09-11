import sys
import unittest
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from audit_liquid_particle_routes import physical_owners, verify_packet


class NativeRoutesTest(unittest.TestCase):
    def test_physical_internal_edges_and_outer_edge(self):
        regions = [dict(id=i, bounds_station_lateral_m=[[i, 0], [i+1, 1]],
                        axis_x_canonical=[1, 0], axis_y_canonical=[0, 1]) for i in range(2)]
        p = np.array([[0, 0, 100], [99, -50, 0], [100, -50, 0], [200, -100, 0], [201, 0, 0]])
        np.testing.assert_array_equal(physical_owners(p, regions), [0, 0, 1, 1, -1])

    def test_rotated_reflected_frame_and_invalid_position(self):
        regions = [dict(id=4, bounds_station_lateral_m=[[1, 2], [2, 3]],
                        axis_x_canonical=[0, 1, 0], axis_y_canonical=[-1, 0, 0])]
        np.testing.assert_array_equal(physical_owners([[-250, -150, 20]], regions), [4])
        with self.assertRaises(ValueError): physical_owners([[np.nan, 0, 0]], regions)
        with self.assertRaises(ValueError): physical_owners([[-250, -150, 20]], regions*2)

    def setUp(self):
        self.record = dict(particle_count=1, particle_capacity=2, route_float_components=6, route_int_components=4,
                           route_position_offset=0, route_velocity_offset=3, route_identity_offsets=[0, 1, 2, 3], region_id=0)
        self.p = np.array([[10, 20, 30, 1]], dtype='<f4')
        self.v = np.array([[40, 50, 60, 1]], dtype='<f4')
        self.ids = np.array([[0, 16777217, -2147483648, -1]], dtype='<i4')
        self.words = np.zeros((10, 2), dtype='<u4')
        self.words[:3, 0] = self.p[0, :3].view('<u4')
        self.words[3:6, 0] = self.v[0, :3].view('<u4')
        self.words[6:, 0] = self.ids[0].view('<u4')
        self.routes = np.array([[1, 0, 0, 1]], dtype='<u4')
        self.counts = np.array([0, 1, 0, 0, 1], dtype='<u4')

    def check(self):
        return verify_packet(self.record, self.words, self.routes, self.counts, self.p, self.v, self.ids, np.array([1]), owners=2)

    def test_exact_payload_and_crossing(self):
        self.assertEqual(self.check(), 1)
        self.words[7, 0] = np.float32(16777217).astype(np.uint32)
        with self.assertRaises(ValueError): self.check()

    def test_wrong_destination_count_and_inactive_state_rejected(self):
        self.routes[0, 0] = 0
        with self.assertRaises(ValueError): self.check()
        self.routes[0, 0] = 1
        self.counts[1] = 2
        with self.assertRaises(ValueError): self.check()
        self.counts[1] = 1
        self.words[0, 1] = 1
        with self.assertRaises(ValueError): self.check()


if __name__ == '__main__': unittest.main()
