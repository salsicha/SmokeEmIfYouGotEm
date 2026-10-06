"""Mutation checks for the independent candidate audit, no engine/cook required."""
import sys
import unittest
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from audit_south_fork_discharge_bed_tiles import grid_check, tile_check


class TileAuditTests(unittest.TestCase):
    def setUp(self):
        self.prior = np.arange(12, dtype=np.float32).reshape(3, 4) + 220
        self.bed = self.prior.copy()
        self.bed[1, 2] -= 1
        self.index = np.array([0, 1, 2, 3], dtype=np.int64)
        # A 2x2 source tile starts at (row1,col1) in the global grid.
        self.old = dict(xyz_local_m=np.array([[0, 0, 5], [2, 0, 6], [0, -2, 9], [2, -2, 10]], dtype=np.float64),
                        triangles=np.array([[0, 1, 2], [1, 3, 2]]), source_grid_vertex_index=self.index)
        self.new = {k: v.copy() for k, v in self.old.items()}
        self.new['xyz_local_m'][1, 2] -= 1

    def check(self):
        return tile_check(self.old, self.new, self.prior, self.bed, (2, 2), (1, 1), 220)

    def test_offset_and_changed_vertex(self):
        self.assertEqual(self.check(), (1, 1.0))

    def test_wrong_candidate_height_rejected(self):
        self.new['xyz_local_m'][0, 2] += .001
        with self.assertRaisesRegex(ValueError, 'Candidate/grid mismatch'):
            self.check()

    def test_topology_index_and_xy_mutations_rejected(self):
        for key, position in [('triangles', (0, 1)), ('source_grid_vertex_index', 0), ('xyz_local_m', (0, 0))]:
            with self.subTest(key=key):
                original = self.new[key].copy()
                self.new[key][position] += 1
                with self.assertRaises(ValueError):
                    self.check()
                self.new[key] = original

    def test_wrong_offset_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Prior/grid mismatch'):
            tile_check(self.old, self.new, self.prior, self.bed, (2, 2), (0, 0), 220)

    def test_dry_and_protected_mutations_rejected(self):
        grid = dict(shape=(3, 4), first_vertex_utm_m=(0, 4), cell_m=2)
        mask = np.zeros((3, 4), dtype=np.uint8)
        mask[1, 2] = 1
        result = grid_check(self.prior, self.bed, mask, grid, (0, 0, 0, 0))
        self.assertEqual(result['changed_grid_vertices'], 1)
        self.assertEqual(result['dry_vertices_checked'], 11)
        with self.assertRaisesRegex(ValueError, 'Protected rapid grid changed'):
            grid_check(self.prior, self.bed, mask, grid, (4, 2, 4, 2))
        mask[1, 2] = 0
        with self.assertRaisesRegex(ValueError, 'Dry grid vertices changed'):
            grid_check(self.prior, self.bed, mask, grid, (0, 0, 0, 0))

    def test_nodata_must_be_preserved_not_introduced(self):
        self.prior[0, 0] = self.bed[0, 0] = np.nan
        mask = np.ones((3, 4), dtype=np.uint8)
        grid = dict(shape=(3, 4), first_vertex_utm_m=(0, 4), cell_m=2)
        result = grid_check(self.prior, self.bed, mask, grid, (0, 0, 0, 0))
        self.assertEqual(result['retained_nodata_vertices'], 1)
        self.bed[0, 1] = np.nan
        with self.assertRaisesRegex(ValueError, 'Finite grid coverage changed'):
            grid_check(self.prior, self.bed, mask, grid, (0, 0, 0, 0))


if __name__ == '__main__':
    unittest.main()
