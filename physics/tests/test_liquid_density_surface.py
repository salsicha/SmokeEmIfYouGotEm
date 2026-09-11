import sys
import unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from liquid_density_surface import triangles_from_density,triangle_distance_squared,narrow_band_distance
from prepare_liquid_surface_baseline import geometry_only_volume


class DensitySurfaceTest(unittest.TestCase):
    def test_captured_baseline_preserves_distance_bits_and_source(self):
        rgba = np.random.default_rng(4).uniform(-2,2,(4,4,4,4)).astype('<f2')
        original = rgba.copy()
        output = geometry_only_volume(rgba)
        np.testing.assert_array_equal(output[...,0].view('u2'),rgba[...,0].view('u2'))
        np.testing.assert_array_equal(output[...,1:],0)
        np.testing.assert_array_equal(rgba,original)
        rgba[0,0,0,0]=np.nan
        with self.assertRaises(ValueError):
            geometry_only_volume(rgba)

    def test_point_triangle_regions(self):
        triangle = np.array([[0.,0.,0.],[1.,0.,0.],[0.,1.,0.]])
        points = np.array([[.2,.2,2.],[2.,0.,0.],[1.,1.,0.],[-1.,-1.,0.]])
        np.testing.assert_allclose(triangle_distance_squared(points,triangle),[4.,1.,.5,2.])

    def test_affine_surface_is_exact_and_faces_outward(self):
        z,y,x = np.meshgrid(*([np.arange(8)+.5]*3),indexing='ij')
        phi = (z+.2*x+.1*y-4.72)/8
        density = .5-phi
        triangles = triangles_from_density(density,[0]*3,[1]*3)
        np.testing.assert_allclose(triangles[:,:,2]+.2*triangles[:,:,0]+.1*triangles[:,:,1],4.72/8,atol=1e-14)
        normals = np.cross(triangles[:,1]-triangles[:,0],triangles[:,2]-triangles[:,0])
        self.assertTrue((normals@np.array([.2,.1,1.]) > 0).all())
        sdf = narrow_band_distance(density,triangles,[0]*3,[1]*3,.25)
        interior = np.s_[:,2:6,2:6]
        np.testing.assert_allclose(sdf[interior],np.clip(phi/np.sqrt(1.05),-.25,.25)[interior],atol=1e-12)

    def test_constant_fields_have_no_fictitious_surface(self):
        for value,sign in ((0.,1.),(1.,-1.)):
            density = np.full((4,4,4),value)
            triangles = triangles_from_density(density,[0]*3,[1]*3)
            self.assertEqual(len(triangles),0)
            np.testing.assert_allclose(narrow_band_distance(density,triangles,[0]*3,[1]*3,.25),sign*.25)

    def test_closed_sphere_mesh_has_two_faces_per_edge(self):
        z,y,x = np.meshgrid(*([(np.arange(12)+.5)/12-.5]*3),indexing='ij')
        density = .5+.3**2-x*x-y*y-z*z
        triangles = triangles_from_density(density,[-.5]*3,[1]*3)
        _,index = np.unique(np.round(triangles.reshape(-1,3),12),axis=0,return_inverse=True)
        faces = index.reshape(-1,3)
        edges = np.sort(np.concatenate((faces[:,[0,1]],faces[:,[1,2]],faces[:,[2,0]])),axis=1)
        _,counts = np.unique(edges,axis=0,return_counts=True)
        np.testing.assert_array_equal(counts,2)


if __name__ == '__main__':
    unittest.main()
