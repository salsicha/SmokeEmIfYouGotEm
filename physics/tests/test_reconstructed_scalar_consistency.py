import unittest
from audit_reconstructed_scalar_consistency import periodic_case


class ConsistencyDiagnosticTests(unittest.TestCase):
    def test_flat_uniform_control_annihilates_constant(self):
        case = periodic_case(16, 0.)
        self.assertTrue(case['exact_constant_scalar_preservation'])
        self.assertEqual(case['uniform_velocity_advective_linf'], 0.)

    def test_smooth_bed_reports_refining_defect_without_false_acceptance(self):
        cases = [periodic_case(n, .2) for n in (16, 32, 64)]
        for case in cases:
            self.assertGreater(case['constant_scalar_gradient_linf'], 0.)
            self.assertFalse(case['exact_constant_scalar_preservation'])
            self.assertFalse(case['physical_or_scene_accepted'])
        self.assertLess(cases[2]['constant_scalar_gradient_linf'], cases[0]['constant_scalar_gradient_linf']/50)


if __name__ == '__main__': unittest.main()
