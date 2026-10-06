import unittest
from build_colorado_catalog_windows import window, registered_label, MILE_M


class ConstructionWindowTests(unittest.TestCase):
    def inputs(self):
        rapid = dict(name='Georgie', river_mile=24.4, **{'class':'6/10'})
        point = dict(attributes=dict(rapid='24-Mile Rapid', rm_label='24.35'), geometry=dict(x=0,y=0))
        rows = [dict(rm=24.35+n*.01, easting=n*.01*MILE_M, northing=0.,
                     ws_final=800.-n*.02, ws_nonincreasing=800.-n*.02,
                     ws_final_source='applanix', min_bed_height=None if n==0 else 798.,
                     max_bed_depth=None if n==0 else 2.) for n in range(-50,51)]
        return rapid, point, rows

    def test_georgie_is_not_24_point_5_mile(self):
        self.assertEqual(registered_label('Georgie'), '24-Mile Rapid')
        rapid, point, rows = self.inputs()
        point['attributes']['rapid']='24.5-Mile Rapid'
        with self.assertRaises(ValueError): window(rapid, point, rows)

    def test_missing_bed_and_distinct_mile_are_preserved(self):
        result = window(*self.inputs())
        self.assertEqual(result['missing_bed_statistic_samples'],1)
        self.assertIsNone(result['full_channel_bathymetry_coverage'])
        self.assertFalse(result['rapid_entry_exit_bounds_verified'])
        self.assertAlmostEqual(result['catalog_to_usgs_mile_delta'],-.05)
        self.assertIsNone(next(r for r in result['samples'] if r['rm']==24.35)['min_bed_height'])

    def test_station_is_local_metric_not_absolute_river_mile(self):
        result = window(*self.inputs())
        self.assertEqual(result['samples'][0]['local_arc_station_m'],0.)
        self.assertAlmostEqual(result['rapid_point_local_station_m'],49*.01*MILE_M)
        self.assertAlmostEqual(result['length_m'],98*.01*MILE_M)

    def test_interpolation_not_claimed_as_survey(self):
        rapid, point, rows = self.inputs()
        rows[50]['ws_final_source']='interpolate - no data'
        result = window(rapid, point, rows)
        self.assertEqual(next(r for r in result['samples'] if r['rm']==24.35)['water_evidence_kind'],'interpolated')

    def test_unknown_source_rejected(self):
        rapid, point, rows = self.inputs()
        rows[50]['ws_final_source']='unknown'
        with self.assertRaises(ValueError): window(rapid, point, rows)

    def test_dsm_is_not_claimed_as_gnss(self):
        rapid, point, rows = self.inputs()
        rows[50]['ws_final_source']='DSM'
        result=window(rapid, point, rows)
        self.assertEqual(next(r for r in result['samples'] if r['rm']==24.35)['water_evidence_kind'],'dsm_derived')

    def test_short_or_unregistered_window_rejected(self):
        rapid, point, rows = self.inputs()
        with self.assertRaises(ValueError): window(rapid, point, rows[40:60])
        point['geometry']['y']=1000
        with self.assertRaises(ValueError): window(rapid, point, rows)


if __name__=='__main__': unittest.main()
