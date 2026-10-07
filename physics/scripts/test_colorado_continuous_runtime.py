import copy
import json
import struct
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np

from export_colorado_continuous_runtime import registered_queries, write_fields, export, BAND


class ContinuousRuntime(unittest.TestCase):
    def setUp(self):
        self.mapping = dict(schema='raftsim.curved_river_coordinate_map.v1', world_y_sign=-1,
            horizontal_origin_epsg6404_m=[200., 300.], vertical_datum_m=310.,
            points=[[s, s, 0., 0., 1.] for s in range(0, 22, 2)])
        self.terrain = dict(horizontal_origin_epsg6404_m=[200., 300.], vertical_datum_m=310.)
        self.grid = dict(nx=4, ny=3, dx=2., dy=2., origin_x=8., origin_y=-2.)

    def test_global_station_subset_is_not_recentred(self):
        station, queries = registered_queries(self.mapping, self.terrain, self.grid)
        np.testing.assert_array_equal(station, [8, 10, 12, 14])
        np.testing.assert_array_equal(queries[0], [[208, 298], [210, 298], [212, 298], [214, 298]])
        np.testing.assert_array_equal(queries[-1, -1], [214, 302])

    def test_wrong_frame_or_normal_refused(self):
        for key, value in [('vertical_datum_m', 0.), ('world_y_sign', 1),
                           ('horizontal_origin_epsg6404_m', [201., 300.])]:
            mapping = dict(self.mapping, **{key: value})
            with self.assertRaisesRegex(ValueError, 'same geographic frame'):
                registered_queries(mapping, self.terrain, self.grid)
        mapping = copy.deepcopy(self.mapping); mapping['points'][5][4] = 2.
        with self.assertRaisesRegex(ValueError, 'Nonunit'):
            registered_queries(mapping, self.terrain, self.grid)

    def test_fractional_or_uncovered_grid_refused(self):
        for origin in (8.1, -2., 20.):
            with self.assertRaisesRegex(ValueError, 'shared hydraulic lattice'):
                registered_queries(self.mapping, self.terrain, dict(self.grid, origin_x=origin))

    def test_fields_and_binary_preserve_station_major_support(self):
        station, _ = registered_queries(self.mapping, self.terrain, self.grid)
        bed = np.arange(12.).reshape(4, 3).T + 920.
        h = np.full(bed.shape, 2.); h[0, 0] = 0.
        frame = dict(h=h, eta=bed+h, u=h*.2, v=h*.1, wet=h > 0)
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)/'fields'
            arrays, baseline = write_fields(folder, self.grid, station, frame, bed)
            for key, expected in [('bed', bed), ('h', h), ('u', frame['u']), ('v', frame['v'])]:
                actual = np.load(folder/BAND/(key+'.npy'))
                np.testing.assert_allclose(actual, expected, rtol=1e-7)
                self.assertTrue(actual.flags.c_contiguous)
                self.assertEqual(arrays[key]['shape'], [3, 4])
            with (folder/baseline['file']).open('rb') as stream:
                self.assertEqual(struct.unpack('<IIiiff', stream.read(24)), (0x52534246, 1, 3, 4, -2., 2.))
                decoded = []
                for dtype in ('<f4', '<f4', '<f4', 'u1'):
                    count, = struct.unpack('<i', stream.read(4))
                    decoded.append(np.frombuffer(stream.read(count*np.dtype(dtype).itemsize), dtype=dtype))
                self.assertEqual(stream.read(), b'')
            np.testing.assert_array_equal(decoded[0], station)
            np.testing.assert_array_equal(decoded[1].reshape(4, 3), frame['eta'].T)
            np.testing.assert_array_equal(decoded[3].reshape(4, 3), frame['wet'].T)

    def test_failed_cook_cannot_create_runtime(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); out = root/'export'
            with patch('export_colorado_continuous_runtime.checked_cook', side_effect=ValueError('Cook did not pass its construction screen')):
                with self.assertRaisesRegex(ValueError, 'construction screen'):
                    export(root/'inputs', root/'cook', root/'review.json', out)
            self.assertFalse(out.exists())

    def test_flow_band_is_explicit_and_cannot_escape_export(self):
        station,_=registered_queries(self.mapping,self.terrain,self.grid)
        bed=np.ones((3,4));frame=dict(h=bed,eta=bed*2,u=bed,v=bed*0,wet=bed)
        with tempfile.TemporaryDirectory() as directory:
            folder=Path(directory)/'fields'
            arrays,baseline=write_fields(folder,self.grid,station,frame,bed,'lidar_flight_window_inferred')
            self.assertTrue(arrays['bed']['file'].startswith('lidar_flight_window_inferred/'))
            self.assertNotIn(BAND,baseline['file'])
            with self.assertRaisesRegex(ValueError,'Unsafe flow band'):
                write_fields(Path(directory)/'other',self.grid,station,frame,bed,'../bad')


if __name__ == '__main__':
    unittest.main()
