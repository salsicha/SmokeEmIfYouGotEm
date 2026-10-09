import json
from pathlib import Path
import tempfile
import unittest

import numpy as np

from build_chilko_coarse_settle import blocks, build, coarse_ghosts
import warm_start_chilko_from_coarse as warm


def write_inputs(root, ny=7, nx=8):
    scenario = root / 'scenario'
    scenario.mkdir(parents=True)
    rows, cols = np.indices((ny, nx))
    bed = 100.0 - 0.1 * cols + 0.5 * np.abs(rows - ny // 2)
    channel = np.abs(rows - ny // 2) <= 1
    h = np.where(channel, 1.0 + 0.05 * cols, 0.0)
    u = np.where(channel, 2.0, 0.0)
    v = np.where(channel, 0.1, 0.0)
    np.save(scenario / 'bed.npy', bed)
    np.savez_compressed(scenario / 'initial_state.npz', depth=h, eta=bed + h, u=u, v=v, hu=h * u, hv=h * v, wet=h > 1e-6)
    ghosts = [[float(bed[r, 0]), float(h[r, 0]), float(u[r, 0]), 0.0] for _ in range(2) for r in range(ny)]
    spec = dict(grid=dict(nx=nx, ny=ny, dx=2.0, dy=2.0, origin_x=-6.0, origin_y=-6.0), fixed_dt=0.05,
                boundaries=[dict(edge='west', kind='discharge_profile', ghost_cells=ghosts, metadata={}),
                            dict(edge='east', kind='outflow', stage=99.0), dict(edge='south', kind='bank'),
                            dict(edge='north', kind='bank')],
                metadata=dict(scenario_id='synthetic'), roughness=0.02, feature_count=0)
    (scenario / 'scenario.json').write_text(json.dumps(spec))
    for name in ('features.json', 'probes.json'):
        (scenario / name).write_text('[]')
    for name in ('coordinate_map.json',):
        (root / name).write_text('{}')
    np.savez_compressed(root / 'reference.npz', station=np.arange(nx, dtype=float))
    (root / 'build_report.json').write_text(json.dumps(dict(name='synthetic')))
    return bed, h, u


def write_frame(coarse):
    """A native frame of the coarse initial state, in the solver's CSV layout."""
    spec = json.loads((coarse / 'scenario/scenario.json').read_text())
    g = spec['grid']
    with np.load(coarse / 'scenario/initial_state.npz') as s:
        state = {k: s[k] for k in s.files}
    cook = coarse / 'native' / spec['metadata']['scenario_id']
    (cook / 'frames').mkdir(parents=True)
    names = ('row', 'col', 'x', 'y', 'h', 'eta', 'u', 'v', 'hu', 'hv', 'wet')
    lines = [','.join(names)]
    for r in range(g['ny']):
        for c in range(g['nx']):
            lines.append(','.join(repr(float(v)) for v in (
                r, c, g['origin_x'] + c * g['dx'], g['origin_y'] + r * g['dy'], state['depth'][r, c], state['eta'][r, c],
                state['u'][r, c], state['v'][r, c], state['hu'][r, c], state['hv'][r, c], float(state['wet'][r, c]))))
    (cook / 'frames/frame_0000.csv').write_text('\n'.join(lines) + '\n')
    (cook / 'manifest.json').write_text(json.dumps(dict(frames=['frames/frame_0000.csv'])))


class CoarseSettleTests(unittest.TestCase):
    def test_blocks_ignore_lateral_padding(self):
        total, count = blocks(np.ones((5, 4)), 2)
        self.assertEqual(total.shape, (3, 2))
        self.assertTrue(np.array_equal(count[-1], [2, 2]))

    def test_ghost_discharge_is_preserved(self):
        ny = 7
        h = np.r_[0, 0, 1.0, 1.2, 0.8, 0, 0]
        u = np.r_[0, 0, 2.0, 2.5, 1.5, 0, 0]
        ghosts = [[100.0, a, b, 0.0] for _ in range(2) for a, b in zip(h, u)]
        coarse = np.asarray(coarse_ghosts(ghosts, ny, 2)).reshape(2, 4, 4)
        for layer in coarse:
            self.assertAlmostEqual((layer[:, 1] * layer[:, 2]).sum() * 4.0, (h * u).sum() * 2.0)

    def test_volume_momentum_and_grid_are_consistent(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            bed, h, u = write_inputs(root / 'inputs')
            result = build(root / 'inputs', 2, root / 'coarse')
            meta = result['metadata']['coarse_settle']
            self.assertAlmostEqual(meta['fine_volume_m3'], meta['coarse_volume_m3'])
            self.assertEqual(result['grid'], dict(nx=4, ny=4, dx=4.0, dy=4.0, origin_x=-5.0, origin_y=-5.0))
            self.assertEqual(result['fixed_dt'], 0.1)
            with np.load(root / 'coarse/scenario/initial_state.npz') as state:
                q_fine = (h * u).sum(axis=0)[::2] * 2.0 + (h * u).sum(axis=0)[1::2] * 2.0
                q_coarse = (state['depth'] * state['u']).sum(axis=0) * 4.0 * 2
                self.assertTrue(np.allclose(q_coarse, q_fine))
                self.assertTrue(np.array_equal(state['wet'], state['depth'] > 1e-6))
            with self.assertRaises(ValueError):
                build(root / 'inputs', 2, root / 'coarse')

    def test_warm_start_keeps_inputs_and_solver_dry_rule(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            bed, h, u = write_inputs(root / 'inputs')
            build(root / 'inputs', 2, root / 'coarse')
            write_frame(root / 'coarse')
            summary = warm.build(root / 'inputs', root / 'coarse', root / 'warm')
            for name in warm.COPIED:
                self.assertEqual((root / 'warm' / name).read_bytes(), (root / 'inputs' / name).read_bytes())
            with np.load(root / 'warm/scenario/initial_state.npz') as s:
                self.assertTrue(np.array_equal(s['wet'], s['depth'] > 1e-6))
                self.assertTrue(np.all(s['u'][~s['wet']] == 0) and np.all(s['v'][~s['wet']] == 0))
                self.assertTrue(np.allclose(s['eta'] - s['depth'], bed))
            self.assertGreater(summary['warm_volume_m3'], 0)
            report = json.loads((root / 'warm/build_report.json').read_text())
            self.assertEqual(report['name'], 'synthetic')
            self.assertEqual(report['coarse_warm_start']['factor'], 2)


if __name__ == '__main__':
    unittest.main()
