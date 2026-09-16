import unittest
import tempfile
from pathlib import Path
import numpy as np
from audit_submitted_carrier_shape import gradients, raw_stage, summarize, read_table, source_grid_triangles


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

    def test_nonplanar_quad_uses_actual_shoreline_fan_not_legacy_diagonal(self):
        # Native BuildClipped's fully wet perimeter is A,C,D,B. Only D is high:
        # ACD is z=x, ADB is z=y. B-C interpolation would give zero at the
        # first two probes and manufacture a source/presentation discrepancy.
        _, _, _, source = self.fixture()
        source[:, 4] = [0., 0., 0., 1.]
        field_points = np.array([[.75,.25],[.25,.75],[.5,.5],[0.,0.],[1.,1.]])
        for sign in (-1, 1):
            heights, valid = raw_stage(field_points*[1,sign], source, 2, 2, sign)
            np.testing.assert_array_equal(valid, np.ones(5, dtype=bool))
            np.testing.assert_array_equal(heights, [.25,.25,.5,0.,1.])
        np.testing.assert_array_equal(source_grid_triangles(2,2), [[0,2,3],[0,3,1]])

    def test_refined_nonplanar_native_fan_has_no_invented_base_error(self):
        meta, _, _, source = self.fixture()
        meta.update(schema='raftsim.submitted_carrier_shape.v2',active_vertices=6,
                    buffer_vertices=6,triangles=4)
        source[:,4] = [0.,0.,0.,1.]
        source = np.column_stack((source,source[:,4],source[:,4]))
        xy = np.array([[0.,0.],[1.,0.],[0.,1.],[1.,1.],[.5,.5],[.25,.25]])
        z = np.array([0.,0.,0.,1.,.5,.25])
        vertices = np.column_stack((np.arange(6),xy*100,z*100,np.zeros((6,3))))
        triangles = np.array([[0,2,4],[2,3,4],[0,4,1],[4,3,1]],dtype=float)
        for sign in (-1,1):
            meta['world_y_sign'] = sign
            meta['focus_y_cm'] = sign*50
            vertices[:,2] = xy[:,1]*100*sign
            result = summarize(meta,vertices,triangles,source,30)
            for group in result['slope_groups']:
                parts = group['source_comparison_signed_gradient_along_displayed_slope']
                if parts:
                    self.assertAlmostEqual(parts['target_minus_source'],0.)
                    self.assertAlmostEqual(parts['submitted_base_minus_target'],0.)

    def test_target_split_retains_opposite_signed_contributions(self):
        meta, vertices, triangles, source = self.fixture()
        meta['schema'] = 'raftsim.submitted_carrier_shape.v2'
        # Raw=x, target base=3x, submitted base=x. Presentation differences
        # cancel; neither absolute magnitudes nor a changed denominator may hide it.
        source = np.column_stack((source, 3*source[:, 1], 3*source[:, 1]+2*source[:, 2]))
        result = summarize(meta, vertices, triangles, source, 30)
        group = result['slope_groups'][3]
        parts = group['source_comparison_signed_gradient_along_displayed_slope']
        along_x = .5/np.sqrt(.5**2+2**2)
        self.assertAlmostEqual(parts['cached_source'], along_x)
        self.assertAlmostEqual(parts['target_minus_source'], 2*along_x)
        self.assertAlmostEqual(parts['submitted_base_minus_target'], -2*along_x)
        self.assertEqual(group['source_comparison_area_m2'], 1.)
        self.assertEqual(result['maximum_source_component_sum_error'], 0.)
        reverse = summarize(meta, vertices, triangles[:, ::-1], source, 30)
        self.assertEqual(reverse['slope_groups'], result['slope_groups'])

    def test_target_split_reflects_world_coordinates(self):
        meta, vertices, triangles, source = self.fixture()
        meta.update(schema='raftsim.submitted_carrier_shape.v2', world_y_sign=-1, focus_y_cm=-50)
        vertices[:, 2] *= -1
        source = np.column_stack((source, 2*source[:, 2], source[:, 1]+2*source[:, 2]))
        report = summarize(meta, vertices, triangles, source, 30)
        parts = report['slope_groups'][3]['source_comparison_signed_gradient_along_displayed_slope']
        # World target gradient=(0,-2), source=(1,0), base=(1,0).
        direction = np.array([.5, -2])/np.sqrt(4.25)
        self.assertAlmostEqual(parts['target_minus_source'], np.dot([-1, -2], direction))
        self.assertAlmostEqual(parts['submitted_base_minus_target'], np.dot([1, 2], direction))

    def test_unavailable_target_or_dry_comparison_is_not_zero_evidence(self):
        meta, vertices, triangles, source = self.fixture()
        historical = summarize(meta, vertices, triangles, source, 30)
        parts = historical['slope_groups'][3]['source_comparison_signed_gradient_along_displayed_slope']
        self.assertNotIn('target_minus_source', parts)
        source[0, 3] = 0
        empty = summarize(meta, vertices, triangles, source, 30)
        self.assertIsNone(empty['maximum_source_component_sum_error'])
        self.assertEqual(empty['slope_groups'][3]['source_comparison_signed_gradient_along_displayed_slope'], {})
        self.assertEqual(empty['slope_groups'][3]['source_comparison_area_m2'], 0.)

    def test_target_schema_and_finiteness_are_required(self):
        meta, vertices, triangles, source = self.fixture()
        meta['schema'] = 'raftsim.submitted_carrier_shape.v2'
        with self.assertRaises(ValueError):
            summarize(meta, vertices, triangles, source, 30)
        source = np.column_stack((source, np.zeros((4, 2))))
        source[0, 6] = np.inf
        with self.assertRaises(ValueError):
            summarize(meta, vertices, triangles, source, 30)

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
