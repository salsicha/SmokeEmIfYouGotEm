import unittest
import numpy as np
from subcell_geometry_patch import SubcellGeometryPatch
from subcell_implicit_transport import frozen_system, advance
from test_triangle_face_section import sampler


class SubcellImplicitTransportTest(unittest.TestCase):
    def test_generator_reproduces_existing_full_semidiscrete_rate(self):
        rng = np.random.default_rng(913)
        for height, periodic in ((lambda x, y: x*0, (True, True)),
                                 (lambda x, y: .3+np.sin(x)*np.cos(y), (False, False))):
            patch = SubcellGeometryPatch(sampler(height), [-1.5, -1.5], (4, 4), periodic=periodic)
            v, p = patch.state_from_stages(.7+rng.random((4, 4)), rng.normal(size=(4, 4, 2))*.2)
            before = v.copy(), p.copy()
            dv, dp, _ = patch.rates(v, p)
            matrix, wall, pressure, _ = frozen_system(patch, v, p)
            np.testing.assert_allclose(matrix@v.ravel(), dv.ravel(), atol=5e-14, rtol=2e-13)
            expected = matrix@p.reshape(-1, 2)-wall*p.reshape(-1, 2)+pressure
            np.testing.assert_allclose(expected, dp.reshape(-1, 2), atol=5e-14, rtol=2e-13)
            np.testing.assert_allclose(matrix.sum(axis=0), 0, atol=1e-14)
            off_diagonal = matrix-np.diag(np.diag(matrix))
            self.assertGreaterEqual(off_diagonal.min(), 0)
            np.testing.assert_array_equal(v, before[0])
            np.testing.assert_array_equal(p, before[1])

    def test_counterflow_without_small_cell_timestep_or_velocity_cap(self):
        for depth in (1e-2, 1e-4, 1e-6):
            patch = SubcellGeometryPatch(sampler(lambda x, y: abs(x)), [-.5, 0], (1, 2), periodic=(False, True))
            v, p = patch.state_from_stages(depth, [[[0, 1.], [0, -1.]]])
            _, _, old_limit = patch.rates(v, p)
            duration = .2
            self.assertGreater(duration, old_limit)
            vv, pp = advance(patch, v, p, duration)
            # A floating linear solve is not a bitwise stationary assignment.
            # Relative roundoff is checked even for 5e-13 m3, no absolute floor.
            np.testing.assert_allclose(vv, v, rtol=1e-12, atol=0)
            # Analytic backward-Euler two-cell tangential exchange.
            expected = 1/(1+duration*2*np.sqrt(9.81*depth)/depth)
            np.testing.assert_allclose(pp[..., 1]/vv, [[expected, -expected]], rtol=1e-11, atol=1e-15)
            self.assertLessEqual(np.max(abs(pp/vv[..., None])), 1)

    def test_small_dt_consistency_and_closed_mass(self):
        patch = SubcellGeometryPatch(sampler(lambda x, y: .2+x*x*.1), [-1.5, -1.5], (4, 4))
        rng = np.random.default_rng(923)
        v, p = patch.state_from_stages(.7+rng.random((4, 4)), rng.normal(size=(4, 4, 2))*.2)
        dv, dp, _ = patch.rates(v, p)
        errors = []
        for dt in (1e-3, 5e-4, 2.5e-4):
            vv, pp = advance(patch, v, p, dt)
            self.assertAlmostEqual(vv.sum(), v.sum(), places=12)
            errors.append(max(np.max(abs((vv-v)/dt-dv)), np.max(abs((pp-p)/dt-dp))))
        self.assertGreater(errors[0]/errors[1], 1.9)
        self.assertGreater(errors[1]/errors[2], 1.9)


if __name__ == '__main__':
    unittest.main()
