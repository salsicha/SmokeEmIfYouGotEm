import unittest
from build_rapid_decision_campaign import build, definitions


class DecisionCampaign(unittest.TestCase):
    def test_no_catalog_entry_disappears(self):
        contracts,plans=build()
        self.assertEqual(len(contracts),99)
        self.assertEqual(sum(c['status']=='missing_playable_section' for c in contracts),26)
        self.assertEqual(sum(len(p['trials']) for p in plans),433)
        self.assertTrue(all(c['catalog_class_match']=='not_established' for c in contracts))
        self.assertEqual(len(definitions()),73)

    def test_new_badger_section_remains_one_colorado_catalog_entry(self):
        contracts,plans=build()
        rows=[c for c in contracts if c['name']=='Badger Creek']
        self.assertEqual(len(rows),1)
        self.assertEqual(rows[0]['river'],'colorado')
        self.assertEqual(rows[0]['assessment_river'],'catalog_badger_creek')
        self.assertEqual(rows[0]['status'],'requires_native_comparison')
        p=next(p for p in plans if p['river']=='catalog_badger_creek')
        self.assertTrue(all(t['rapid_id']=='badger_creek' for t in p['trials']))

    def test_matched_approach_and_route(self):
        for p in build()[1]:
            for rapid in {t['rapid_id'] for t in p['trials']}:
                group=[t for t in p['trials'] if t['rapid_id']==rapid]
                a=group[0]
                self.assertTrue(all(t['route_laterals']==a['route_laterals'] for t in group))
                self.assertTrue(all(t['start_m']==a['start_m'] and t['lane_m']==0 for t in group))
                self.assertTrue(all(t['strict_route'] for t in group))
                self.assertTrue(all('rescue_drill_station_m' not in t for t in group))
                self.assertTrue(all(t['start_m']<=t['mistake_trigger_m']<t['finish_m'] for t in group))

    def test_pinball_timing_is_after_first_obstacle(self):
        p=next(p for p in build()[1] if p['river']=='pacuare')
        trials=[t for t in p['trials'] if t['rapid_id']=='lower_pinball']
        self.assertTrue(all(t['mistake_trigger_m']==2010 for t in trials))
        self.assertEqual(trials[0]['route_laterals'][2],[2026,12])

    def test_bidwell_includes_clean_control_and_whole_exit(self):
        p=next(p for p in build()[1] if p['river']=='chilko')
        for t in [t for t in p['trials'] if t['rapid_id']=='bidwell']:
            self.assertEqual(t['finish_m'],1080)
            self.assertEqual(t['lookahead_m'],45)
            self.assertEqual(t['route_laterals'][-2:],[[980,1],[1080,1]])
            self.assertGreater(t['gates'][-1]['station_m'],1015)

    def test_width_and_timing_are_independent(self):
        for p in build('width')[1]:
            for t in p['trials']:
                self.assertNotIn('mistake_seconds',t)
                self.assertNotIn('disable_steering',t)
        for p in build('timing')[1]:
            for t in p['trials']: self.assertEqual(t['lane_m'],0)

    def test_portage_and_evidence_gaps(self):
        contracts,plans=build()
        zam=next(p for p in plans if p['river']=='zambezi')
        self.assertEqual([t['variant'] for t in zam['trials'] if t['rapid_id']=='rapid_9'],['portage'])
        self.assertTrue(any(c.get('family')=='unresolved' for c in contracts))

    def test_missing_entries_have_sources_not_fake_routes(self):
        missing=[c for c in build()[0] if c['status']=='missing_playable_section']
        self.assertEqual(len(missing),26)
        for c in missing:
            self.assertTrue(c['source'].startswith('https://'))
            self.assertTrue(c['construction_review'])
            self.assertIsNone(c['route_coordinates'])
        bobo=next(c for c in missing if c['name']=='Bobo Falls')
        self.assertEqual(bobo['family'],'unresolved')
        self.assertIn('Upper Pacuare',bobo['construction_review'])

    def test_poor_approach_has_a_matched_ordinary_recovery(self):
        for p in build()[1]:
            for rapid in {t['rapid_id'] for t in p['trials'] if not t.get('portage')}:
                a=next(t for t in p['trials'] if t['id']==rapid+'--poor-heading')
                b=next(t for t in p['trials'] if t['id']==rapid+'--poor-heading-recovery')
                self.assertEqual(a['initial_heading_deg'],60.)
                self.assertEqual(a['initial_heading_deg'],b['initial_heading_deg'])
                self.assertEqual(a['heading_offset_deg'],60.)
                self.assertLessEqual(a['heading_start_m'],a['mistake_trigger_m'])
                self.assertGreater(a['heading_end_m'],a['mistake_trigger_m'])
                self.assertLess(a['heading_end_m'],a['finish_m'])
                for key in ('heading_start_m','heading_end_m','heading_offset_deg'):
                    self.assertEqual(a[key],b[key])
                self.assertEqual(a['route_laterals'],b['route_laterals'])
                self.assertFalse(a['normal_rescue_inputs'])
                self.assertTrue(b['normal_rescue_inputs'])


if __name__=='__main__': unittest.main()
