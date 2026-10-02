"""Parser fixtures only; no synthetic states are physical evidence."""
import math
import unittest
from audit_rock_pin_sequence import mechanism


class PinSequence(unittest.TestCase):
    def fixture(self):
        row = dict(seconds=.1, contact_impulses=1, up_z=1.,
                   downstream_minus_upstream_tube_height_m=.2, scoop_wet_upper_faces=0,
                   scoop_upper_face_surface_offset_m=0., scoop_incoming_normal_mps=0.,
                   candidate_pressure_force_n=0., scoop_longitudinal_torque_nm=0.,
                   omega_x_rad_s=0., omega_y_rad_s=-1., omega_z_rad_s=0.,
                   quat_x=0., quat_y=0., quat_z=math.sqrt(.5), quat_w=math.sqrt(.5))
        wet = dict(row, seconds=.2, scoop_wet_upper_faces=2,
                   scoop_upper_face_surface_offset_m=-.1, scoop_incoming_normal_mps=4.,
                   candidate_pressure_force_n=50., scoop_longitudinal_torque_nm=-50.)
        return dict(first_capsize_seconds=.5, motion=[row, wet])

    def test_ordered_reinforcing_sequence(self):
        self.assertEqual(mechanism(self.fixture())['first_reinforcing_scoop_seconds'], .2)

    def test_contact_flip_alone_is_not_scoop(self):
        for key, value in [('scoop_wet_upper_faces', 0), ('scoop_upper_face_surface_offset_m', 0.),
                           ('scoop_incoming_normal_mps', 0.), ('candidate_pressure_force_n', 0.),
                           ('scoop_longitudinal_torque_nm', 50.), ('seconds', .6)]:
            with self.subTest(key=key):
                fixture = self.fixture(); fixture['motion'][1][key] = value
                with self.assertRaises(ValueError): mechanism(fixture)

    def test_lift_and_valid_numeric_evidence_required(self):
        fixture = self.fixture(); fixture['motion'][0]['contact_impulses'] = 0
        with self.assertRaises(ValueError): mechanism(fixture)
        fixture = self.fixture(); fixture['motion'][1]['scoop_incoming_normal_mps'] = float('nan')
        with self.assertRaises(ValueError): mechanism(fixture)


if __name__ == '__main__':
    unittest.main()
