import unittest
import numpy as np
from water_feature_flat_metrics import closed_box_phi,mesh_metrics,paired_residuals


class FlatMetricsTests(unittest.TestCase):
    def test_closed_native_box_wall_crossings(self):
        p=closed_box_phi((32,24,24))
        np.testing.assert_array_equal(p[:5,12,6],[-1.5,-.5,.5,1.5,2.5])
        np.testing.assert_array_equal(p[16,12,:5],[-1.5,-.5,.5,1.5,2.5])
        self.assertEqual(p[29,12,6],.5);self.assertEqual(p[30,12,6],-.5)

    def test_native_triangle_top_height_and_missing_support(self):
        vertices=np.array([[2.,2.,4.],[7.,2.,4.],[2.,7.,4.]])
        result=mesh_metrics(vertices,[[0,1,2]],[[3,3],[8,8]],1.,1.,(12,12,12))
        self.assertEqual(result['samples'][0]['top_upward_triangle_height_m'],4.)
        self.assertEqual(result['samples'][1]['status'],'absent')
        self.assertEqual(result['boundary_edges'],3)

    def test_wall_intrusion_is_retained(self):
        r=mesh_metrics([[1.,2.,4.],[7.,2.,4.],[2.,7.,4.]],[[0,1,2]],[],1.,1.,(12,12,12))
        self.assertEqual(r['maximum_vertex_wall_intrusion_m'],1.)
        self.assertEqual(r['sampled_vertices_outside_closed_fluid_box'],1)

    def test_degenerate_face_is_not_hidden(self):
        r=mesh_metrics([[2.,2.,4.],[3.,2.,4.],[4.,2.,4.]],[[0,1,2]],[[3,3]],1.,1.,(12,12,12))
        self.assertEqual(r['exact_zero_area_triangles'],1)
        self.assertEqual(r['samples'][0]['status'],'absent')

    def test_missing_phi_is_not_filled(self):
        r=paired_residuals([dict(column=[3,3],status='supported',top_upward_triangle_height_m=1.)],
            [dict(column=[3,3],interface=dict(status='absent',crossings=[]))],.9)
        self.assertIsNone(r[0]['mesh_minus_phi_m']);self.assertIsNone(r[0]['phi_minus_initial_m'])

    def test_mismatched_column_rejected(self):
        with self.assertRaises(ValueError):paired_residuals([dict(column=[3,3])],[dict(column=[3,4])],.9)


if __name__=='__main__':unittest.main()
