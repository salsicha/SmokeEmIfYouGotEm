import unittest
import numpy as np
from triangle_cell_storage import TriangleCellStorage, cell_triangles, clip_polygon, projected_areas
from south_fork_registered_mesh import RegisteredMeshSampler


def mesh(z):
    y, x = np.meshgrid([1., 0., -1.], [-1., 0., 1.], indexing='ij')
    root = np.array([0, 1, 3, 4])
    return dict(east_m=x, north_m=y, z_m=z(x, y),
                nominal_east_axis_m=x[0], nominal_north_axis_m=y[:, 0],
                triangles=np.concatenate((np.stack((root, root+1, root+3), 1),
                                          np.stack((root+1, root+4, root+3), 1))))


class TriangleCellStorageTest(unittest.TestCase):
    def test_flat_cell_and_exact_zero(self):
        sampler = RegisteredMeshSampler(mesh(lambda x, y: x*0+3.))
        triangles = cell_triangles(sampler, [0, 0], [1, 1])
        storage = TriangleCellStorage(triangles)
        self.assertAlmostEqual(storage.area, 1.)
        self.assertEqual(storage.volume_and_wet_area(3.), (0., 0.))
        self.assertEqual(storage.stage_for_volume(0.), 3.)
        self.assertAlmostEqual(storage.stage_for_volume(.7), 3.7)
        self.assertAlmostEqual(storage.volume_and_wet_area(3.7)[0], .7)

    def test_ramp_exact_partial_wetting_and_inverse(self):
        sampler = RegisteredMeshSampler(mesh(lambda x, y: 2*x+1))
        triangles = cell_triangles(sampler, [0, 0], [1, 1])
        storage = TriangleCellStorage(triangles)
        for eta in (.001, .1, .7, 1., 1.9, 2.):
            volume, wet = storage.volume_and_wet_area(eta)
            self.assertAlmostEqual(volume, eta**2/4, places=13)
            self.assertAlmostEqual(wet, eta/2, places=13)
            self.assertAlmostEqual(storage.stage_for_volume(volume), eta, places=12)

    def test_formula_against_independent_polygon_integration(self):
        rng = np.random.default_rng(412)
        for heights in ([0, 0, 0], [0, 0, 2], [0, 2, 2], [0, 1, 2], *rng.normal(size=(30, 3))):
            triangle = np.array([[0., 0., heights[0]], [1., 0., heights[1]], [0., 1., heights[2]]])
            storage = TriangleCellStorage(triangle[None])
            for eta in np.linspace(min(heights)-.1, max(heights)+.1, 11):
                polygon = clip_polygon(triangle, 2, eta, False)
                pieces = np.asarray([polygon[[0, j, j+1]] for j in range(1, len(polygon)-1)]).reshape(-1, 3, 3)
                areas = projected_areas(pieces)
                volume = sum(areas*(eta-pieces[:, :, 2].mean(axis=1)))
                actual = storage.volume_and_wet_area(eta)
                # A flat dry triangle at eta has geometric area but no positive
                # depth. The derivative has a kink here; wet area is zero.
                wet_area = 0. if eta <= min(heights) else areas.sum()
                np.testing.assert_allclose(actual, [volume, wet_area], atol=2e-14, rtol=2e-13)

    def test_registered_vertices_and_diagonal_preserved(self):
        data = mesh(lambda x, y: x*x+y*y)
        data['east_m'][1, 1] += .24
        data['north_m'][1, 1] -= .15
        sampler = RegisteredMeshSampler(data)
        before = sampler.xyz.copy(), sampler.faces.copy()
        triangles = cell_triangles(sampler, [.1, -.1], [1.2, .8])
        for point in triangles.mean(axis=1):
            expected = sampler.sample(point[0]+.1, point[1]-.1)
            self.assertAlmostEqual(point[2], float(expected), places=13)
        np.testing.assert_array_equal(sampler.xyz, before[0])
        np.testing.assert_array_equal(sampler.faces, before[1])
        self.assertAlmostEqual(projected_areas(triangles).sum(), .96, places=13)

    def test_volume_derivative_translation_and_thin_water(self):
        triangles = np.array([[[0., 0., 0.], [1., 0., 1.], [0., 1., 2.]]])
        storage = TriangleCellStorage(triangles)
        for eta in (.2, .8, 1.2, 1.8, 2.2):
            plus = storage.volume_and_wet_area(eta+1e-5)[0]
            minus = storage.volume_and_wet_area(eta-1e-5)[0]
            self.assertAlmostEqual((plus-minus)/2e-5, storage.volume_and_wet_area(eta)[1], places=9)
        shifted = triangles+np.array([8, -10, 220])
        other = TriangleCellStorage(shifted)
        for volume in (1e-18, 1e-9, .1, 2.):
            eta = storage.stage_for_volume(volume)
            np.testing.assert_allclose(storage.volume_and_wet_area(eta)[0], volume, atol=1e-28, rtol=2e-12)
            self.assertAlmostEqual(other.stage_for_volume(volume)-220, eta, places=12)

    def test_shallow_water_on_repeated_low_vertices_does_not_cancel(self):
        triangles = np.array([[[0., 0., 0.], [1., 0., 0.], [0., 1., 2.]]])
        storage = TriangleCellStorage(triangles)
        for eta in (1e-12, 1e-9, 1e-6, .1, 1.):
            # Independent analytic integral along the horizontal isobaths:
            # integral_0^(eta/2) (eta-2*y)*(1-y) dy.
            expected = eta*eta/4-eta**3/24
            np.testing.assert_allclose(storage.volume_and_wet_area(eta)[0], expected, atol=0, rtol=2e-15)
            np.testing.assert_allclose(storage.stage_for_volume(expected), eta, atol=0, rtol=2e-14)

    def test_missing_coverage_and_bad_state_fail(self):
        sampler = RegisteredMeshSampler(mesh(lambda x, y: x*0))
        for center, size in (([1, 1], [1, 1]), ([0, 0], [0, 1]), ([np.nan, 0], [1, 1])):
            with self.assertRaises(ValueError):
                cell_triangles(sampler, center, size)
        storage = TriangleCellStorage(cell_triangles(sampler, [0, 0], [1, 1]))
        for volume in (-1., np.inf, np.nan):
            with self.assertRaises(ValueError):
                storage.stage_for_volume(volume)


if __name__ == '__main__':
    unittest.main()
