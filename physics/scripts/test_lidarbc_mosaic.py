import json
import tempfile
import unittest
from pathlib import Path

import numpy as np

from mosaic_lidarbc_crops import CRS, VERTICAL, mosaic_crops, sha


class LidarBCMosaicTests(unittest.TestCase):
    def make_crop(self, folder, name, values, x0=10, y_top=22):
        path = folder / (name + '.npz')
        data = np.asarray(values, dtype=np.float32)
        np.savez(path, height_m=data, x0=float(x0), y_top=float(y_top), cell_m=1.)
        meta = dict(schema='raftsim.lidarbc_dem_crop.v1', npz_sha256=sha(path),
                    crs=CRS, vertical=VERTICAL, cell_m=1., shape=list(data.shape),
                    window_utm=[x0, y_top-data.shape[0], x0+data.shape[1], y_top],
                    tiles=[dict(file=name)])
        path.with_suffix('.json').write_text(json.dumps(meta))
        return path

    def test_later_source_fills_only_gaps_and_records_disagreement(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            a = self.make_crop(folder, 'a', [[1, np.nan], [3, 4]])
            b = self.make_crop(folder, 'b', [[2, 8], [40, np.nan]], x0=11)
            out = folder / 'mosaic.npz'
            meta = mosaic_crops([a, b], [10, 20, 13, 22], out)
            with np.load(out) as z:
                np.testing.assert_array_equal(z['height_m'], [[1, 2, 8], [3, 4, np.nan]])
                np.testing.assert_array_equal(z['source_index'], [[1, 2, 2], [1, 1, 0]])
            self.assertEqual(meta['missing_pixels'], 1)
            self.assertEqual(meta['inputs'][1]['contributed_pixels'], 2)
            self.assertEqual(meta['inputs'][1]['overlap_abs_difference_m_max'], 36.)
            with self.assertRaises(ValueError):
                mosaic_crops([a, b], [10, 20, 13, 22], out)

    def test_rejects_tampered_frame_hash_and_array(self):
        for field, value in [('crs', 'EPSG:32610'), ('npz_sha256', 'wrong'),
                             ('window_utm', [10.1, 20, 12.1, 22]), ('shape', [3, 2])]:
            with self.subTest(field=field), tempfile.TemporaryDirectory() as tmp:
                folder = Path(tmp)
                a = self.make_crop(folder, 'a', [[1, 2], [3, 4]])
                receipt = a.with_suffix('.json')
                meta = json.loads(receipt.read_text()); meta[field] = value
                receipt.write_text(json.dumps(meta))
                with self.assertRaises(ValueError):
                    mosaic_crops([a], [10, 20, 12, 22], folder / 'bad.npz')
                self.assertFalse((folder / 'bad.npz').exists())

    def test_north_up_offsets_and_output_crop_select_native_centres(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            south = self.make_crop(folder, 'south', [[21, 22], [31, 32]], x0=10, y_top=22)
            north = self.make_crop(folder, 'north', [[11, 12], [91, 92]], x0=10, y_top=23)
            out = folder / 'strip.npz'
            meta = mosaic_crops([south, north], [11, 20, 12, 23], out)
            with np.load(out) as z:
                np.testing.assert_array_equal(z['height_m'], [[12], [22], [32]])
                np.testing.assert_array_equal(z['source_index'], [[2], [1], [1]])
                self.assertEqual(float(z['x0']), 11.)
                self.assertEqual(float(z['y_top']), 23.)
            self.assertEqual(meta['inputs'][1]['overlap_abs_difference_m_max'], 70.)

    def test_all_missing_or_nonintersecting_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            a = self.make_crop(folder, 'a', [[np.nan, np.nan], [np.nan, np.nan]])
            for bounds in ([10, 20, 12, 22], [30, 40, 32, 42]):
                with self.assertRaises(ValueError):
                    mosaic_crops([a], bounds, folder / 'bad.npz')


if __name__ == '__main__':
    unittest.main()
