import copy
import unittest

from audit_paired_water_contact import audit


def fixture():
    probe = dict(x_cm=-12., y_cm=3., water_z_cm=20., ground_hit=True,
                 ground_z_cm=10., support_available=True, support_wet=True,
                 raw_available=True, raw_wet=True)
    contact = dict(detail_frame_sequence=11, tested_wet_points=1, raw_dry_points=0,
                   unavailable_points=0, detail_affected_contact_points=1,
                   maximum_support_carrier_error_cm=0.00005,
                   rms_support_carrier_error_cm=0.00002,
                   maximum_contact_detail_height_cm=2., world_seconds=10.,
                   ground_contact_probes=[probe], ground_occluded_points=0,
                   ground_occluded_wet_points=0, includes_paired_detail=True,
                   detail_gpu_audit_requested=True)
    gpu = dict(detail_frame_sequence=11, queries=4226, maximum_rgba_error=1e-8,
               maximum_sampled_detail_height_cm=3., sample_elapsed_seconds=10.,
               simulation_seconds=9.8, passed=True)
    return contact, gpu


class PairedWaterContactTest(unittest.TestCase):
    def test_valid_paired_snapshot(self):
        self.assertTrue(audit(*fixture())['passed'])

    def test_every_missing_required_field_is_refused(self):
        for report_index, report in enumerate(fixture()):
            for key in report:
                with self.subTest(report=report_index, key=key):
                    pair = fixture()
                    del pair[report_index][key]
                    with self.assertRaises((KeyError, ValueError)):
                        audit(*pair)

    def test_nonfinite_and_non_numeric_values_are_refused(self):
        for value in (float('nan'), float('inf'), -1, True, '0'):
            for index, key in ((0, 'maximum_support_carrier_error_cm'),
                               (1, 'maximum_rgba_error'), (0, 'tested_wet_points')):
                with self.subTest(value=value, key=key):
                    pair = fixture()
                    pair[index][key] = value
                    with self.assertRaises(ValueError):
                        audit(*pair)

    def test_mismatched_sequence_and_disabled_detail_fail(self):
        for index, key, value in ((1, 'detail_frame_sequence', 12),
                                  (0, 'includes_paired_detail', False),
                                  (0, 'detail_gpu_audit_requested', False),
                                  (0, 'detail_affected_contact_points', 0),
                                  (1, 'passed', False)):
            pair = fixture()
            pair[index][key] = value
            self.assertFalse(audit(*pair)['passed'])

    def test_summary_cannot_hide_invalid_probe_population(self):
        contact, gpu = fixture()
        contact['ground_contact_probes'].append(copy.deepcopy(contact['ground_contact_probes'][0]))
        with self.assertRaises(ValueError):
            audit(contact, gpu)
        contact, gpu = fixture()
        contact['ground_contact_probes'][0]['support_wet'] = False
        with self.assertRaises(ValueError):
            audit(contact, gpu)

    def test_ground_occlusion_is_independent_of_gpu_parity(self):
        contact, gpu = fixture()
        contact['ground_contact_probes'][0]['ground_z_cm'] = 21.
        contact['ground_occluded_points'] = contact['ground_occluded_wet_points'] = 1
        result = audit(contact, gpu)
        self.assertEqual(result['failures'], ['no_wet_support_below_registered_ground'])

    def test_ground_occluded_dry_support_is_not_a_wet_failure(self):
        contact, gpu = fixture()
        dry = copy.deepcopy(contact['ground_contact_probes'][0])
        dry.update(ground_z_cm=21., support_wet=False, raw_wet=False)
        contact['ground_contact_probes'].append(dry)
        contact.update(raw_dry_points=1, ground_occluded_points=1)
        self.assertTrue(audit(contact, gpu)['passed'])

    def test_error_gates_cannot_be_overridden_by_passed_flag(self):
        contact, gpu = fixture()
        gpu['maximum_rgba_error'] = 1e-6
        self.assertFalse(audit(contact, gpu)['passed'])
        contact, gpu = fixture()
        contact['maximum_support_carrier_error_cm'] = 0.002
        self.assertFalse(audit(contact, gpu)['passed'])


if __name__ == '__main__':
    unittest.main()
