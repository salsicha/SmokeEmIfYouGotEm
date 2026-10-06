"""Stdlib-only checks for coverage and conservative report semantics."""
import unittest
from report_rapid_assessment import inventory, assess, passing_track_spread


class AssessmentTests(unittest.TestCase):
    def test_all_master_entries_are_reported(self):
        rows = inventory()
        self.assertEqual(sum(r['master_catalog'] for r in rows), 85)
        self.assertEqual(len(rows), 99)
        self.assertEqual(len({(r['river'], r['name']) for r in rows}), len(rows))

    def test_missing_reach_is_not_a_fake_class(self):
        row = next(r for r in inventory() if r['name'] == 'Lava Falls')
        result = assess(row, {})
        self.assertEqual(result['rating'], 'Not rateable')
        self.assertIn('Not modeled', result['status'])

    def test_portage_not_automation_failure(self):
        row = next(r for r in inventory() if r['name'] == 'Commercial Suicide')
        self.assertEqual(assess(row, {})['status'], 'Intentional mandatory portage')

    def test_hance_main_is_not_a_missing_catalog_rapid(self):
        row = next(r for r in inventory() if r['name'] == 'Hance')
        self.assertIsNotNone(row['trial'])
        self.assertNotIn('Not modeled', assess(row, {})['status'])

    def test_partial_trial_not_grade_six(self):
        row = next(r for r in inventory() if r['name'] == 'Upper Pinball')
        data = {('pacuare', 'upper_pinball', 'center'): {'outcome': 'time_limit_partial', 'finite': True, 'evidence': 'fixture'}}
        self.assertIn('not Class VI', assess(row, data)['rating'])

    def test_surface_anomaly_blocks_rating(self):
        row = next(r for r in inventory() if r['name'] == 'White Kilometre')
        data = {('chilko', 'white_kilometre', v): dict(outcome='section_cleared', finite=True,
                minimum_center_clearance_m=-6, mistake_start_s=5, evidence='fixture')
                for v in ('center', 'left', 'right', 'missed-turn')}
        self.assertIn('do not grade', assess(row, data)['rating'])

    def test_miss_not_reached_is_not_recovery_evidence(self):
        row = next(r for r in inventory() if r['name'] == 'Upper Pinball')
        data = {('pacuare', 'upper_pinball', v): dict(outcome='section_cleared', finite=True,
                mistake_start_s=-1, evidence='fixture') for v in ('center', 'left', 'right', 'missed-turn')}
        self.assertEqual(assess(row, data)['rating'], 'Not yet established')

    def test_converged_tracks_not_wide_safe_corridor(self):
        trial = dict(control_m=0, finish_m=100)
        lanes = [dict(samples=[dict(station_m=0, lateral_m=x), dict(station_m=100, lateral_m=x)]) for x in (-.2, 0, .2)]
        self.assertAlmostEqual(passing_track_spread(trial, lanes), .4)

    def test_guatemala_finish_is_inside_actual_reach(self):
        row = next(r for r in inventory() if r['name'] == 'Guatemala')
        self.assertEqual(row['trial']['finish_m'], 2328)

    def test_old_wrong_high_side_cannot_support_grade(self):
        row = next(r for r in inventory() if r['name'] == 'Upper Pinball')
        data = {('pacuare', 'upper_pinball', v): dict(outcome='section_cleared', finite=True,
                high_side_responses=1, mistake_start_s=5, evidence='fixture')
                for v in ('center', 'left', 'right', 'missed-turn')}
        self.assertIn('do not grade', assess(row, data)['rating'])
        for value in data.values():
            value['assessment_protocol_version'] = 7
        self.assertNotIn('Superseded', assess(row, data)['rating'])


if __name__ == '__main__':
    unittest.main()
