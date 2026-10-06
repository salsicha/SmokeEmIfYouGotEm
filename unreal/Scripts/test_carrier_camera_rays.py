import unittest
import numpy as np
from audit_carrier_camera_rays import camera_ray, nearest_triangle, probe, terrain_comparison


class CarrierCameraRaysTest(unittest.TestCase):
    def view(self):
        return dict(schema='raftsim.carrier_view.v1', game_frame=2, world_seconds=.5,
                    constrained_view_rect=[10, 20, 210, 120],
                    world_cm_to_clip_row_matrix=np.diag([1., 1., -1., 1.]).tolist())

    def test_row_matrix_translation_and_viewport_y(self):
        view = self.view()
        view['world_cm_to_clip_row_matrix'][3][0] = -100
        origin, direction = camera_ray(view, view, [160, 45])
        np.testing.assert_allclose(origin, [1.005, .005, -.01], rtol=0, atol=1e-15)
        np.testing.assert_array_equal(direction, [0, 0, 1])

    def test_mismatched_epoch_rejected(self):
        for key in ('game_frame', 'world_seconds'):
            meta = self.view()
            meta[key] += 1
            with self.assertRaisesRegex(ValueError, 'epoch'):
                camera_ray(self.view(), meta, [100, 50])

    def test_reversed_z_perspective_homogeneous_divide(self):
        view = self.view()
        view['world_cm_to_clip_row_matrix'] = [[2, 0, 0, 0], [0, 3, 0, 0], [0, 0, 0, 1], [0, 0, 1, 0]]
        origin, direction = camera_ray(view, view, [160, 45])
        expected = np.array([.25, 1/6, 1.])
        np.testing.assert_allclose(origin, expected*.01, rtol=0, atol=1e-16)
        np.testing.assert_allclose(direction, expected/np.linalg.norm(expected), rtol=0, atol=1e-15)

    def test_invalid_projection_or_pixel_rejected(self):
        for pixel in ([0, 50], [210, 50], [100, 120], [np.nan, 50]):
            with self.assertRaises(ValueError):
                camera_ray(self.view(), self.view(), pixel)
        view = self.view()
        view['world_cm_to_clip_row_matrix'] = np.zeros((4, 4)).tolist()
        with self.assertRaises(np.linalg.LinAlgError):
            camera_ray(view, view, [100, 50])

    def test_nearest_hit_winding_and_missing(self):
        triangle = np.array([[[-1., -1., 1.], [1., -1., 1.], [0., 1., 1.]]])
        origin, direction = np.zeros(3), np.array([0., 0., 1.])
        for order in (slice(None), slice(None, None, -1)):
            xyz = np.concatenate((triangle+np.array([0, 0, 2]), triangle))[:, order]
            index, distance, bary = nearest_triangle(origin, direction, xyz)
            self.assertEqual((index, distance), (1, 1.))
            np.testing.assert_array_equal(bary @ xyz[index], [0, 0, 1])
        self.assertIsNone(nearest_triangle(origin, -direction, triangle))
        self.assertIsNone(nearest_triangle(origin, np.array([1., 0., 0.]), triangle))
        self.assertIsNone(nearest_triangle(np.array([3., 0., 0.]), direction, triangle))

    def fixture(self):
        xy = np.array([[-1., -1.], [1., -1.], [-1., 1.], [1., 1.]])
        vertices = np.column_stack((np.arange(4), xy*100, np.zeros((4, 4))))
        source = np.column_stack((np.arange(4), xy, np.ones(4), np.zeros(4), np.ones(4), np.zeros((4, 2))))
        normals = np.column_stack((np.arange(4), np.tile([0., 0., 1.], (4, 1))))
        meta = dict(schema='raftsim.submitted_carrier_shape.v2', game_frame=2, world_seconds=.5,
            active_vertices=4, buffer_vertices=4, triangles=2, source_nx=2, source_ny=2,
            world_y_sign=1, focus_x_cm=0, focus_y_cm=0, render_lift_cm=0, detail_sequence=0, scope='test')
        return meta, self.view(), vertices, np.array([[0., 2., 3.], [0., 3., 1.]]), source, normals

    def test_flat_plane_full_probe_and_dry_exclusion(self):
        args = self.fixture()
        hit = probe(*args, [[110, 70]])['probes'][0]['hit']
        self.assertEqual(hit['world_m'], [0., 0., 0.])
        self.assertEqual(hit['slope_degrees'], 0.)
        self.assertEqual(hit['cpu_normal_face_angle_degrees'], 0.)
        self.assertEqual(hit['component_gradient']['submitted_base_minus_target'], [0., 0.])
        self.assertEqual([c['id'] for c in hit['source_cell_corners']], [0, 1, 2, 3])
        args[4][0, 3] = 0
        hit = probe(*args, [[110, 70]])['probes'][0]['hit']
        self.assertFalse(hit['fully_wet_source_comparison'])
        self.assertNotIn('cached_source', hit['component_gradient'])

    def test_reordered_normals_rejected(self):
        args = self.fixture()
        args[5][:, 0] = [3, 2, 1, 0]
        with self.assertRaisesRegex(ValueError, 'normals'):
            probe(*args, [[110, 70]])

    def test_signed_terrain_gap_is_not_clamped_or_invented(self):
        view = self.view()
        view['world_cm_to_clip_row_matrix'] = [[2, 0, 0, 0], [0, 3, 0, 0], [0, 0, 0, 1], [0, 0, 1, 0]]
        origin, direction = camera_ray(view, view, [110, 70])
        hit = dict(world_m=[0., 0., 1.])
        self.assertIsNone(terrain_comparison(view, [110, 70], hit, origin, direction))
        row = dict(pixel=[110, 70], hit=True, ray_origin_cm=(origin*100).tolist(),
                   ray_direction=direction.tolist(), ground_world_cm=[0, 0, 150])
        view['terrain_ray_probes'] = [row]
        result = terrain_comparison(view, [110, 70], hit, origin, direction)
        self.assertEqual(result['signed_distance_behind_water_m'], .5)
        self.assertEqual(result['signed_camera_depth_gap_cm'], 50.)
        self.assertEqual(result['independent_direction_error'], 0.)
        row['ground_world_cm'][2] = 50
        self.assertEqual(terrain_comparison(view, [110, 70], hit, origin, direction)['signed_camera_depth_gap_cm'], -50.)
        row['hit'] = False
        self.assertNotIn('signed_camera_depth_gap_cm', terrain_comparison(view, [110, 70], hit, origin, direction))
        view['terrain_ray_probes'].append(row)
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            terrain_comparison(view, [110, 70], hit, origin, direction)


if __name__ == '__main__':
    unittest.main()
