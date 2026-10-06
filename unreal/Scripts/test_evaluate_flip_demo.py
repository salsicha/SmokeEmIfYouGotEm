"""Classifier unit fixtures only; these are not simulated boat receipts."""
import unittest
from evaluate_flip_demo import water_generated


class WaterGeneratedClassification(unittest.TestCase):
    def fixture(self):
        return dict(first_capsize_seconds=4., initial_roll_degrees=0.,
                    initial_roll_rate_rad_s=0., initial_up_z=1., initial_omega_rad_s=0.,
                    timed_pose_transition_used=False, pressure_before_capsize=True,
                    moving_water_torque_before_capsize=False, contact_impulses=0,
                    sampled_pressure_angular_impulse_magnitude_nms=25.,
                    capsize_mode_before_actual_inversion=False, final_swimmer_count=5,
                    last_up_z=-1.)

    def test_upright_native_provenance_can_qualify(self):
        self.assertTrue(water_generated(self.fixture()))

    def test_seeded_entries_do_not_qualify(self):
        for key, value in [('initial_roll_degrees', 75.), ('initial_roll_rate_rad_s', 5.),
                           ('initial_up_z', .25), ('initial_omega_rad_s', 5.)]:
            with self.subTest(key=key):
                result = self.fixture(); result[key] = value
                self.assertFalse(water_generated(result))

    def test_missing_or_invalid_force_provenance_does_not_qualify(self):
        for key, value in [('initial_up_z', None), ('initial_omega_rad_s', None),
                           ('timed_pose_transition_used', True), ('pressure_before_capsize', False),
                           ('sampled_pressure_angular_impulse_magnitude_nms', None),
                           ('sampled_pressure_angular_impulse_magnitude_nms', float('inf')),
                           ('sampled_pressure_angular_impulse_magnitude_nms', -1.)]:
            with self.subTest(key=key):
                result = self.fixture(); result[key] = value
                self.assertFalse(water_generated(result))

    def test_buoyancy_generated_flip_does_not_require_overtopping(self):
        result = self.fixture()
        result.update(pressure_before_capsize=False, moving_water_torque_before_capsize=True,
                      sampled_pressure_angular_impulse_magnitude_nms=0.)
        self.assertTrue(water_generated(result))
        result['contact_impulses'] = 1
        self.assertFalse(water_generated(result))

    def test_nonflip_and_premature_lifecycle_do_not_qualify(self):
        for key, value in [('first_capsize_seconds', -1.), ('last_up_z', 1.),
                           ('final_swimmer_count', 0), ('capsize_mode_before_actual_inversion', True)]:
            with self.subTest(key=key):
                result = self.fixture(); result[key] = value
                self.assertFalse(water_generated(result))


if __name__ == '__main__':
    unittest.main()
