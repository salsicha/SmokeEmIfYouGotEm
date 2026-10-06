from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tmp/south-fork-geospatial-deps'))
sys.path.insert(0,str(ROOT/'physics/scripts'))
import numpy as np
from south_fork_mesh_sampling import sample_triangles, select_bed_sampling, grid_triangles


class MeshSamplingTests(unittest.TestCase):
    def test_mesh_builder_uses_the_samplers_b_c_diagonal(self):
        np.testing.assert_array_equal(grid_triangles(2,3),[[0,1,3],[1,2,4],[1,4,3],[2,5,4]])
        with self.assertRaises(ValueError):grid_triangles(1,3)

    def test_export_records_and_checks_interpolation_identity(self):
        import sys
        from types import SimpleNamespace
        sys.path.insert(0,str(ROOT/'physics/src'))
        from export_south_fork_survey_review_fields import validate_bed_sampling
        scenario=SimpleNamespace(metadata=SimpleNamespace(provenance={'bed_sampling':'render_triangles'}))
        self.assertEqual(validate_bed_sampling({'bed_sampling':'render_triangles'},scenario),'render_triangles')
        with self.assertRaises(ValueError):validate_bed_sampling({},scenario)

    def test_new_cooks_use_mesh_but_old_histories_keep_their_sampling(self):
        self.assertEqual(select_bed_sampling(),'render_triangles')
        self.assertEqual(select_bed_sampling(parent_registration={}),'bilinear')
        self.assertEqual(select_bed_sampling(parent_registration={'bed_sampling':'render_triangles'}),'render_triangles')
        self.assertEqual(select_bed_sampling('bilinear'),'bilinear')
        self.assertEqual(select_bed_sampling('registered_triangles'),'registered_triangles')
        self.assertEqual(select_bed_sampling(parent_registration={'bed_sampling':'registered_triangles'}),'registered_triangles')
        with self.assertRaises(ValueError):select_bed_sampling(raw_resume=True)
        with self.assertRaises(ValueError):select_bed_sampling('unknown')
    def test_exact_vertices_including_last_row_and_column(self):
        values=np.arange(12.).reshape(3,4)**2
        rows,cols=np.indices(values.shape)
        np.testing.assert_array_equal(sample_triangles(values,rows,cols),values)

    def test_exported_diagonal_not_bilinear_saddle(self):
        values=np.array([[0.,0.],[0.,4.]])
        self.assertEqual(sample_triangles(values,.25,.25),0.)
        self.assertEqual(sample_triangles(values,.75,.75),2.)
        self.assertEqual(sample_triangles(values,.5,.5),0.)

    def test_planar_surface_and_triangle_seam(self):
        values=np.array([[1.,3.],[4.,6.]])
        row=np.array([0.,.2,.7,1.]);col=np.array([1.,.8,.3,0.])
        np.testing.assert_allclose(sample_triangles(values,row,col),1+2*col+3*row)
        np.testing.assert_allclose(sample_triangles(values,(row+1e-9)[1:-1],(col-1e-9)[1:-1]),
                                  (1+2*(col-1e-9)+3*(row+1e-9))[1:-1])

    def test_invalid_coordinates_rejected_instead_of_clamped(self):
        for row,col in ((-.01,0),(0,-.01),(1.01,0),(0,1.01),(np.nan,0),(0,np.inf)):
            with self.subTest(row=row,col=col):
                with self.assertRaises(ValueError):sample_triangles(np.ones((2,2)),row,col)
        with self.assertRaises(ValueError):sample_triangles(np.ones((1,2)),0,0)


if __name__=='__main__': unittest.main()
