import copy
import unittest

from audit_breaking_surface_profiles import summarize


def fixture(detail=True):
    site = dict(east_m=10., north_m=-20., direction_east=0., direction_north=1.,
                additional_crest_m=.04, spilling_fraction=.9, presentation_weight=1., samples=[])
    for across in (-2., 0., 2.):
        for step in range(-48, 49):
            along = step*.25
            row = dict(along_m=along, across_m=across, east_m=10-across, north_m=-20+along,
                raw_available=True, raw_wet=True, carrier_wet=True,
                raw_surface_world_m=10+.1*along, raw_bed_world_m=9+.1*along, raw_depth_m=1.,
                raw_velocity_east_mps=0., raw_velocity_north_mps=1., carrier_macro_world_m=10+.2*along)
            row.update(raw_surface_absolute_m=row['raw_surface_world_m']+220.,
                       raw_bed_absolute_m=row['raw_bed_world_m']+220.)
            if detail:
                row.update(presented_detail_m=.01, carrier_with_detail_world_m=row['carrier_macro_world_m']+.01)
            site['samples'].append(row)
    return dict(schema='raftsim.breaking_surface_profiles.v2', world_seconds=10.,
                raw_height_frame='datum_relative_world_z_m', river_vertical_datum_m=220.,
                presented_detail_sequence=3, presented_detail_simulation_seconds=9.8,
                presented_detail_elapsed_seconds=9.9,
                committed_water_seconds=9.9, presented_detail_available=detail, sites=[site])


class Profiles(unittest.TestCase):
    def test_double_datum_subtraction_and_obsolete_capture_rejected(self):
        data = fixture()
        data['sites'][0]['samples'][0]['raw_surface_world_m'] -= 220.
        with self.assertRaisesRegex(ValueError, 'datum conversion'):
            summarize(data)
        data = fixture()
        data['schema'] = 'raftsim.breaking_surface_profiles.v1'
        with self.assertRaisesRegex(ValueError, 'obsolete'):
            summarize(data)

    def test_separate_raw_macro_and_detail(self):
        result = summarize(fixture())
        row = result['sites'][0]['transects'][1]
        self.assertAlmostEqual(row['raw']['range_m'], 2.4)
        self.assertAlmostEqual(row['macro']['range_m'], 4.8)
        self.assertAlmostEqual(row['with_detail']['maximum_adjacent_abs_slope'], .2)
        self.assertAlmostEqual(row['maximum_abs_detail_m'], .01)
        self.assertFalse(result['surface_realism_accepted'])

    def test_missing_detail_is_unavailable_not_zero(self):
        row = summarize(fixture(False))['sites'][0]['transects'][0]
        self.assertIsNone(row['maximum_abs_detail_m'])
        self.assertEqual(row['with_detail']['samples'], 0)
        self.assertIsNone(row['with_detail']['range_m'])

    def test_dry_gap_never_bridged(self):
        data = fixture()
        for row in data['sites'][0]['samples']:
            row['raw_wet'] = row['carrier_wet'] = row['along_m'] in (-12, 12)
        row = summarize(data)['sites'][0]['transects'][1]
        self.assertEqual(row['macro']['samples'], 2)
        self.assertEqual(row['macro']['adjacent_segments'], 0)
        self.assertIsNone(row['macro']['maximum_adjacent_abs_slope'])

    def test_malformed_data_rejected(self):
        original = fixture()
        for mutate in (
            lambda d: d['sites'][0]['samples'].pop(),
            lambda d: d['sites'][0]['samples'].__setitem__(0, copy.deepcopy(d['sites'][0]['samples'][1])),
            lambda d: d['sites'][0]['samples'][0].update(east_m=11),
            lambda d: d['sites'][0]['samples'][0].update(raw_wet=1),
            lambda d: d['sites'][0]['samples'][0].update(raw_depth_m=float('nan')),
            lambda d: d['sites'][0]['samples'][0].update(carrier_with_detail_world_m=0),
            lambda d: d.update(world_seconds=-1),
        ):
            data = copy.deepcopy(original)
            mutate(data)
            with self.assertRaises(ValueError):
                summarize(data)


if __name__ == '__main__':
    unittest.main()
