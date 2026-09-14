import unittest
import numpy as np
from triangle_cell_storage import TriangleCellStorage
from triangle_face_section import TriangleFaceSection
from subcell_geometry_patch import SubcellGeometryPatch
from subcell_implicit_transport import frozen_system
from test_triangle_face_section import sampler


class SubcellRelativeStageTest(unittest.TestCase):
    def test_tiny_volume_retains_pressure_without_absolute_elevation_floor(self):
        datum = 8.233870004582505
        triangle = np.array([[[0., 0., datum], [1., 0., datum+1], [0., 1., datum+2]]])
        storage = TriangleCellStorage(triangle)
        target = 1e-53
        old = storage.volume_and_wet_area(storage.stage_for_volume(target))[0]
        self.assertGreater(old/target, 1e6)
        for volume in (1e-300, 1e-200, 1e-100, target, 1e-18, .01, 2.):
            height = storage.relative_stage_for_volume(volume)
            represented = storage.relative_volume_and_wet_area(height)[0]
            np.testing.assert_allclose(represented, volume, rtol=2e-14, atol=0)
            force = storage.hydrostatic_bed_force(height, relative=True)
            np.testing.assert_allclose(force/volume, [-9.81, -19.62], rtol=2e-14, atol=0)
        np.testing.assert_array_equal(triangle, [[[0., 0., datum], [1., 0., datum+1], [0., 1., datum+2]]])

    def test_relative_face_keeps_arbitrarily_small_wet_section(self):
        datum = 8.233870004582505
        section = TriangleFaceSection([[[0., datum], [1., datum]]], [0., 1.])
        for depth in (1e-100, 1e-30, 1e-12, .1):
            np.testing.assert_allclose(section.moments(depth, datum), [depth, depth*depth, 1.], rtol=2e-15, atol=0)
            flux, _ = section.flux(depth, [0, 0], depth, [0, 0], 0, left_datum=datum, right_datum=datum)
            np.testing.assert_allclose(flux, [0., .5*9.81*depth*depth, 0.], rtol=2e-15, atol=0)

    def test_shared_geometry_and_generator_use_the_same_relative_state(self):
        for relative in (False, True):
            patch = SubcellGeometryPatch(sampler(lambda x, y: 8+abs(x)), [-.5, 0], (1, 2),
                                        periodic=(False, True), relative_stages=relative)
            for depth in ((1e-3,) if not relative else (1e-3, 1e-30, 1e-100)):
                volume = np.full((1, 2), depth*depth/2)
                momentum = volume[..., None]*np.array([[[0., 1.], [0., -1.]]])
                dv, dp, _ = patch.rates(volume, momentum)
                matrix, wall, pressure, _ = frozen_system(patch, volume, momentum)
                np.testing.assert_array_equal(dv, 0.)
                np.testing.assert_allclose((matrix@volume.ravel()).reshape(volume.shape), dv, atol=1e-20)
                actual = matrix@momentum.reshape(-1, 2)-wall*momentum.reshape(-1, 2)+pressure
                np.testing.assert_allclose(actual, dp.reshape(-1, 2), rtol=1e-12, atol=1e-200)
                if relative:
                    expected = -2*np.sqrt(9.81*depth)/depth*momentum[..., 1]
                    np.testing.assert_allclose(dp[..., 1], expected, rtol=2e-14, atol=0)


if __name__ == '__main__':
    unittest.main()
