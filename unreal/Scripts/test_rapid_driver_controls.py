import unittest
from build_rapid_driver_controls import plans


class DriverControls(unittest.TestCase):
    def test_only_explicit_input_controls_differ(self):
        allowed={'id','variant','lookahead_m','heading_start_m','heading_end_m','heading_offset_deg','disable_steering'}
        for p in plans():
            base={k:v for k,v in p['trials'][0].items() if k not in allowed}
            self.assertEqual(len(p['trials']),4)
            self.assertEqual(p['trials'][0]['lookahead_m'],12.)
            self.assertEqual(p['trials'][1]['lookahead_m'],45.)
            for t in p['trials']:
                self.assertEqual({k:v for k,v in t.items() if k not in allowed},base)
                self.assertTrue(t['strict_route'])
                self.assertFalse(t['normal_rescue_inputs'])
                self.assertNotIn('rescue_drill_station_m',t)

    def test_covers_both_distinct_failure_types(self):
        self.assertEqual({p['river'] for p in plans()},{'chilko','zambezi'})

    def test_historical_bidwell_control_keeps_its_original_gates(self):
        for t in next(p for p in plans() if p['river']=='chilko')['trials']:
            self.assertEqual([g['station_m'] for g in t['gates']], [741.25,832.5,923.75,996.75])
            self.assertTrue(all(t['start_m']<g['station_m']<t['finish_m'] for g in t['gates']))


if __name__=='__main__': unittest.main()
