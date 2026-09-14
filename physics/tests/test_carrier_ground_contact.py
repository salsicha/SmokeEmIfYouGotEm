import unittest
import json
import numpy as np
from audit_carrier_ground_contact import compare


class GroundContactAuditTest(unittest.TestCase):
    def probe(self, water, wet, **changes):
        p = dict(x_cm=0., y_cm=0., water_z_cm=water, ground_hit=True,
                 ground_z_cm=1., support_available=True, support_wet=wet,
                 raw_available=True, raw_wet=True)
        p.update(changes)
        return p

    def test_buried_and_arbitrarily_thin_clear_water(self):
        report = compare([self.probe(.5, False), self.probe(1.+1e-8, True)], [1., 1.])
        self.assertTrue(report['scoped_contact_pass'])
        self.assertEqual(report['buried_points'], 1)
        json.dumps(compare([self.probe(.5, False)], np.array([1.])))

    def test_buried_wet_is_failure_not_excluded(self):
        self.assertFalse(compare([self.probe(.5, True)], [1.])['scoped_contact_pass'])

    def test_false_dry_is_failure(self):
        self.assertFalse(compare([self.probe(2., False)], [1.])['scoped_contact_pass'])

    def test_missing_and_displaced_ground_fail(self):
        for changes in (dict(ground_hit=False), dict(ground_z_cm=2.),
                        dict(support_available=False)):
            self.assertFalse(compare([self.probe(3., True, **changes)], [1.])['scoped_contact_pass'])

    def test_raw_dry_cannot_become_support(self):
        self.assertFalse(compare([self.probe(3., True, raw_wet=False)], [1.])['scoped_contact_pass'])

    def test_no_ground_survivor_only_pass(self):
        with self.assertRaises(ValueError):
            compare([], [])


if __name__ == '__main__':
    unittest.main()
