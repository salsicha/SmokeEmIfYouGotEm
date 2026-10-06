import copy
import unittest

from audit_packaged_shared_water_rollout import feature_activation


class FeatureCoverageTest(unittest.TestCase):
    def fixture(self):
        return {'feature_activation_history': [{
            'world_seconds': 12., 'published_hole_owners': 1, 'physical_eddy_owners': 1,
            'actual_wet_hole_depth_probes': [{
                'depth_m': 1.5, 'intensity': 1., 'spilling_fraction': 1.,
                'surface_along_mps': -1., 'submerged_along_mps': 2.,
                'submerged_minus_surface_along_mps': 3.}],
            'actual_wet_eddy_owner_probes': [{
                'physical_source': '/Game/ExistingPhysicalRock',
                'actual_wet_hull_current_probes': [
                    dict(local_x_radius=4., local_y_radius=.1, actual_along_mps=-1., actual_across_mps=0.),
                    dict(local_x_radius=1.75, local_y_radius=.6, actual_along_mps=0., actual_across_mps=1.),
                    dict(local_x_radius=2.25, local_y_radius=1.25, actual_along_mps=2., actual_across_mps=0.)]}]}]}

    def test_missing_history_cannot_claim_activation(self):
        result = feature_activation({'changed_probes': 441, 'active_physical_eddy_owners': 9})
        self.assertFalse(result['available'])
        self.assertFalse(result['hole_activation_observed'])
        self.assertFalse(result['eddy_activation_observed'])

    def test_quiet_window_is_not_activation(self):
        feature = self.fixture()
        row = feature['feature_activation_history'][0]
        row.update(published_hole_owners=0, physical_eddy_owners=0,
                   actual_wet_hole_depth_probes=[], actual_wet_eddy_owner_probes=[])
        result = feature_activation(feature)
        self.assertTrue(result['available'])
        self.assertFalse(result['hole_activation_observed'])
        self.assertFalse(result['eddy_activation_observed'])

    def test_actual_branches_and_depth_leg(self):
        result = feature_activation(self.fixture())
        self.assertTrue(result['hole_activation_observed'])
        self.assertTrue(result['eddy_activation_observed'])
        self.assertEqual(result['hole_surface_return_probes'], 1)

    def test_partial_eddy_topology_is_not_accepted(self):
        feature = self.fixture()
        feature['feature_activation_history'][0]['actual_wet_eddy_owner_probes'][0]['actual_wet_hull_current_probes'].pop()
        self.assertFalse(feature_activation(feature)['eddy_activation_observed'])

    def test_depth_delta_alone_does_not_prove_a_returning_hole(self):
        feature = self.fixture()
        hole = feature['feature_activation_history'][0]['actual_wet_hole_depth_probes'][0]
        hole.update(surface_along_mps=1., submerged_along_mps=4.,
                    submerged_minus_surface_along_mps=3.)
        result = feature_activation(feature)
        self.assertEqual(result['hole_submerged_leg_probes'], 1)
        self.assertFalse(result['hole_activation_observed'])

    def test_inconsistent_depth_receipt_is_rejected(self):
        feature = self.fixture()
        feature['feature_activation_history'][0]['actual_wet_hole_depth_probes'][0]['submerged_minus_surface_along_mps'] = 0.
        with self.assertRaises(ValueError):
            feature_activation(feature)

    def test_nonfinite_history_is_rejected(self):
        feature = self.fixture()
        feature['feature_activation_history'][0]['world_seconds'] = float('nan')
        with self.assertRaises(ValueError):
            feature_activation(feature)

    def test_stale_or_unowned_samples_are_rejected(self):
        for mutation in ('owner', 'clock', 'count'):
            feature = self.fixture()
            row = feature['feature_activation_history'][0]
            if mutation == 'owner':
                row['actual_wet_eddy_owner_probes'][0]['physical_source'] = ''
            elif mutation == 'clock':
                feature['feature_activation_history'].append(copy.deepcopy(row))
            else:
                row['physical_eddy_owners'] = 0
            with self.assertRaises(ValueError):
                feature_activation(feature)


if __name__ == '__main__':
    unittest.main()
