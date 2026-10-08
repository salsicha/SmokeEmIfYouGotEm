import unittest
import numpy as np
from export_chilko_completed_corridor import validate_depth_arrays


class CompletedDepthTests(unittest.TestCase):
    def fixture(self):
        return dict(station_m=np.arange(55725.), depth_amplitude_m=np.full(55725, 2.),
                    previous_depth_amplitude_m=np.ones(55725), capacity_chart_station_m=np.arange(8.),
                    inferred_capacity_m3s=np.full(8, 45.), available_width_m=np.full(8, 12.))

    def test_entire_fit_is_required(self):
        a = self.fixture()
        self.assertEqual(validate_depth_arrays(a, 8)['changed_profile_samples'], 55725)
        with self.assertRaises(ValueError): validate_depth_arrays(a)
        for key, value in (('inferred_capacity_m3s', 44.99), ('depth_amplitude_m', 10.01),
                           ('available_width_m', 0.), ('station_m', np.nan)):
            bad = self.fixture(); bad[key][3] = value
            with self.assertRaises(ValueError): validate_depth_arrays(bad, 8)

    def test_no_dry_section_or_nonmonotonic_station_can_be_hidden(self):
        for key in ('station_m', 'capacity_chart_station_m'):
            bad = self.fixture(); bad[key][4] = bad[key][3]
            with self.assertRaises(ValueError): validate_depth_arrays(bad, 8)


if __name__ == '__main__': unittest.main()
