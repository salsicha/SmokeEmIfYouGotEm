import sys
from pathlib import Path
import unittest
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from liquid_compatible_projection import gradient, divergence, project, constrain_velocity
from analyze_liquid_compatible_projection import audit


class CompatibleProjectionTest(unittest.TestCase):
    def test_audit_all_fluid_without_fixed_or_air_cells(self):
        shape = (4, 5, 6)
        fields = {'Velocity': np.zeros((*shape, 3)),
                  'Pressure': np.zeros((*shape, 1)),
                  'SimFloat': np.zeros((*shape, 1)),
                  'SolidVelocity_Boundary': np.zeros((*shape, 4))}
        result = audit(fields)
        self.assertEqual(result['fixed_velocity_error_max_cm_s'], 0.)
        self.assertEqual(result['nonfluid_nonstage_pressure_max'], 0.)
        self.assertEqual(result['final_divergence_rms_per_s'], 0.)

    def test_gradient_divergence_are_negative_adjoints(self):
        rng = np.random.default_rng(431)
        p = rng.normal(size=(7, 8, 9))
        v = rng.normal(size=(*p.shape, 3))
        h = (1., 1.2, .7)
        self.assertAlmostEqual(float(np.sum(p*divergence(v, h))), -float(np.sum(gradient(p, h)*v)), places=10)

    def test_projection_removes_divergence_with_fixed_terrain(self):
        rng = np.random.default_rng(812)
        b = np.zeros((12, 14, 16, 4))
        b[..., 3] = 2
        b[2:10, 2:12, 2:14, 3] = 0
        b[:2, ..., 3] = 1
        v = rng.normal(size=(*b.shape[:-1], 3))
        _, _, result = project(v, b, spacing=(1., 1.2, .7), tolerance=1e-9)
        self.assertTrue(result['converged'])
        self.assertLess(result['divergence_after_rms_per_s'], 1e-8)
        self.assertEqual(result['maximum_fixed_velocity_change_cm_s'], 0.)

    def test_invalid_dimensions_rejected(self):
        with self.assertRaises(ValueError):
            project(np.zeros((4, 4, 4, 3)), np.zeros((4, 4, 4, 4)), spacing=(0, 1, 1))

    def test_nonzero_external_pressure_is_preserved_and_projection_converges(self):
        b = np.zeros((12, 14, 16, 4))
        b[..., 3] = 3
        b[2:-2, 2:-2, 2:-2, 3] = 0
        rng = np.random.default_rng(832)
        v = rng.normal(size=(*b.shape[:-1], 3))
        pressure = np.broadcast_to(np.arange(16, dtype=float), b.shape[:-1]).copy()
        pressure[b[..., 3] != 3] = 0
        updated, p, report = project(v, b, spacing=(1., 1.2, .7), boundary_pressure=pressure, tolerance=1e-9)
        self.assertTrue(report['converged'])
        self.assertLess(report['divergence_after_rms_per_s'], 1e-8)
        np.testing.assert_array_equal(p[b[..., 3] == 3], pressure[b[..., 3] == 3])

    def test_stage_cells_require_explicit_pressure(self):
        b = np.zeros((4, 4, 4, 4))
        b[..., 3] = 3
        with self.assertRaisesRegex(ValueError, 'prescribed pressure'):
            project(np.zeros((4, 4, 4, 3)), b)

    def test_wide_stencil_dispatch_covers_grid_without_same_color_dependency(self):
        for y in range(68):
            for z in range(24):
                lanes = []
                for iteration in range(2):
                    x = np.arange(34)
                    x = (x//2)*4+x % 2+2*((y//2+z//2+iteration % 2) % 2)
                    self.assertEqual(len(set(x)), 34)
                    color = (x//2+y//2+z//2) % 2
                    self.assertTrue((color == iteration).all())
                    self.assertTrue((((x+2)//2+y//2+z//2) % 2 != color).all())
                    lanes.extend(x)
                self.assertEqual(sorted(lanes), list(range(68)))

    def test_audit_matches_projected_fields(self):
        rng = np.random.default_rng(813)
        b = np.zeros((12, 14, 16, 4))
        b[..., 3] = 2
        b[2:10, 2:12, 2:14, 3] = 0
        b[:2, ..., 3] = 1
        v = rng.normal(size=(*b.shape[:-1], 3))
        spacing = (1., 1.2, .7)
        fixed, _, _ = constrain_velocity(v, b)
        updated, p, _ = project(v, b, spacing=spacing, tolerance=1e-9)
        result = audit(dict(Velocity=updated, Pressure=p[..., None],
                            SimFloat=divergence(fixed, spacing)[..., None],
                            SolidVelocity_Boundary=b), spacing=spacing)
        self.assertLess(result['predicted_vs_actual_divergence_rms_per_s'], 1e-12)
        self.assertLess(result['final_divergence_rms_per_s'], 1e-8)
        self.assertEqual(result['fixed_velocity_error_max_cm_s'], 0.)


if __name__ == '__main__':
    unittest.main()
