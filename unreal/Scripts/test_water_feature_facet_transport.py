import unittest
import numpy as np
import test_water_feature_mesh_interface as fixtures
from water_feature_facet_transport import FacetTransport


class FacetTransportTests(unittest.TestCase):
    def setUp(self):
        vertices, triangles = fixtures.cube()
        self.interface = fixtures.model(vertices, triangles)
        self.walker = FacetTransport(self.interface)

    def face_at(self, point):
        return self.interface.sample(point)['triangle']

    def test_coplanar_diagonal_exact_straight_motion(self):
        p, v = np.array([-.6, .3, 1.]), np.array([.8, -.4, 0.])
        result = self.walker.walk(p, v, self.face_at(p), 1)
        self.assertTrue(result['complete'])
        self.assertGreaterEqual(len(result['crossings']), 1)
        np.testing.assert_allclose(result['position_m'], p+v, atol=1e-13)
        np.testing.assert_allclose(result['velocity_mps'], v, atol=1e-13)

    def test_right_angle_fold_matches_exact_unfolding(self):
        p, v = np.array([.7, .23, 1.]), np.array([.5, 0., 0.])
        result = self.walker.walk(p, v, self.face_at(p), 2.)
        self.assertTrue(result['complete'])
        np.testing.assert_allclose(result['position_m'], [1., .23, .3], atol=1e-13)
        np.testing.assert_allclose(result['velocity_mps'], [0., 0., -.5], atol=1e-13)
        self.assertLess(result['maximum_speed_error_mps'], 1e-13)

    def test_split_step_matches_whole_geodesic(self):
        p, v = np.array([.7, .23, 1.]), np.array([.5, .03, 0.])
        face = self.face_at(p)
        whole = self.walker.walk(p, v, face, 4)
        for _ in range(40):
            part = self.walker.walk(p, v, face, .1)
            self.assertTrue(part['complete'])
            p, v, face = np.array(part['position_m']), np.array(part['velocity_mps']), part['face']
        np.testing.assert_allclose(p, whole['position_m'], atol=1e-12)
        np.testing.assert_allclose(v, whole['velocity_mps'], atol=1e-12)

    def test_recorded_event_segments_remain_on_actual_facets(self):
        p = np.array([.7, .23, 1.])
        result = self.walker.walk(p, [.5, .03, 0], self.face_at(p), 4.)
        points = result['path']
        for a, b in zip(points, points[1:]):
            for fraction in (.1, .5, .9):
                q = (1-fraction)*np.array(a['position_m'])+fraction*np.array(b['position_m'])
                self.assertLess(abs(self.interface.sample(q)['phi_m']), 1e-12)

    def test_vertex_and_contact_boundaries_stop_explicitly(self):
        p = np.array([.5, .5, 1.])
        result = self.walker.walk(p, [.5, .5, 0], self.face_at(p), 2.)
        self.assertFalse(result['complete'])
        self.assertIn('vertex', result['status'])
        self.assertGreater(result['remaining_seconds'], 0)
        p = np.array([.7, .23, 1.])
        self.interface.allowed[self.interface.normals[:, 0] > .9] = False
        result = self.walker.walk(p, [.5, 0, 0], self.face_at(p), 2.)
        self.assertFalse(result['complete'])
        self.assertIn('contact', result['status'])
        np.testing.assert_allclose(result['position_m'], [1., .23, 1.], atol=1e-13)

    def test_initial_burial_normal_velocity_and_limits_rejected(self):
        p = np.array([.7, .23, 1.])
        face = self.face_at(p)
        for point, velocity, seconds in [(p+[0, 0, -.001], [.5, 0, 0], 1),
                                        (p, [.5, 0, .01], 1), (p, [.5, 0, 0], -1)]:
            with self.assertRaises(ValueError):
                self.walker.walk(point, velocity, face, seconds)
        result = self.walker.walk(p, [.5, .03, 0], face, 20, maximum_crossings=1)
        self.assertFalse(result['complete'])
        self.assertIn('limit', result['status'])

    def test_zero_velocity_and_inputs_unchanged(self):
        p, v = np.array([.7, .23, 1.]), np.zeros(3)
        before = p.copy()
        result = self.walker.walk(p, v, self.face_at(p), 1.)
        self.assertTrue(result['complete'])
        self.assertEqual(result['remaining_seconds'], 0)
        np.testing.assert_array_equal(result['position_m'], p)
        np.testing.assert_array_equal(p, before)
        np.testing.assert_array_equal(v, np.zeros(3))

    def test_complete_event_paths_cover_exact_requested_endpoint(self):
        p = np.array([.7, .23, 1.])
        face = self.face_at(p)
        # These independently selected multi-edge cube paths previously
        # accumulated terminal timestamps one ulp on either side of duration.
        for velocity, duration in [([.51, .03, 0.], 7.7),
                                   ([.73, .17, 0.], 3.1),
                                   ([.13, .17, 0.], 7.7)]:
            with self.subTest(velocity=velocity, duration=duration):
                result = self.walker.walk(p, velocity, face, duration)
                self.assertTrue(result['complete'])
                self.assertGreater(len(result['crossings']), 1)
                self.assertEqual(result['consumed_seconds'], duration)
                self.assertEqual(result['remaining_seconds'], 0.)
                self.assertEqual(result['path'][0]['seconds'], 0.)
                self.assertEqual(result['path'][-1]['seconds'], duration)
                self.assertTrue(all(a['seconds'] <= b['seconds'] for a, b in
                                    zip(result['path'], result['path'][1:])))
                self.assertEqual(result['path'][-1]['position_m'], result['position_m'])
                self.assertLess(result['maximum_speed_error_mps'], 1e-12)
                self.assertLess(result['maximum_facet_plane_error_m'], 1e-12)


if __name__ == '__main__':
    unittest.main()
