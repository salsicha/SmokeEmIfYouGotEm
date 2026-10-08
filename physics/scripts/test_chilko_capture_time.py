from datetime import datetime, timezone
import unittest

import numpy as np

from chilko_capture_time import utc_seconds_2023, date_counts


class CaptureTimeTests(unittest.TestCase):
    def test_standard_gps_adjustment_and_2023_utc_offset(self):
        utc = datetime(2023, 10, 7, 19, 30, tzinfo=timezone.utc)
        gps_origin = datetime(1980, 1, 6, tzinfo=timezone.utc)
        adjusted = (utc-gps_origin).total_seconds() + 18 - 1_000_000_000
        np.testing.assert_array_equal(utc_seconds_2023([adjusted, adjusted+.125], 17),
                                      [utc.timestamp(), utc.timestamp()+.125])

    def test_no_guessing_missing_week_invalid_values_or_other_year_offset(self):
        for values, encoding in [([380000000], 16), ([380000000], -1),
                                 ([np.nan], 17), ([], 17), ([[380000000]], 17),
                                 ([0], 17), ([800000000], 17)]:
            with self.assertRaises(ValueError): utc_seconds_2023(values, encoding)

    def test_utc_and_fixed_pst_midnight_are_reported_separately(self):
        seconds = [datetime(2023, 10, 8, hour, tzinfo=timezone.utc).timestamp()
                   for hour in (1, 7, 8, 9)]
        self.assertEqual(date_counts(seconds), {'2023-10-08': 4})
        self.assertEqual(date_counts(seconds, -8), {'2023-10-07': 2, '2023-10-08': 2})
        with self.assertRaises(ValueError): date_counts(seconds, -7)


if __name__ == '__main__': unittest.main()
