import unittest
from audit_station_coverage import audit


class StationCoverageAuditTest(unittest.TestCase):
    row = ('StationCoverageAudit frame=1 stations=128 queries=10000 '
           'differences=0 recentered=1 center=20 north=-30')

    def check(self, row):
        return audit(row + '\nLogExit: Exiting.', minimum_refreshes=1)

    def test_exact_runtime_values(self):
        result = self.check(self.row)
        self.assertTrue(result['passed'])
        self.assertEqual(result['queries'], 10000)
        self.assertFalse(result['release_accepted'])

    def test_mismatch_retained_and_fails(self):
        result = self.check(self.row.replace('differences=0', 'differences=1'))
        self.assertFalse(result['passed'])
        self.assertEqual(result['differences'], 1)

    def test_no_recentering_is_not_qualified(self):
        self.assertFalse(self.check(self.row.replace('recentered=1', 'recentered=0'))['passed'])

    def test_invalid_measurement_rejected(self):
        for old, new in [('center=20', 'center=nan'), ('queries=10000', 'queries=0'),
                         ('stations=128', 'stations=0'), ('north=-30', '')]:
            with self.assertRaises(ValueError):
                self.check(self.row.replace(old, new))

    def test_incomplete_capture_rejected(self):
        with self.assertRaises(ValueError):
            audit(self.row, minimum_refreshes=1)
        with self.assertRaises(ValueError):
            audit(self.row + '\nLogExit: Exiting.')


if __name__ == '__main__':
    unittest.main()
