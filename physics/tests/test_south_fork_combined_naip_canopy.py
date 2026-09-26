"""Data-backed regression for the additive pass and preserved channel repair.

Engine readback is separate: verify_south_fork_combined_naip_canopy.py.
These tests cannot by themselves prove what the playable packages contain.
"""
import hashlib
import json
import sys
import unittest
from pathlib import Path
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'physics/scripts'))
from audit_south_fork_canopy_channel import sample_mask


class CombinedCanopyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        base = ROOT / 'physics/data/real_world/south_fork_american_chili_bar/reconstruction_2026_09/full_reach'
        original = base / 'naip_canopy_20260926/placement.json'
        cls.original_sha = hashlib.sha256(original.read_bytes()).hexdigest()
        cls.original = json.loads(original.read_text())
        cls.additions = json.loads((base / 'naip_canopy_20260926/lower_gorge_additions_placement.json').read_text())
        cls.repair = json.loads((ROOT / 'docs/reconstruction-review-2026-09-07/canopy-channel-repair/repair.json').read_text())
        cls.mask_path = base / 'source_context_extension/unknown_submerged_bed_mask.tif'
        cls.context = json.loads((cls.mask_path.parent / 'manifest.json').read_text())
        with Image.open(cls.mask_path) as image:
            cls.mask = np.array(image)

    def values(self, data):
        self.assertEqual(data['world_origin_utm_m'], [689237., 4293073.])
        self.assertEqual(data['world_y_sign'], -1)
        positions = np.asarray([r['world_root_cm'] for r in data['instances']])
        xy = np.column_stack((positions[:, 0] / 100 + 689237., 4293073. - positions[:, 1] / 100))
        grid = self.context['grid']
        return sample_mask(self.mask, xy, grid['first_vertex_utm_m'], grid['cell_m'])

    def test_mask_identity_and_additive_parent(self):
        digest = hashlib.sha256(self.mask_path.read_bytes()).hexdigest()
        self.assertEqual(list(self.mask.shape), self.context['grid']['shape'])
        self.assertEqual(digest, self.context['artifacts'][self.mask_path.name])
        self.assertEqual(digest, self.repair['mask_sha256'])
        self.assertEqual(digest, self.additions['sources'][self.mask_path.relative_to(ROOT).as_posix()])
        self.assertEqual(self.original_sha, self.repair['placement_sha256'])
        self.assertEqual(self.original_sha, self.additions['addition_to_placement_sha256'])

    def test_original_removals_are_exactly_water_cells(self):
        values = self.values(self.original)
        wet = {r['id'] for r, value in zip(self.original['instances'], values) if value == 1}
        self.assertEqual(len(wet), 266)
        self.assertEqual(wet, set(self.repair['removed_ids']))
        self.assertEqual(int((values == 255).sum()), 0)

    def test_every_added_root_is_dry_and_covered(self):
        values = self.values(self.additions)
        self.assertEqual(len(values), 24211)
        self.assertTrue(np.all(values == 0))

    def test_combined_count_and_no_reintroduced_or_duplicate_roots(self):
        old = {tuple(r['world_root_cm'][:2]) for r in self.original['instances']}
        added = {tuple(r['world_root_cm'][:2]) for r in self.additions['instances']}
        self.assertEqual(len(old), 140683)
        self.assertEqual(len(added), 24211)
        self.assertFalse(old & added)
        self.assertEqual(len(old) - self.repair['removed_count'] + len(added), 164628)


if __name__ == '__main__':
    unittest.main(verbosity=2)
