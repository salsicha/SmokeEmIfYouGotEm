import gzip
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from types import SimpleNamespace
import numpy as np
from native_frame_io import load_frame, native_frame_paths, NativeFrameStore
from continue_colorado_catalog_cook import restart_state


HEADER = 'row,col,x,y,h,eta,u,v,hu,hv,wet,normal_x,normal_y,normal_z,froude\n'


class NativeFrameIOTests(unittest.TestCase):
    def test_disk_backed_frames_are_exact_and_scratch_is_scoped(self):
        for compressed in (False,True):
            path=self.write(compressed=compressed);before=path.read_bytes()
            expected=load_frame(path,(2,3))
            with patch('native_frame_io.shutil.disk_usage',return_value=SimpleNamespace(free=100*1024**3)):
                with NativeFrameStore(self.root) as store:
                    actual=store.load(path,(2,3),block_cells=2)
                    scratch=Path(store._temporary.name)
                    self.assertTrue(scratch.is_dir())
                    for key in expected:
                        self.assertIsInstance(actual[key],np.memmap)
                        np.testing.assert_array_equal(actual[key],expected[key])
                self.assertFalse(scratch.exists())
                with self.assertRaisesRegex(ValueError,'not open'):store.load(path,(2,3))
            self.assertEqual(before,path.read_bytes())

    def test_disk_guard_refuses_before_mapping_allocation(self):
        path=self.write()
        with NativeFrameStore(self.root) as store:
            with patch('native_frame_io.shutil.disk_usage',return_value=SimpleNamespace(free=40*1024**3)), \
                 patch('native_frame_io.np.lib.format.open_memmap') as allocate:
                with self.assertRaisesRegex(ValueError,'headroom'):store.load(path,(2,3))
                allocate.assert_not_called()

    def test_failed_mapping_parse_cleans_only_private_scratch(self):
        path=self.write(self.text.replace(',901,',',nan,',1));before=path.read_bytes()
        with patch('native_frame_io.shutil.disk_usage',return_value=SimpleNamespace(free=100*1024**3)):
            with self.assertRaisesRegex(ValueError,'Nonfinite'):
                with NativeFrameStore(self.root) as store:
                    scratch=Path(store._temporary.name)
                    store.load(path,(2,3),block_cells=2)
        self.assertFalse(scratch.exists())
        self.assertEqual(before,path.read_bytes())

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='raftsim-frame-io-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.text = HEADER+''.join(
            f'{i//3},{i%3},{i%3*2},{i//3*2},1,901,.125,-.25,.125,-.25,1,0,0,1,.1\n'
            for i in range(6))

    def write(self, text=None, compressed=False):
        path = self.root/('frame.csv.gz' if compressed else 'frame.csv')
        with (gzip.open if compressed else open)(path, 'wt', encoding='utf-8', newline='') as f:
            f.write(self.text if text is None else text)
        return path

    def test_exact_all_field_parity_across_blocks_and_formats(self):
        for compressed in (False, True):
            path = self.write(compressed=compressed)
            old = np.genfromtxt(path, delimiter=',', names=True)
            for block in (1, 2, 4, 16384):
                actual = load_frame(path, (2, 3), block_cells=block)
                self.assertEqual(set(actual), set(old.dtype.names))
                for name in actual:
                    np.testing.assert_array_equal(actual[name], old[name].reshape(2, 3))
                restored = restart_state(actual, np.full((2, 3), 900.), dict(ny=2, nx=3))
                np.testing.assert_array_equal(restored['hu'], actual['hu'])

    def test_single_cell(self):
        frame = load_frame(self.write(HEADER+self.text.splitlines()[1]+'\n'), (1, 1))
        self.assertEqual(frame['h'][0, 0], 1.)

    def test_refuse_corrupt_values_shapes_and_order(self):
        lines = self.text.splitlines(keepends=True)
        variants = [lines[0]+''.join(lines[2:]), self.text+lines[-1],
                    lines[0]+lines[2]+lines[1]+''.join(lines[3:]),
                    self.text.replace(',1,901,', ',-1,901,', 1),
                    self.text.replace(',0,0,1,.1', ',0,0,1,nan', 1),
                    self.text.replace('row,col', 'row,row', 1),
                    self.text.replace(',901,', ',901,,', 1), self.text+'\n']
        for i, text in enumerate(variants):
            with self.subTest(corruption=i), self.assertRaises(ValueError):
                load_frame(self.write(text), (2, 3), block_cells=2)

    def test_truncated_gzip_refused(self):
        path = self.write(compressed=True)
        path.write_bytes(path.read_bytes()[:-8])
        with self.assertRaises((EOFError, OSError)):
            load_frame(path, (2, 3), block_cells=2)

    def test_manifest_strict_collection_and_format(self):
        (self.root/'frames').mkdir()
        for compressed in (False, True):
            suffix = '.csv.gz' if compressed else '.csv'
            path = self.root/f'frames/frame_0000{suffix}'
            path.write_bytes(b'fixture')
            native = dict(frames=[path.relative_to(self.root).as_posix()])
            if compressed:
                native['frame_storage'] = 'streamed_lossless_gzip_csv_v1'
            self.assertEqual(native_frame_paths(self.root, native), [path])
            for names in ([], ['../outside.csv'], ['frames/frame_0001'+suffix],
                          native['frames']*2):
                with self.subTest(names=names), self.assertRaises(ValueError):
                    native_frame_paths(self.root, dict(native, frames=names))
            with self.assertRaises(ValueError):
                native_frame_paths(self.root, dict(native, frame_storage='unknown'))
            with self.assertRaises(ValueError):
                native_frame_paths(self.root, native, minimum=3)
            extra = self.root/'frames/frame_0001.csv.partial'
            extra.write_bytes(b'incomplete')
            with self.assertRaises(ValueError):
                native_frame_paths(self.root, native)
            extra.unlink()
            path.unlink()


