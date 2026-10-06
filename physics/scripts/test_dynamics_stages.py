import unittest
from audit_dynamics_stages import analyze, VECTOR_KEYS


def fixture():
    result = []
    velocity, omega = [0., 0., 0.], [0., 0., 0.]
    for i in range(960):
        row = {k: [0., 0., 0.] for k in VECTOR_KEYS}
        row.update(sequence=i+1, world_s=26+i/120., frame=100+i//4, dt=1/120., mass_kg=2.,
                   angular_damping=.99, ground_points=0, penetration_m=0., invalid_state=False,
                   alternate_contact=False, inertia=[1., 2., 4.], force=[2., 0., 0.], torque=[0., 0., 4.])
        row['before_v'], row['before_w'] = velocity[:], omega[:]
        velocity = [velocity[0]+1/120., 0., 0.]
        omega = [0., 0., (omega[2]+1/120.)*.99]
        row['pre_contact_v'], row['pre_contact_w'] = velocity[:], omega[:]
        row['after_v'], row['after_w'] = velocity[:], omega[:]
        result.append(row)
    return result


class DynamicsStagesTests(unittest.TestCase):
    def test_closes_analytic_budget(self):
        result = analyze(fixture())
        self.assertTrue(result['budget_passed'])
        self.assertAlmostEqual(result['stages']['support']['angular'][2], 8.)
        self.assertEqual(result['ground_contact_substeps'], 0)
        self.assertLess(result['stages']['angular_damping']['angular'][2], 0.)

    def test_missing_duplicate_reordered(self):
        rows = fixture()
        for altered in (rows[:50]+rows[51:], rows[:50]+[rows[49]]+rows[50:], rows[::-1]):
            with self.assertRaises(ValueError): analyze(altered)

    def test_incomplete_window(self):
        with self.assertRaisesRegex(ValueError, 'Incomplete'):
            analyze(fixture()[:800])

    def test_integration_mismatch(self):
        rows = fixture(); rows[5]['pre_contact_w'][2] += .01
        with self.assertRaisesRegex(ValueError, 'does not close'): analyze(rows)

    def test_external_state_change(self):
        rows = fixture(); rows[5]['before_v'][0] += 1.
        with self.assertRaisesRegex(ValueError, 'outside recorded'): analyze(rows)

    def test_invalid_values_or_modes(self):
        for key, value in [('mass_kg', 0), ('dt', float('nan')), ('invalid_state', True),
                           ('alternate_contact', True), ('ground_points', .5), ('penetration_m', -1)]:
            rows = fixture(); rows[0][key] = value
            with self.assertRaises(ValueError): analyze(rows)

    def test_last_step_small_ground_response(self):
        rows = fixture(); row = rows[-1]
        row['after_v'][0] -= .01
        row['after_w'][2] *= .9
        row['ground_points'], row['penetration_m'] = 1, .0001
        result = analyze(rows)
        self.assertEqual(result['ground_contact_substeps'], 1)
        self.assertAlmostEqual(result['stages']['ground_response']['linear'][0], -.01)
        self.assertLess(result['stages']['ground_response']['angular'][2], 0.)

    def test_force_partition_and_external_impulse(self):
        rows = fixture(); row = rows[-1]
        row['retained_force'] = [1., 0., 0.]
        row['obstacle_force_cumulative'] = [1.5, 0., 0.]
        row['linear_impulse'] = [.2, 0., 0.]
        row['pre_contact_v'][0] += .1; row['after_v'][0] += .1
        result = analyze(rows)
        self.assertAlmostEqual(result['stages']['external_impulse']['linear'][0], .1)
        self.assertAlmostEqual(result['stages']['retained']['linear'][0], 1/240.)
        self.assertAlmostEqual(result['stages']['obstacle']['linear'][0], 1/480.)


if __name__ == '__main__':
    unittest.main()
