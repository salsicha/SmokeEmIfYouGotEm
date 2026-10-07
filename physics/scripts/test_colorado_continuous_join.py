import copy
import unittest
import tempfile
from pathlib import Path

import numpy as np

from join_colorado_continuous_scenarios import merge_registered, write_native_arrays


class ContinuousJoin(unittest.TestCase):
    def test_transposed_terrain_serializes_row_major_without_moving_values(self):
        bed = np.arange(35., dtype=float).reshape(7, 5).T
        self.assertTrue(bed.flags.f_contiguous)
        h, u, v = bed*.01+1., bed*.02, bed*0.
        with tempfile.TemporaryDirectory() as folder:
            pkg = Path(folder)
            write_native_arrays(pkg, bed, h, u, v)
            actual = np.load(pkg/'bed.npy')
            self.assertTrue(actual.flags.c_contiguous)
            np.testing.assert_array_equal(actual, bed)
            with np.load(pkg/'initial_state.npz') as state:
                for key in state.files:
                    self.assertTrue(state[key].flags.c_contiguous, key)
                np.testing.assert_allclose(state['eta']-actual, h, atol=1e-14, rtol=0)

    def setUp(self):
        self.grid = dict(nx=7, ny=5, dx=2., dy=2., origin_x=100., origin_y=-4.)
        self.bed = np.ones((5, 7))*20.
        self.padding = np.zeros((5, 7), bool)
        self.items = []
        for start, ny in ((100., 5), (106., 3)):
            self.items.append(dict(grid=dict(nx=4, ny=ny, dx=2., dy=2., origin_x=start,
                                            origin_y=-(ny-1)),
                bed=np.ones((ny, 4))*20., depth=np.ones((ny, 4))*2.,
                u=np.ones((ny, 4))*.5, v=np.zeros((ny, 4)),
                classified_water=np.ones((ny, 4), bool), reference_surface=np.ones(4)*22.))

    def run_merge(self, items=None):
        return merge_registered(self.items if items is None else items, self.bed, self.grid, self.padding)

    def test_exact_overlap_and_explicit_dry_padding(self):
        state, mask, surface, covered = self.run_merge()
        self.assertEqual(int((~covered).sum()), 6)
        self.assertTrue(np.array_equal(mask, covered))
        self.assertTrue((surface == 22).all())
        self.assertTrue((state['depth'][~covered] == 0).all())
        self.assertTrue((state['depth'][covered] == 2).all())

    def test_conflicting_state_is_not_blended(self):
        for key in ('depth', 'u', 'v'):
            items = copy.deepcopy(self.items)
            items[1][key][1, 0] += .001
            with self.assertRaisesRegex(ValueError, 'states disagree'):
                self.run_merge(items)

    def test_terrain_mismatch_refused(self):
        self.items[1]['bed'][1, 0] += .01
        with self.assertRaisesRegex(ValueError, 'rendered triangles'):
            self.run_merge()

    def test_missing_wet_padding_refused(self):
        self.padding[0, -1] = True
        with self.assertRaisesRegex(ValueError, 'classified water'):
            self.run_merge()

    def test_fractional_lattice_refused(self):
        self.items[1]['grid']['origin_x'] += .2
        with self.assertRaisesRegex(ValueError, 'exact cell lattice'):
            self.run_merge()

    def test_stage_or_classification_conflict_refused(self):
        items = copy.deepcopy(self.items)
        items[1]['reference_surface'][0] += .01
        with self.assertRaisesRegex(ValueError, 'stage references'):
            self.run_merge(items)
        self.items[1]['classified_water'][1, 0] = False
        with self.assertRaisesRegex(ValueError, 'classifications disagree'):
            self.run_merge()


if __name__ == '__main__':
    unittest.main()