@unittest.skipUnless(os.environ.get('RAFTSIM_STREAM_TEST_SOLVER'), 'Set isolated native solver path for CLI parity')
class NativeStreamCLIParityTests(unittest.TestCase):
    def test_actual_solver_buffered_streamed_parity(self):
        solver = Path(os.environ['RAFTSIM_STREAM_TEST_SOLVER']).resolve()
        root = Path(__file__).resolve().parents[2]
        fixture = root/'unreal/Plugins/SEIYGECore/data/validation/milestone17/analytic_fixtures/fixtures/lake_at_rest_balance/scenario'
        with tempfile.TemporaryDirectory(prefix='raftsim-cli-parity-') as temporary:
            for steps, progress in ((0, False), (5, False), (6, True)):
                outputs = []
                for streaming in (False, True):
                    output = Path(temporary)/f'{steps}-{streaming}'
                    command = [str(solver), '--scenario', str(fixture), '--output', str(output),
                               '--steps', str(steps), '--frame-interval', '2', '--solver-mode', 'finite_volume',
                               '--boundary-mode', 'scenario', '--flux-scheme', 'hll', '--spatial-order', '2',
                               '--cfl', '.2', '--feature-strength-scale', '0', '--no-preserve-initial-mass',
                               '--disable-fixture-calibrations']
                    if streaming: command.append('--stream-output')
                    if progress: command.append('--progress')
                    run = subprocess.run(command, capture_output=True, text=True, timeout=90)
                    self.assertEqual(run.returncode, 0, run.stdout+run.stderr)
                    directories = list(output.iterdir())
                    self.assertEqual(len(directories), 1)
                    outputs.append(directories[0])
                a, b = outputs
                manifests = [json.loads((p/'manifest.json').read_text()) for p in outputs]
                files = [native_frame_paths(p, m) for p, m in zip(outputs, manifests)]
                self.assertEqual(len(files[0]), 1+steps//2+int(steps % 2 != 0))
                self.assertEqual(len(files[0]), len(files[1]))
                for plain, compressed in zip(*files):
                    with gzip.open(compressed, 'rt') as f:
                        self.assertEqual(plain.read_text(), f.read())
                for name in ('validation.json', *manifests[0]['probes'], *manifests[0]['cross_sections']):
                    self.assertEqual((a/name).read_text(), (b/name).read_text())
                for key, value in manifests[0].items():
                    if key != 'frames': self.assertEqual(value, manifests[1][key], key)
            refused = subprocess.run([str(solver), '--scenario', str(fixture), '--stream-output'],
                                     capture_output=True, text=True, timeout=30)
            self.assertEqual(refused.returncode, 1)
            self.assertIn('requires --disable-fixture-calibrations', refused.stderr)


if __name__ == '__main__':
    unittest.main()
