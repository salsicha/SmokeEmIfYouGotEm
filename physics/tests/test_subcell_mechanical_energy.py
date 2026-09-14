import unittest
import numpy as np
from triangle_cell_storage import TriangleCellStorage, clip_polygon, projected_areas
from subcell_mechanical_energy import squared_depth_integral, energy
from subcell_geometry_patch import SubcellGeometryPatch
from test_triangle_face_section import sampler


class SubcellMechanicalEnergyTest(unittest.TestCase):
    def test_squared_depth_against_independent_clipped_quadrature(self):
        quadrature = np.full((3, 3), 1/6)+np.eye(3)*.5
        rng = np.random.default_rng(880)
        for heights in ([0, 0, 0], [0, 0, 2], [0, 1, 2], [0, 2, 2], *rng.normal(size=(30, 3))):
            triangle = np.array([[0., 0., heights[0]], [1., 0., heights[1]], [0., 1., heights[2]]])
            storage = TriangleCellStorage(triangle[None])
            for stage in np.linspace(min(heights)-.1, max(heights)+.1, 11):
                polygon = clip_polygon(triangle, 2, stage, False)
                pieces = np.array([polygon[[0, i, i+1]] for i in range(1, len(polygon)-1)]).reshape(-1, 3, 3)
                sampled_z = np.einsum('ij,tjk->tik', quadrature, pieces)[..., 2]
                expected = float(projected_areas(pieces)@np.mean((stage-sampled_z)**2, axis=1))
                np.testing.assert_allclose(squared_depth_integral(storage, stage), expected, atol=3e-14, rtol=3e-13)

    def test_thin_repeated_low_vertices_and_derivative(self):
        storage = TriangleCellStorage(np.array([[[0., 0., 0.], [1., 0., 0.], [0., 1., 2.]]]))
        for d in (1e-12, 1e-9, .1, 1.):
            expected = d**3/6-d**4/48
            np.testing.assert_allclose(squared_depth_integral(storage, d), expected, atol=0, rtol=2e-15)
        for d in (.1, .5, 1., 1.9, 2.5):
            derivative = (squared_depth_integral(storage, d+1e-5)-squared_depth_integral(storage, d-1e-5))/2e-5
            np.testing.assert_allclose(derivative, 2*storage.volume_and_wet_area(d)[0], atol=1e-10, rtol=1e-8)

    def test_energy_direction_uses_same_hydrostatic_storage(self):
        patch = SubcellGeometryPatch(sampler(lambda x, y: .3+np.sin(x)*np.cos(y)), [-.5, -.5], (2, 2))
        rng = np.random.default_rng(43)
        v, p = patch.state_from_stages(1., rng.normal(size=(2, 2, 2))*.2)
        dv, dp = rng.normal(size=v.shape)*.01, rng.normal(size=p.shape)*.01
        u = p/v[..., None]
        base = energy(patch, v, p)
        stage = np.array([c.stage_for_volume(x) for c, x in zip(patch.cells, v.ravel())]).reshape(v.shape)
        expected = np.sum((9.81*(stage-base['reference_datum_m'])-.5*np.sum(u*u, axis=-1))*dv)+np.sum(u*dp)
        measured = (energy(patch, v+1e-5*dv, p+1e-5*dp)['total']-energy(patch, v-1e-5*dv, p-1e-5*dp)['total'])/2e-5
        np.testing.assert_allclose(measured, expected, atol=2e-9, rtol=1e-8)

    def test_local_datum_energy_preserves_the_same_resolved_function(self):
        rng = np.random.default_rng(403)
        terrain = sampler(lambda x, y: 8.25+.3*np.sin(x)*np.cos(y))
        original = SubcellGeometryPatch(terrain, [-.5, -.5], (2, 2))
        relative = SubcellGeometryPatch(terrain, [-.5, -.5], (2, 2), relative_stages=True)
        v, p = original.state_from_stages(8.6, rng.normal(size=(2, 2, 2))*.2)
        for key in ('total', 'kinetic', 'potential'):
            self.assertAlmostEqual(energy(original, v, p)[key], energy(relative, v, p)[key], places=12)
        storage = TriangleCellStorage(np.array([[[0., 0., 8.], [1., 0., 8.], [0., 1., 10.]]]))
        for d in (1e-30, 1e-12, .1):
            np.testing.assert_allclose(squared_depth_integral(storage, d, True), d**3/6-d**4/48,
                                       atol=0, rtol=2e-15)


if __name__ == '__main__':
    unittest.main()
