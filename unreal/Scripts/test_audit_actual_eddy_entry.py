"""Parser-only adversarial fixtures; never native boat or FPS evidence."""
import copy
import unittest

from audit_actual_eddy_entry import validate_native_inputs


class NativeEddyInputTests(unittest.TestCase):
    def setUp(self):
        self.entry = dict(
            physical_source='/Game/RaftSim/Maps/L_SouthFork_Troublemaker.L_SouthFork_Troublemaker:PersistentLevel.Rock.Component',
            world_seconds=8.0, owner_hydraulic_x_m=1.0, owner_hydraulic_y_m=2.0,
            owner_direction_x=1.0, owner_direction_y=0.0, inferred_radius_m=8.0,
            entry_local_x_radius=4.0, entry_local_y_radius=.1)
        self.motion = dict(map='L_SouthFork_Troublemaker', feature_kinematics_enabled=True,
                           maximum_shared_surface_error_mps=0.0, dry_became_wet=0,
                           actual_boat_motion=[dict(world_seconds=t) for t in (.5, 1., 1.5)])

    def test_valid_native_fields_unchanged(self):
        before = copy.deepcopy((self.entry, self.motion))
        validate_native_inputs(self.entry, self.motion)
        self.assertEqual(before, (self.entry, self.motion))

    def test_missing_nonfinite_negative_and_fractional_physics_refuse(self):
        for field in ('maximum_shared_surface_error_mps', 'dry_became_wet'):
            for bad in (None, True, float('nan'), float('inf'), -1):
                with self.subTest(field=field, bad=bad):
                    motion = copy.deepcopy(self.motion)
                    motion[field] = bad
                    with self.assertRaises(ValueError):
                        validate_native_inputs(self.entry, motion)
        self.motion['dry_became_wet'] = .1
        with self.assertRaises(ValueError):
            validate_native_inputs(self.entry, self.motion)

    def test_wrong_map_and_disabled_currents_refuse(self):
        self.motion['map'] = 'L_Hance'
        with self.assertRaises(ValueError):
            validate_native_inputs(self.entry, self.motion)
        self.motion['map'] = 'L_SouthFork_Troublemaker'
        self.motion['feature_kinematics_enabled'] = False
        with self.assertRaises(ValueError):
            validate_native_inputs(self.entry, self.motion)

    def test_nonfinite_initial_conditions_refuse(self):
        for field in ('world_seconds', 'owner_direction_x', 'inferred_radius_m', 'entry_local_x_radius'):
            with self.subTest(field=field):
                entry = copy.deepcopy(self.entry)
                entry[field] = float('nan')
                with self.assertRaises(ValueError):
                    validate_native_inputs(entry, self.motion)

    def test_invalid_setup_states_not_silently_filtered(self):
        for bad in (None, float('nan'), float('inf'), .5, -.1):
            with self.subTest(bad=bad):
                motion = copy.deepcopy(self.motion)
                motion['actual_boat_motion'][1]['world_seconds'] = bad
                with self.assertRaises(ValueError):
                    validate_native_inputs(self.entry, motion)


if __name__ == '__main__':
    unittest.main()
