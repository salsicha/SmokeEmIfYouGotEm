import sys
import unittest
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from liquid_anisotropic_surface import fit_kernels, cubic_kernel, splat_density, upper_surface, filter_kernels
from compare_liquid_surface_reconstruction import compare, main_liquid_body


class AnisotropicSurfaceTest(unittest.TestCase):
    def test_weighted_sparse_transition_removes_neighbor_boundary_jump(self):
        theta=np.arange(24)*2*np.pi/24
        ring=np.stack((.35*np.cos(theta),.35*np.sin(theta),np.zeros(24)),axis=-1)
        fields=[]
        for smooth in (False,True):
            axes=[]
            for offset in (-1e-6,1e-6):
                points=np.vstack(([0,0,0],ring,[.8+offset,0,0]))
                fit=fit_kernels(points,.4,smoothing=0,smooth_sparse=smooth)
                np.testing.assert_array_equal(fit['centers'],points)
                axes.append(fit['axes'][0])
            fields.append(np.max(abs(axes[0]-axes[1])))
        self.assertGreater(fields[0],.05)
        self.assertLess(fields[1],1e-5)

    def test_continuous_sparse_preserves_isolated_volume_and_dense_limit(self):
        for points in (np.array([[0.,0.,0.]]),np.random.default_rng(12).normal(0,.08,(150,3))):
            old=fit_kernels(points,.4,smoothing=0)
            new=fit_kernels(points,.4,smoothing=0,smooth_sparse=True)
            np.testing.assert_array_equal(old['sample_volumes'],new['sample_volumes'])
            np.testing.assert_allclose(old['axes'],new['axes'])

    def test_sparse_droplet_stays_spherical_and_stationary(self):
        points = np.array([[0., 0., 0.], [3., 0., 0.]])
        fit = fit_kernels(points, .4)
        np.testing.assert_array_equal(fit['centers'], points)
        np.testing.assert_allclose(fit['axes'], .2)
        self.assertTrue(fit['sparse'].all())

    def test_planar_sheet_flattens_kernels_without_moving_physics(self):
        y, x = np.meshgrid(np.arange(-.6, .61, .1), np.arange(-.6, .61, .1))
        points = np.stack((x.ravel(), y.ravel(), np.zeros(x.size)), axis=1)
        original = points.copy()
        fit = fit_kernels(points, .4)
        center = np.argmin(np.linalg.norm(points, axis=1))
        self.assertGreater(fit['matrix'][center, 2, 2], 2*fit['matrix'][center, 0, 0])
        self.assertLessEqual(np.max(fit['axes'][:, -1]/fit['axes'][:, 0]), 4+1e-12)
        np.testing.assert_array_equal(points, original)

    def test_rotation_translation_and_unit_equivariance(self):
        rng = np.random.default_rng(2010)
        points = rng.normal(size=(150, 3))*[.25, .2, .05]
        q, _ = np.linalg.qr(rng.normal(size=(3, 3)))
        fit = fit_kernels(points, .4)
        moved = fit_kernels(points@q.T+[3, -2, 1], .4)
        np.testing.assert_allclose(moved['centers'], fit['centers']@q.T+[3, -2, 1], atol=1e-12)
        np.testing.assert_allclose(moved['matrix'], q@fit['matrix']@q.T, atol=1e-10)
        scaled = fit_kernels(points*100, 40)
        np.testing.assert_allclose(scaled['matrix'], fit['matrix']/100, atol=1e-12)

    def test_kernel_integral_and_ellipsoid_mass(self):
        q = np.linspace(0, 1, 10001)
        self.assertAlmostEqual(float(np.trapezoid(4*np.pi*q*q*cubic_kernel(q), q)), 1, places=8)
        kernels = dict(centers=np.zeros((1, 3)), matrix=np.array([np.diag([2., 3., 5.])]),
                       axes=np.array([[.5, 1/3, .2]]), basis=np.eye(3)[None])
        density = splat_density(kernels, .008, [-.6]*3, [1.2]*3, [96]*3)
        self.assertAlmostEqual(float(density.sum()*(1.2/96)**3), .008, delta=2e-6)

    def test_invalid_input_rejected(self):
        for points, radius in [(np.empty((0, 3)), .4), ([[np.nan, 0, 0]], .4), ([[0, 0, 0]], 0)]:
            with self.assertRaises(ValueError):
                fit_kernels(points, radius)

    def test_density_weight_is_invariant_to_duplicate_sampling(self):
        rng = np.random.default_rng(8)
        points = rng.uniform(-.2, .2, (80, 3))
        fit = fit_kernels(points, .4)
        doubled = fit_kernels(np.repeat(points, 2, axis=0), .4)
        np.testing.assert_allclose(doubled['sample_volumes'][::2], fit['sample_volumes']/2)
        density = splat_density(fit, fit['sample_volumes'], [-.6]*3, [1.2]*3, [32]*3)
        duplicate_density = splat_density(doubled, doubled['sample_volumes'], [-.6]*3, [1.2]*3, [32]*3)
        np.testing.assert_allclose(density, duplicate_density, atol=1e-11)

    def test_coincident_particles_use_finite_spherical_fallback(self):
        fit = fit_kernels(np.zeros((40, 3)), .4)
        self.assertTrue(fit['degenerate'].all())
        np.testing.assert_allclose(fit['axes'], .2)
        np.testing.assert_allclose(fit['sample_volumes'], .4**3/(40*cubic_kernel(0)))

    def test_unshifted_candidate_changes_only_render_center_policy(self):
        points = np.random.default_rng(4).uniform(-.3, .3, (100, 3))
        shifted = fit_kernels(points, .4)
        unshifted = fit_kernels(points, .4, smoothing=0)
        np.testing.assert_array_equal(unshifted['centers'], points)
        np.testing.assert_array_equal(unshifted['matrix'], shifted['matrix'])
        np.testing.assert_array_equal(unshifted['sample_volumes'], shifted['sample_volumes'])

    def test_prefilter_matches_voxel_covariance_and_preserves_centers(self):
        fit = fit_kernels(np.random.default_rng(5).uniform(-.3, .3, (100, 3)), .4, smoothing=0)
        filtered = filter_kernels(fit, .16)
        basis = fit['basis']
        original_covariance = np.einsum('nik,nk,njk->nij', basis, .075*fit['axes']**2, basis)
        filtered_covariance = np.einsum('nik,nk,njk->nij', basis, .075*filtered['axes']**2, basis)
        np.testing.assert_allclose(filtered_covariance-original_covariance,
                                   np.broadcast_to(np.eye(3)*.16**2/12, (100, 3, 3)), atol=1e-15)
        np.testing.assert_array_equal(filtered['centers'], fit['centers'])
        np.testing.assert_array_equal(filtered['sample_volumes'], fit['sample_volumes'])
        np.testing.assert_allclose(filter_kernels(fit, 0)['matrix'], fit['matrix'])
        self.assertGreaterEqual(filtered['axes'].min(), .16/np.sqrt(.9))

    def test_prefilter_rejects_invalid_footprints(self):
        fit = fit_kernels([[0., 0., 0.]], .4)
        for footprint in (-1, np.nan, np.inf):
            with self.assertRaises(ValueError):
                filter_kernels(fit, footprint)

    def test_volume_array_validation(self):
        fit = fit_kernels([[0., 0., 0.]], .4)
        for volumes in ([1., 2.], [np.nan], [0.], [-1.]):
            with self.assertRaises(ValueError):
                splat_density(fit, volumes, [-1]*3, [2]*3, [10]*3)

    def test_upper_crossing_uses_highest_interface_and_voxel_centers(self):
        density = np.array([1., 0., 1., .75, .25, 0.])[:, None, None]
        surface = upper_surface(density, [0, 0, 10], [1, 1, 12])
        self.assertEqual(surface[0, 0], 18.)
        self.assertTrue(np.isnan(upper_surface(np.ones((3, 1, 1)), [0]*3, [1]*3)).all())
        self.assertTrue(np.isnan(upper_surface(np.zeros((3, 1, 1)), [0]*3, [1]*3)).all())

    def test_grid_comparison_is_exact_for_affine_surface(self):
        def grid(n):
            z, y, x = np.meshgrid(*([np.arange(n)+.5]*3), indexing='ij')
            return dict(density=.5+.6+.1*x/n+.05*y/n-z/n,
                        minimum=np.zeros(3), extent=np.ones(3), cells=np.full(3, n),
                        centers=np.zeros((1, 3)), matrix=np.eye(3)[None], sample_volumes=np.ones(1))
        report = compare(grid(8), grid(16))
        self.assertLess(report['height_change_rms_m'], 1e-14)
        self.assertEqual(report['common_columns'], 64)
        changed = grid(16)
        changed['minimum'][0] = 1
        with self.assertRaises(ValueError):
            compare(grid(8), changed)

    def test_main_body_separates_droplet_without_changing_source(self):
        density = np.full((8, 8, 8), .1)
        density[1:4, 1:4, 1:4] = .9
        density[6, 6, 6] = 1.
        original = density.copy()
        field, stats = main_liquid_body(density)
        self.assertEqual(stats, dict(component_count=2, main_body_voxels=27, detached_liquid_voxels=1))
        self.assertEqual(field[6, 6, 6], 0.)
        self.assertEqual(field[4, 3, 3], .1)
        np.testing.assert_array_equal(density, original)


if __name__ == '__main__':
    unittest.main()
