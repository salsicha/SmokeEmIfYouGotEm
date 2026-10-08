"""Source-geometry regression tests, not substitutes for native water tests."""
import copy
import json
from pathlib import Path
import tempfile
import unittest

import numpy as np

from audit_rapid_feature_source import ROOT, audit, digest


class SourceAuditTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root/'source'
        (self.source/'scenario').mkdir(parents=True)
        self.x = np.arange(0., 202., 2.)
        self.y = np.arange(-30., 32., 2.)
        self.wet = np.ones((len(self.y), len(self.x)), dtype=np.uint8)
        self.bed = np.full(self.wet.shape, 98.)
        (self.source/'coordinate_map.json').write_text('{}')
        self.candidate = dict(rapid='fixture', source_directory='source',
                              features=[[100, 0, 0, .8, 4, .5]],
                              quiet_station_intervals_m=[[0, 50], [150, 200]])
        self.rebind()

    def rebind(self):
        np.savez(self.source/'reference.npz', station=self.x, lateral=self.y,
                 reference_surface=np.full(self.x.shape, 100.), classified_water=self.wet)
        np.save(self.source/'scenario/bed.npy', self.bed)
        self.candidate['source_sha256'] = {name: digest(self.source/name) for name in
                                         ('coordinate_map.json', 'reference.npz', 'scenario/bed.npy')}

    def test_exact_shared_kernel_bounds_and_no_acceptance(self):
        result = audit(self.candidate, self.root)
        self.assertEqual(result['sites'][0]['footprint_station_bounds_m'], [88., 128.])
        self.assertEqual(result['sites'][0]['constructed_reference_depth_m'], 2.)
        self.assertFalse(result['engine_accepted'])
        self.assertFalse(result['catalog_class_match_accepted'])

    def test_source_mismatch_is_not_silently_rebound(self):
        (self.source/'coordinate_map.json').write_text('{"changed":true}')
        with self.assertRaisesRegex(ValueError, 'hash mismatch'):
            audit(self.candidate, self.root)

    def test_missing_identity_and_path_escape_rejected(self):
        original = copy.deepcopy(self.candidate)
        self.candidate['source_directory'] = '../elsewhere'
        with self.assertRaisesRegex(ValueError, 'escapes'):
            audit(self.candidate, self.root)
        self.candidate = original
        del self.candidate['source_sha256']['reference.npz']
        with self.assertRaisesRegex(ValueError, 'Bind'):
            audit(self.candidate, self.root)

    def test_dry_or_shallow_centre_rejected(self):
        self.wet[15, 50] = 0
        self.rebind()
        with self.assertRaisesRegex(ValueError, 'Dry/shallow'):
            audit(self.candidate, self.root)
        self.wet[15, 50] = 1
        self.bed[15, 50] = 99.66
        self.rebind()
        with self.assertRaisesRegex(ValueError, 'Dry/shallow'):
            audit(self.candidate, self.root)

    def test_dry_footprint_reported_not_hidden(self):
        self.wet[15, 51] = 0
        self.rebind()
        result = audit(self.candidate, self.root)
        self.assertEqual(result['sites'][0]['dry_support_cells'], 1)
        self.assertFalse(result['engine_accepted'])

    def test_nonfinite_invalid_and_snapped_features_rejected(self):
        for field, value in ((0, float('nan')), (1, 50), (0, 101), (3, 0),
                             (3, 1.21), (4, 1.9), (4, 7.1), (5, -.1), (5, 1.1)):
            with self.subTest(field=field, value=value):
                candidate = copy.deepcopy(self.candidate)
                candidate['features'][0][field] = value
                with self.assertRaises(ValueError):
                    audit(candidate, self.root)

    def test_rotated_support_includes_lateral_width(self):
        self.candidate['features'][0][2] = 90
        self.candidate['quiet_station_intervals_m'] = [[111, 200]]
        with self.assertRaisesRegex(ValueError, 'quiet interval'):
            audit(self.candidate, self.root)

    def test_tail_cannot_froth_quiet_pool(self):
        self.candidate['quiet_station_intervals_m'] = [[128, 200]]
        with self.assertRaisesRegex(ValueError, 'quiet interval'):
            audit(self.candidate, self.root)

    def test_invalid_grid_rejected(self):
        self.x[3] = self.x[2]
        self.rebind()
        with self.assertRaisesRegex(ValueError, 'Invalid source grid'):
            audit(self.candidate, self.root)

    def test_committed_sockdolager_candidate(self):
        path = ROOT/'physics/data/real_world/colorado_river_grand_canyon_rowing/observed_rapids/sockdolager_profile_candidate_2026_10_07.json'
        candidate = json.loads(path.read_text())
        result = audit(candidate)
        self.assertEqual(len(result['sites']), 16)
        self.assertTrue(result['quiet_intervals_clear'])
        self.assertGreaterEqual(min(row['constructed_reference_depth_m'] for row in result['sites']), .35)
        self.assertFalse(candidate['runtime_implemented'])


if __name__ == '__main__':
    unittest.main()
