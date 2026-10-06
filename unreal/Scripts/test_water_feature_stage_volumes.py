"""Synthetic evidence-integrity and fixed-field integration checks."""
import json
from pathlib import Path
import tempfile
import unittest

import numpy as np

from audit_water_feature_stage_volumes import audit, sha256


class StageVolumeTests(unittest.TestCase):
    def fixture(self, directory, extra=False):
        root = Path(directory)
        data = root/'cache'/'data'
        data.mkdir(parents=True)
        original = data/'fluid_data_0096.vdb'
        original.write_bytes(b'synthetic integrity fixture; not a native VDB')
        phi, solid = root/'phi.npy', root/'solid.npy'
        np.save(phi, -np.ones((2, 2, 2), np.float32))
        np.save(solid, np.ones((2, 2, 2), np.float32))
        report = dict(complete=True, original_vdb_unchanged=True,
                      resumed_primary_matches_native_count_positions_and_velocities=True,
                      frame=96, original_vdb_sha256=sha256(original),
                      solid_file=str(solid), engine_cell_size_m=[1, 1, 1],
                      extra_extrapolation_checkpoints=extra,
                      rows=[dict(stage=f'synthetic-{index}', interface_file=str(phi),
                                 interface_sha256=sha256(phi), partial_cell_volume_m3=8.,
                                 outside_solid_sign_volume_m3=8.) for index in range(8 if extra else 6)])
        path = root/'probe.json'
        path.write_text(json.dumps(report))
        return path, report, original, phi

    def test_six_and_eight_checkpoints(self):
        for extra in (False, True):
            with tempfile.TemporaryDirectory() as directory:
                path, _, _, _ = self.fixture(directory, extra)
                result = audit(path, [8, 16])
                self.assertTrue(result['originals_unchanged'])
                self.assertFalse(result['accepted'])
                self.assertEqual(result['net_local_step_delta_m3'], {'8': 0., '16': 0.})

    def test_changed_original_or_interface_refused(self):
        for target in ('original', 'phi'):
            with tempfile.TemporaryDirectory() as directory:
                path, _, original, phi = self.fixture(directory)
                (original if target == 'original' else phi).write_bytes(b'changed')
                with self.assertRaisesRegex(ValueError, 'changed|mismatch'):
                    audit(path, [8])

    def test_incomplete_and_wrong_checkpoint_count_refused(self):
        for failure in ('incomplete', 'missing_checkpoint'):
            with tempfile.TemporaryDirectory() as directory:
                path, report, _, _ = self.fixture(directory)
                if failure == 'incomplete':
                    report['complete'] = False
                else:
                    report['rows'].pop()
                path.write_text(json.dumps(report))
                with self.assertRaises(ValueError):
                    audit(path, [8])


if __name__ == '__main__':
    unittest.main()
