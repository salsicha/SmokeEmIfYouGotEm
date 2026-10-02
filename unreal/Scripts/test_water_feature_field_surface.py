import unittest
import numpy as np
from water_feature_field_surface import sample_centers,interface_residuals,planar_case,refine_lattice,regularize_exact_mesh


class FieldSurfaceTests(unittest.TestCase):
    def test_affine_field_at_arbitrary_subcell_positions(self):
        phi,n=planar_case((12,12,12),(1,2,3),6.)
        p=np.array([[3.1,4.8,2.7],[6.2,5.1,7.3]])
        np.testing.assert_allclose(sample_centers(phi,p),p@n-6.,atol=2e-7,rtol=0)

    def test_outside_support_rejected_not_clamped(self):
        with self.assertRaises(ValueError):sample_centers(np.ones((12,12,12)),[[.1,4,5]])

    def test_last_original_knot_is_supported_but_exterior_is_not(self):
        a=np.arange(8**3).reshape((8,8,8))
        self.assertEqual(sample_centers(a,[[7.5,7.5,7.5]])[0],a[-1,-1,-1])
        with self.assertRaises(ValueError):sample_centers(a,[[7.5+1e-7,7.5,7.5]])

    def test_plane_zero_residual(self):
        p=np.array([[2.,2.,6.3],[7.,2.,6.3],[2.,7.,6.3]])
        phi,_=planar_case((12,12,12),(0,0,1),6.3)
        r=interface_residuals(phi,np.ones(phi.shape),p,[[0,1,2]])
        self.assertLess(r['vertices']['composite_residual_abs_cells_quantiles'][-1],2e-7)

    def test_solid_overlap_is_not_hidden(self):
        p=np.array([[2.,2.,6.],[7.,2.,6.],[2.,7.,6.]])
        phi,_=planar_case((12,12,12),(0,0,1),6.)
        r=interface_residuals(phi,-np.ones(phi.shape),p,[[0,1,2]])
        self.assertEqual(r['vertices']['maximum_inside_solid_phi_cells'],1.)

    def test_sampling_max_changes_contact_intersection(self):
        x=np.broadcast_to(np.arange(12)[:,None,None]+.5-6,(12,12,12)).copy()
        z=np.broadcast_to(np.arange(12)[None,None,:]+.5-6,(12,12,12)).copy()
        points=np.array([[6.,5.,6.]])
        value=sample_centers(np.maximum(x,z),points)[0]
        self.assertEqual(max(sample_centers(x,points)[0],sample_centers(z,points)[0]),0.)
        self.assertEqual(value,.25) # Retain the contact sampling error; no false exact-CSG claim.

    def test_zero_normal_refused(self):
        with self.assertRaises(ValueError):planar_case((12,12,12),(0,0,0),6.)

    def test_refinement_preserves_every_original_knot(self):
        array=np.random.default_rng(17).normal(size=(8,9,10)).astype(np.float32)
        for r in (1,2,4):
            fine,offset=refine_lattice(array,r)
            np.testing.assert_array_equal(fine[::r,::r,::r],array)
            self.assertEqual(fine.shape,tuple((n-1)*r+1 for n in array.shape))
            self.assertEqual(.5/r+offset,.5)

    def test_refined_nonlinear_field_matches_original_interpolation(self):
        xyz=np.stack(np.meshgrid(*[np.arange(8)+.5 for _ in range(3)],indexing='ij'),axis=-1)
        array=(xyz[...,0]**2+xyz[...,1]*xyz[...,2]).astype(np.float32)
        p=np.array([[2.7,3.25,5.8],[4.1,6.3,2.9]])
        for r in (2,4):
            fine,offset=refine_lattice(array,r)
            np.testing.assert_allclose(sample_centers(fine,(p-offset)*r),sample_centers(array,p),atol=1e-6,rtol=0)

    def test_exact_cleanup_keeps_tetrahedral_surface(self):
        vertices=np.array([[0,0,0],[1,0,0],[0,1,0],[0,0,1],[0,0,0]],dtype=float)
        faces=np.array([[4,2,1],[4,1,3],[1,2,3],[2,4,3],[0,4,1]])
        v,t,proof=regularize_exact_mesh(vertices,faces)
        self.assertEqual((len(v),len(t)),(4,4))
        self.assertEqual(proof['exact_zero_area_faces_removed'],1)
        self.assertAlmostEqual(proof['native_signed_volume_after'],1/6)

    def test_nearby_coordinates_are_never_welded(self):
        vertices=np.array([[0.,0,0],[1,0,0],[0,1,0],[0,0,1e-12]])
        v,t,proof=regularize_exact_mesh(vertices,[[0,1,2],[3,1,2]])
        self.assertEqual(len(v),4);self.assertEqual(len(t),2)
        self.assertEqual(proof['duplicate_vertices_merged'],0)


if __name__=='__main__':unittest.main()
