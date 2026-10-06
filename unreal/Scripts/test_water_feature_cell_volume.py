"""Independent analytic checks for volume quadrature, not hydraulic acceptance."""
import unittest
import numpy as np
from water_feature_cell_volume import reconstructed_volume, reconstructed_volume_bounds


class VolumeTests(unittest.TestCase):
    def test_interval_contributions_partition_full_domain(self):
        xyz = np.meshgrid(*[np.array((.5, 1.5, 2.5))]*3, indexing='ij')
        phi = xyz[0]+xyz[1]-.9
        for field in (phi, -np.ones_like(phi), np.ones_like(phi)):
            row = reconstructed_volume(field, np.ones_like(field), (1, 2, 3), 8,
                                       return_interval_volumes=True)
            intervals = row['interval_volumes_m3']
            self.assertEqual(intervals.shape, (4, 4, 4))
            self.assertAlmostEqual(intervals.sum(), row['volume_m3'])
            self.assertTrue((intervals >= 0).all())
        full = reconstructed_volume(-np.ones_like(phi), np.ones_like(phi), (1, 2, 3), 8,
                                    return_interval_volumes=True)['interval_volumes_m3']
        self.assertEqual(full[0, 0, 0], .75)
        self.assertEqual(full[1, 1, 1], 6.)

    def test_full_and_empty_anisotropic_domain(self):
        phi = -np.ones((3, 4, 5))
        solid = np.ones_like(phi)
        row = reconstructed_volume(phi, solid, (.2, .3, .4))
        self.assertAlmostEqual(row['volume_m3'], .6*1.2*2.)
        self.assertAlmostEqual(row['covered_domain_volume_m3'], .6*1.2*2.)
        self.assertEqual(reconstructed_volume(-phi, solid, (.2, .3, .4))['volume_m3'], 0)
        self.assertEqual(reconstructed_volume(phi, -solid, (.2, .3, .4))['volume_m3'], 0)
        bound = reconstructed_volume_bounds(phi, solid, (.2, .3, .4))
        self.assertAlmostEqual(bound['lower_m3'], row['volume_m3'])
        self.assertAlmostEqual(bound['upper_m3'], row['volume_m3'])

    def test_plane_with_solid_intersection_and_outer_half_cells(self):
        spacing = np.array((.2, .3, .4))
        xyz = np.meshgrid((np.arange(5)+.5)*spacing[0],
                          (np.arange(6)+.5)*spacing[1],
                          (np.arange(7)+.5)*spacing[2], indexing='ij')
        # Liquid x<.63, outside obstacle y>.47. Exact rectangular intersection.
        phi, solid = xyz[0]-.63, xyz[1]-.47
        exact = .63*(1.8-.47)*2.8
        errors = []
        for n in (2, 4, 8, 16, 32):
            row = reconstructed_volume(phi, solid, spacing, n)
            errors.append(abs(row['volume_m3']-exact))
            # Independent bound from midpoint error in each planar dimension.
            bound = (.2/(2*n)*1.8+.3/(2*n)*1.)*2.8
            self.assertLessEqual(errors[-1], bound)
        self.assertLess(errors[-1], errors[0])
        previous_width = None
        for n in (2, 4, 8, 16):
            bound = reconstructed_volume_bounds(phi, solid, spacing, n)
            self.assertLessEqual(bound['lower_m3'], exact)
            self.assertGreaterEqual(bound['upper_m3'], exact)
            sampled = reconstructed_volume(phi, solid, spacing, n)['volume_m3']
            self.assertLessEqual(bound['lower_m3'], sampled)
            self.assertGreaterEqual(bound['upper_m3'], sampled)
            if previous_width is not None:
                self.assertLessEqual(bound['width_m3'], previous_width+1e-12)
            previous_width = bound['width_m3']

    def test_sphere_spatial_refinement(self):
        exact = 4*np.pi*.5**3/3
        errors = []
        for cells in (16, 32):
            h = 2./cells
            xyz = np.meshgrid(*[(np.arange(cells)+.5)*h-1]*3, indexing='ij')
            phi = np.sqrt(sum(a*a for a in xyz))-.5
            row = reconstructed_volume(phi, np.ones_like(phi), (h, h, h), 8)
            errors.append(abs(row['volume_m3']-exact)/exact)
        self.assertLess(errors[1], errors[0])
        self.assertLess(errors[1], .015)

    def test_oblique_plane_with_constant_edge_extension(self):
        xyz = np.meshgrid(*[np.array((.5, 1.5))]*3, indexing='ij')
        phi = sum(xyz)-1.8
        solid = np.ones_like(phi)
        # On [0,2]^3 each clamped coordinate minus .5 has an atom of
        # length .5 at zero plus uniform density on (0,1). The upper atom
        # at one cannot contribute to sum<.3. Integrate the k-dimensional
        # simplex for each of the 0..3 continuous-coordinate combinations.
        def exact_at(s):
            return .5**3+3*.5**2*s+3*.5*s**2/2+s**3/6
        exact = exact_at(.3)
        bound = reconstructed_volume_bounds(phi, solid, (1, 1, 1), 32)
        self.assertLessEqual(bound['lower_m3'], exact)
        self.assertGreaterEqual(bound['upper_m3'], exact)
        sampled = reconstructed_volume(phi, solid, (1, 1, 1), 32)['volume_m3']
        self.assertLessEqual(bound['lower_m3'], sampled)
        self.assertGreaterEqual(bound['upper_m3'], sampled)
        # Within a fine interval, the sum of the three clamped coordinates
        # differs from its midpoint by at most 3/(2*n). Independently bound
        # midpoint error by moving the analytic plane that far in either direction.
        delta = 3/(2*32)
        self.assertGreaterEqual(sampled, exact_at(.3-delta))
        self.assertLessEqual(sampled, exact_at(.3+delta))
        coarse = reconstructed_volume(phi, solid, (1, 1, 1), 8)['volume_m3']
        self.assertLess(abs(sampled-exact), abs(coarse-exact))

    def test_invalid_fields(self):
        phi = np.ones((3, 4, 5))
        for spacing in ((1, 0, 1), (1, np.nan, 1)):
            with self.assertRaises(ValueError):
                reconstructed_volume(phi, phi, spacing)
        with self.assertRaises(ValueError):
            reconstructed_volume(phi, phi[:, :, :3], (1, 1, 1))
        phi[0, 0, 0] = np.nan
        with self.assertRaises(ValueError):
            reconstructed_volume(phi, phi, (1, 1, 1))


if __name__ == '__main__':
    unittest.main()
