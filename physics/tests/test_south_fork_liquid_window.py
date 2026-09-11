"""Geometry/coupling invariants; these do not establish visual acceptance."""
from pathlib import Path
import sys
import unittest
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from build_south_fork_liquid_window import closed_patch, bilinear, boundary_profiles, apply_native_boundary_flux
from build_south_fork_liquid_sources import split_face_discharge


class LiquidWindowTests(unittest.TestCase):
    def test_native_flux_replaces_interpolated_dry_face_leak_without_inventing_water(self):
        import copy
        row={'resolved_depth_m':0.,'outward_discharge_m3_per_s':.5,'dry_flux_conflict':True}
        profiles=[{'samples':[copy.deepcopy(row),dict(row,resolved_depth_m=1.)],'sample_width_m':.5} for _ in range(4)]
        audit={'passed':True,'local_station_lateral_face_bounds_m':[[-1,-1],[1,1]],
               'face_discharge_m3_per_s':{name:[0.,q] for name,q in zip(('west','east','south','north'),(2.,-2.,3.,-3.))}}
        apply_native_boundary_flux(profiles,audit,[[-1,-1],[1,1]])
        for profile in profiles:
            self.assertEqual(profile['samples'][0]['outward_discharge_m3_per_s'],0)
            self.assertFalse(profile['samples'][0]['dry_flux_conflict'])
            self.assertTrue(profile['samples'][0]['interpolated_dry_flux_conflict'])
        self.assertEqual(sum(p['inflow_m3_per_s'] for p in profiles),5)
        self.assertEqual(sum(p['outflow_m3_per_s'] for p in profiles),5)
        audit['face_discharge_m3_per_s']['west'][0]=1.
        with self.assertRaisesRegex(ValueError,'wet support'):
            apply_native_boundary_flux(profiles,audit,[[-1,-1],[1,1]])
        with self.assertRaisesRegex(ValueError,'requested domain'):
            apply_native_boundary_flux(profiles,audit,[[-2,-1],[1,1]])

    def test_rectangular_collision_preserves_surface_and_volume(self):
        vertices = np.array([[-4,-4,0],[-4,4,4],[4,4,8],[4,-4,4]], dtype=float)
        points, faces, count, _ = closed_patch(vertices,np.array([[0,1,2],[0,2,3]]),[3,1],-1)
        top = points[faces[:count]].reshape(-1,3)
        np.testing.assert_allclose(top[:,2],.5*top[:,0]+.5*top[:,1]+4,atol=1e-12)
        self.assertLessEqual(abs(top[:,0]).max(),3)
        self.assertLessEqual(abs(top[:,1]).max(),1)
        volume = abs(np.einsum('ij,ij->i',points[faces[:,0]],np.cross(points[faces[:,1]],points[faces[:,2]])).sum()/6)
        self.assertAlmostEqual(volume,60.)

    def test_rectangular_offset_faces_preserve_both_flux_components(self):
        grid={'origin_x_m':-10.,'origin_y_m':-10.,'dx_m':1.,'dy_m':1.}
        fields={'h':np.full((21,21),2.),'u':np.full((21,21),3.),
                'v':np.full((21,21),-2.),'bed':np.ones((21,21))}
        class Bed:
            def sample(self,x,y):return np.ones_like(x)
        profiles=boundary_profiles(fields,grid,[2.,-1.],[8.,4.],.5,Bed(),np.array([1,0]),np.array([0,1]))
        self.assertEqual([len(p['samples']) for p in profiles],[8,8,16,16])
        self.assertEqual([p['inflow_m3_per_s'] for p in profiles],[24,0,0,32])
        self.assertEqual([p['outflow_m3_per_s'] for p in profiles],[0,24,32,0])
        self.assertEqual(profiles[0]['samples'][0]['station_lateral_m'],[-2.,-2.75])
        self.assertEqual(profiles[3]['samples'][-1]['station_lateral_m'],[5.75,1.])
        anisotropic=boundary_profiles(fields,grid,[2.,-1.],[8.,4.],[.25,.5],Bed(),np.array([1,0]),np.array([0,1]))
        self.assertEqual([len(p['samples']) for p in anisotropic],[8,8,32,32])
        self.assertEqual([p['inflow_m3_per_s'] for p in anisotropic],[24,0,0,32])

    def test_bad_rectangular_extents_and_partial_boundary_cells_rejected(self):
        from build_south_fork_liquid_window import positive_xy
        for value in ([1,0],[1,-1],[1,float('nan')],[1,2,3]):
            with self.assertRaises(ValueError):positive_xy(value,'test')
        with self.assertRaisesRegex(ValueError,'Whole boundary cells'):
            boundary_profiles({}, {}, [0,0], [3.1,4], .5, None, None, None)

    def test_subface_flux_preserves_both_signs_and_excludes_dry_support(self):
        for discharge in (-7., 0., 7.):
            flux, speed = split_face_discharge(discharge, [0., .5, 2., 0.], .125)
            self.assertAlmostEqual(flux.sum(), discharge)
            np.testing.assert_allclose(flux, [0, discharge*.2, discharge*.8, 0])
            self.assertAlmostEqual(speed*.3125, discharge)

    def test_subface_flux_rejects_missing_wet_support_and_bad_inputs(self):
        with self.assertRaisesRegex(ValueError, 'wet support'):
            split_face_discharge(1., [0., 0.], .125)
        flux, speed = split_face_discharge(0., [0., 0.], .125)
        np.testing.assert_array_equal(flux, [0., 0.])
        self.assertEqual(speed, 0.)
        for width in (0., -1., float('nan'), float('inf')):
            with self.assertRaises(ValueError):
                split_face_discharge(0., [1.], width)
        for depth in (-1., float('nan'), float('inf')):
            with self.assertRaises(ValueError):
                split_face_discharge(1., [depth], .125)

    def test_clipped_top_preserves_sloped_source_and_closed_volume(self):
        vertices = np.array([[-2,-2,0],[-2,2,2],[2,2,4],[2,-2,2]], dtype=float)
        points, faces, count, sources = closed_patch(vertices, np.array([[0,1,2],[0,2,3]]), 1, -1)
        top = points[faces[:count]].reshape(-1,3)
        np.testing.assert_allclose(top[:,2], .5*top[:,0]+.5*top[:,1]+2, atol=1e-12)
        self.assertEqual(len(sources), count)
        volume = abs(np.einsum('ij,ij->i', points[faces[:,0]],
            np.cross(points[faces[:,1]], points[faces[:,2]])).sum()/6)
        self.assertAlmostEqual(volume, 12.)

    def test_incomplete_source_coverage_cannot_be_silently_sealed(self):
        with self.assertRaisesRegex(ValueError, 'coverage'):
            closed_patch(np.array([[-2,-2,0],[-2,2,0],[2,2,0]], dtype=float),
                         np.array([[0,1,2]]), 1, -1)

    def test_bottom_cannot_cut_into_the_surface(self):
        with self.assertRaisesRegex(ValueError, 'strictly lower'):
            closed_patch(np.array([[-2,-2,0],[-2,2,0],[2,2,0],[2,-2,0]], dtype=float),
                         np.array([[0,1,2],[0,2,3]]), 1, 0)

    def test_cell_centres_and_linear_sampling(self):
        grid = {'origin_x_m': -2., 'origin_y_m': -2., 'dx_m': 1., 'dy_m': 1.}
        x, y = np.meshgrid(np.arange(5)-2, np.arange(5)-2)
        values = 3*x-2*y+7
        np.testing.assert_allclose(bilinear(values, np.array([.25,-.75]), np.array([.5,-1]),grid), [6.75,6.75])
        with self.assertRaises(ValueError):
            bilinear(values, -3, 0, grid)

    def test_uniform_channel_has_balanced_momentum_flux(self):
        grid = {'origin_x_m': -3., 'origin_y_m': -3., 'dx_m': 1., 'dy_m': 1.}
        fields = {'h': np.full((7,7),2.), 'u': np.full((7,7),3.),
                  'v': np.zeros((7,7)), 'bed': np.ones((7,7))}
        class Bed:
            def sample(self,x,y): return np.ones_like(x)
        profiles = boundary_profiles(fields, grid, np.zeros(2), 4, .5, Bed(),
                                     np.array([1,0]),np.array([0,1]))
        self.assertAlmostEqual(sum(p['inflow_m3_per_s'] for p in profiles),24)
        self.assertAlmostEqual(sum(p['outflow_m3_per_s'] for p in profiles),24)
        self.assertEqual(sum(p['dry_flux_conflicts'] for p in profiles),0)

    def test_dry_actual_bed_does_not_hide_nonzero_source_flux(self):
        grid = {'origin_x_m': -3., 'origin_y_m': -3., 'dx_m': 1., 'dy_m': 1.}
        fields = {'h': np.ones((7,7)), 'u': np.ones((7,7)),
                  'v': np.zeros((7,7)), 'bed': np.zeros((7,7))}
        class HighBed:
            def sample(self,x,y): return np.full_like(x,2.)
        profiles = boundary_profiles(fields, grid, np.zeros(2), 4, .5, HighBed(),
                                     np.array([1,0]),np.array([0,1]))
        self.assertEqual(sum(p['dry_flux_conflicts'] for p in profiles),16)


if __name__ == '__main__':
    unittest.main()
