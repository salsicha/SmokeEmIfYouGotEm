import unittest
import tempfile
from pathlib import Path
import numpy as np
from audit_submitted_carrier_shape import gradients, raw_stage, summarize, read_table


class SubmittedCarrierShapeTest(unittest.TestCase):
    def fixture(self):
        xy = np.array([[0., 0.], [1., 0.], [0., 1.], [1., 1.]])
        # Base x, crest 2y, detail -x/2. Displayed gradient=(.5,2).
        vertices = np.column_stack((np.arange(4), xy*100, (xy[:, 0]+2*xy[:, 1])*100,
                                   xy[:, 1]*150, xy[:, 1]*50, -xy[:, 0]*50))
        source = np.column_stack((np.arange(4), xy, np.ones(4), xy[:, 0], np.ones(4)))
        meta = dict(schema='raftsim.submitted_carrier_shape.v1', active_vertices=4,
                    buffer_vertices=8, triangles=2, source_nx=2, source_ny=2,
                    world_y_sign=1, focus_x_cm=50, focus_y_cm=50, render_lift_cm=0,
                    scope='fixture', world_seconds=13, detail_sequence=5)
        return meta, vertices, np.array([[0., 2., 1.], [1., 2., 3.]]), source

    def test_plane_and_signed_component_closure(self):
        report = summarize(*self.fixture(), 30)
        self.assertAlmostEqual(report['projected_area_m2'], 1.)
        self.assertEqual(report['maximum_gradient_component_sum_error'], 0.)
        for triangle in report['steepest_triangles_at_least_one_square_centimeter']:
            self.assertEqual(triangle['component_gradient']['displayed'], [.5, 2.])
            self.assertEqual(triangle['component_gradient']['base_residual'], [1., 0.])
            self.assertEqual(triangle['raw_source_triangle_gradient'], [1., 0.])
        self.assertLess(report['slope_groups'][3]['area_weighted_signed_gradient_along_displayed_slope']['detail'], 0)

    def test_winding_independent_gradient(self):
        xy = np.array([[[0., 0.], [2., 0.], [0., 3.]]])
        values = np.array([[4., 6., -2.]])
        np.testing.assert_array_equal(gradients(xy, values), [[1., -2.]])
        np.testing.assert_array_equal(gradients(xy[:, ::-1], values[:, ::-1]), [[1., -2.]])

    def test_world_sign_and_no_dry_or_outside_extrapolation(self):
        meta, vertices, triangles, source = self.fixture()
        points = np.array([[.3, -.4], [2., 2.]])
        height, valid = raw_stage(points, source, 2, 2, -1)
        self.assertEqual(valid.tolist(), [True, False])
        self.assertAlmostEqual(height[0], .3)
        self.assertTrue(np.isnan(height[1]))
        source[3, 3] = 0
        self.assertFalse(raw_stage(points, source, 2, 2, -1)[1].any())

    def test_reserved_fractional_negative_indices_rejected(self):
        for value in [4., -.1, .5]:
            meta, vertices, triangles, source = self.fixture()
            triangles[0, 0] = value
            with self.assertRaises(ValueError):
                summarize(meta, vertices, triangles, source, 30)

    def test_wrong_count_ids_lattice_and_radius_rejected(self):
        for mutation in ['count', 'id', 'source_id', 'lattice', 'radius']:
            meta, vertices, triangles, source = self.fixture()
            radius = 30
            if mutation == 'count': meta['active_vertices'] = 5
            if mutation == 'id': vertices[2, 0] = 0
            if mutation == 'source_id': source[2, 0] = 0
            if mutation == 'lattice': source[2, 1] = .1
            if mutation == 'radius': radius = 0
            with self.assertRaises(ValueError):
                summarize(meta, vertices, triangles, source, radius)

    def test_zero_area_reported_not_silently_accepted(self):
        meta, vertices, triangles, source = self.fixture()
        triangles[1] = [0, 0, 0]
        result = summarize(meta, vertices, triangles, source, 30)
        self.assertEqual(result['zero_projected_area_nearby'], 1)
        self.assertFalse(result['accepted'])
        with self.assertRaises(ValueError):
            gradients(np.zeros((1, 3, 2)), np.zeros((1, 3)))

    def test_nonfinite_tables_and_metadata_rejected(self):
        for location in ['vertex', 'source', 'triangle', 'metadata']:
            meta, vertices, triangles, source = self.fixture()
            if location == 'vertex': vertices[1, 3] = np.nan
            if location == 'source': source[1, 4] = np.inf
            if location == 'triangle': triangles[0, 0] = np.nan
            if location == 'metadata': meta['render_lift_cm'] = np.nan
            with self.assertRaises(ValueError):
                summarize(meta, vertices, triangles, source, 30)

    def test_csv_headers_truncation_and_nonfinite_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'fixture.csv'
            for text in ['b,a\n1,2\n', 'a,b\n1\n', 'a,b\n1,nan\n', 'a,b\n']:
                path.write_text(text, encoding='utf-8-sig')
                with self.assertRaises(ValueError):
                    read_table(path, ['a', 'b'])
            path.write_text('a,b\n1,2\n', encoding='utf-8-sig')
            np.testing.assert_array_equal(read_table(path, ['a', 'b']), [[1, 2]])


if __name__ == '__main__':
    unittest.main()
