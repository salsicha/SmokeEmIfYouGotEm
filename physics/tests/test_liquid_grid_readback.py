import sys
from pathlib import Path
import unittest
from unittest.mock import patch
import json
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from analyze_liquid_grid_readback import load_fields


class GridReadbackTest(unittest.TestCase):
    def decode(self, grid, raw):
        with patch.object(Path, 'read_text', return_value=json.dumps({'grids': [grid]})), patch('numpy.fromfile', return_value=raw):
            return load_fields(Path('not-a-real-grid'))

    def test_pressure_float32_is_not_half_converted(self):
        grid = dict(readback_saved=True, texture_size=[2, 1, 1], cells=[2, 1, 1], tiles=[1, 1, 1],
                    rgba_texture=True, encoding='r32f', file='p', attributes=[dict(name='Pressure', type='NiagaraFloat', offset=0)])
        p = np.array([123456.75, -234567.5], dtype='<f4')
        np.testing.assert_array_equal(self.decode(grid, p)['Pressure'].ravel(), p)

    def test_tiled_scalar_offsets(self):
        grid = dict(readback_saved=True, texture_size=[4, 1, 1], cells=[2, 1, 1], tiles=[2, 1, 1],
                    rgba_texture=False, file='p', attributes=[dict(name='Second', type='NiagaraFloat', offset=1)])
        raw = np.zeros((4, 4), dtype='<f2'); raw[:, 0] = [1, 2, 3, 4]
        np.testing.assert_array_equal(self.decode(grid, raw.ravel())['Second'].ravel(), [3, 4])

    def test_incomplete_bytes_rejected(self):
        grid = dict(readback_saved=True, texture_size=[2, 1, 1], file='p')
        with self.assertRaises(ValueError):
            self.decode(grid, np.zeros(3, dtype='<f2'))


if __name__ == '__main__':
    unittest.main()
