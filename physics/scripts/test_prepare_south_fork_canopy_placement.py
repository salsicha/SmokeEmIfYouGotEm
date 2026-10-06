import unittest
import numpy as np
from prepare_south_fork_canopy_placement import translated_roots


class FullRiverCanopyPlacementTest(unittest.TestCase):
    def test_local_world_north_is_not_reflected_twice(self):
        records = [{'location_cm': [10., -20., 30.]}]
        result = translated_roots(records, [-500., -700., 0.])
        np.testing.assert_array_equal(result, [[-490., -720., 30.]])
        self.assertEqual(records[0]['location_cm'], [10., -20., 30.])

    def test_invalid_coordinates_never_create_fallback_roots(self):
        for position in ([1., 2.], [1., np.nan, 3.]):
            with self.assertRaises(ValueError):
                translated_roots([{'location_cm': position}], [0., 0., 0.])


if __name__ == '__main__':
    unittest.main()
