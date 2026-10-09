"""Stdlib-only checks for coverage and conservative report semantics."""
import unittest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch
from report_rapid_assessment import inventory, assess, passing_track_spread, catalogue_range, clean


class AssessmentTests(unittest.TestCase):
    def test_all_master_entries_are_reported(self):
        rows = inventory()
        self.assertEqual(sum(r['master_catalog'] for r in rows), 105)
        self.assertEqual(len(rows), 119)
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
        self.assertIsNone(assess(row, data)['game_class'])

    def test_depth_alone_does_not_establish_class_or_invalid_motion(self):
        row = next(r for r in inventory() if r['name'] == 'White Kilometre')
        data = {('chilko', 'white_kilometre', v): dict(outcome='section_cleared', finite=True,
                minimum_center_clearance_m=-6, mistake_start_s=5, evidence='fixture')
                for v in ('center', 'left', 'right', 'missed-turn')}
        self.assertIsNone(assess(row, data)['game_class'])
        self.assertNotIn('test faults', assess(row, data)['status'])

    def test_miss_not_reached_is_not_recovery_evidence(self):
        row = next(r for r in inventory() if r['name'] == 'Upper Pinball')
        data = {('pacuare', 'upper_pinball', v): dict(outcome='section_cleared', finite=True,
                mistake_start_s=-1, evidence='fixture') for v in ('center', 'left', 'right', 'missed-turn')}
        result = assess(row, data)
        self.assertIsNone(result['game_class'])
        self.assertEqual(result['recovery'], 'Not established')

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
        self.assertIn('superseded high-side input', assess(row, data)['status'])
        for value in data.values():
            value['assessment_protocol_version'] = 8
        self.assertNotIn('superseded', assess(row, data)['status'])

    def test_clean_hands_off_is_not_automatic_class_one(self):
        row = next(r for r in inventory() if r['name'] == 'Upper Pinball')
        value = dict(outcome='section_cleared', finite=True, evidence='fixture')
        result = assess(row, {('pacuare', 'upper_pinball', 'hands-off'): value})
        self.assertEqual(result['hands_off'], 'clean')
        self.assertIsNone(result['game_class'])
        self.assertIn('Incomplete evidence', result['status'])

    def test_all_clean_variants_do_not_prove_class_match(self):
        row = next(r for r in inventory() if r['name'] == 'Hance')
        data = {(row.get('assessment_river', row['river']), row['trial']['id'], v):
                dict(outcome='section_cleared', finite=True, mistake_start_s=5, evidence='fixture')
                for v in ('hands-off', 'center', 'left', 'right', 'missed-turn')}
        result = assess(row, data)
        self.assertIsNone(result['game_class'])
        self.assertTrue(all(v is None for v in result['criteria'].values()))
        self.assertIn('not converted', result['comparison'])

    def test_grand_canyon_scale_is_not_halved(self):
        self.assertIsNone(catalogue_range('8/10'))
        self.assertIsNone(catalogue_range('6–8/10'))
        self.assertEqual(catalogue_range('III–IV'), (3, 4))

    def test_checkpoint_restored_exit_is_not_recovery(self):
        row = next(r for r in inventory() if r['name'] == 'Upper Pinball')
        value = dict(outcome='section_cleared', finite=True, checkpoint_restores_during_trial=1,
                     mistake_start_s=5, evidence='fixture')
        self.assertFalse(clean(value))
        result = assess(row, {('pacuare', 'upper_pinball', 'missed-turn'): value})
        self.assertIn('not recovery', result['recovery'])
        legacy = dict(value, checkpoint_restores_during_trial=0, checkpoint_restores=1)
        self.assertFalse(clean(legacy))

    def test_nonfinite_receipt_is_retained_but_excluded(self):
        row = next(r for r in inventory() if r['name'] == 'Upper Pinball')
        value = dict(outcome='section_cleared', finite=False, evidence='fixture')
        result = assess(row, {('pacuare', 'upper_pinball', 'center'): value})
        self.assertIn('nonfinite', result['status'])
        self.assertEqual(result['evidence'], ['fixture'])
        self.assertIn('center not tested', result['route'])

    def test_html_and_json_do_not_reintroduce_unsupported_classes(self):
        from report_rapid_assessment import main
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            with patch('sys.argv', ['report_rapid_assessment', str(root/'inputs'), '--output', str(root/'report')]):
                main()
            rows = json.loads((root/'report/report.json').read_text(encoding='utf-8'))
            self.assertEqual(len(rows), 119)
            self.assertTrue(all(r['game_class'] is None for r in rows))
            document = (root/'report/report.html').read_text(encoding='utf-8')
            self.assertIn('OBSERVATION INVENTORY', document)
            self.assertNotIn('Class I by definition', document)
            self.assertNotIn('roughly half the number', document)
            self.assertNotIn('each on the I–V scale', document)


if __name__ == '__main__':
    unittest.main()
