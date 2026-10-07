import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np

from capture_lidarbc_plan import acquire, checked_plan
from mosaic_lidarbc_crops import CRS, VERTICAL, sha


class PlanCaptureTests(unittest.TestCase):
    def plan(self, root):
        route = root/'route.json'; route.write_text('{}')
        catalogue = root/'catalogue.json'; catalogue.write_text('{}')
        filename = 'bc_test.tif'
        url = 'https://nrs.objectstore.gov.bc.ca/gdwuts/test/dem/'+filename
        self.attributes = dict(filename=filename, s3Url=url, spacing='1 metre', projection='utm10')
        data = dict(schema='raftsim.lidarbc_continuous_capture_plan.v1', route=str(route),
                    route_sha256=sha(route), catalogue_sha256=sha(catalogue),
                    accepted_headers=[dict(filename=filename, url=url,
                        catalogue_attributes=self.attributes, raster_bounds=[0, 0, 4, 2])],
                    cells=[dict(cell=[i, 0], bounds=[i*2, 0, i*2+2, 2]) for i in range(2)],
                    capture_requests=[dict(cell=[i, 0], tile=filename,
                        window_utm=[i*2, 0, i*2+2, 2]) for i in range(2)])
        path = root/'plan.json'; path.write_text(json.dumps(data))
        return path

    def capture(self, filename, bounds, path):
        x0, y0, x1, y1 = bounds
        data = np.ones((y1-y0, x1-x0), dtype=np.float32)
        np.savez(path, height_m=data, x0=float(x0), y_top=float(y1), cell_m=1.)
        catalogue = path.with_suffix('.catalog.json'); catalogue.write_text('{}')
        meta = dict(schema='raftsim.lidarbc_dem_crop.v1', npz_sha256=sha(path),
                    crs=CRS, vertical=VERTICAL, cell_m=1., window_utm=bounds,
                    shape=list(data.shape), missing_pixels=0, valid_share=1.,
                    catalogue_sha256=sha(catalogue), tiles=[dict(file=filename,
                        url=self.attributes['s3Url'], source_catalogue_attributes=self.attributes)])
        path.with_suffix('.json').write_text(json.dumps(meta))

    def test_serial_resume_does_not_repeat_verified_captures(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); plan = self.plan(root); out = root/'out'
            with patch('capture_lidarbc_plan.capture', side_effect=self.capture) as call:
                first = acquire(plan, out, 1)
                self.assertEqual((first['completed'], first['pending']), (1, 1))
                second = acquire(plan, out, 1)
                self.assertTrue(second['source_acquisition_complete'])
                self.assertFalse(second['full_corridor_valid_pixels_verified'])
                self.assertEqual(call.call_count, 2)
                acquire(plan, out, 1)
                self.assertEqual(call.call_count, 2)
            self.assertFalse((out/'capture.lock').exists())

    def test_tampered_completed_pixels_stop_resume(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); plan = self.plan(root); out = root/'out'
            with patch('capture_lidarbc_plan.capture', side_effect=self.capture):
                acquire(plan, out, 1)
            path = out/'request_0000.npz'
            path.write_bytes(path.read_bytes()+b'tampered')
            with patch('capture_lidarbc_plan.capture') as call:
                with self.assertRaisesRegex(ValueError, 'provenance'):
                    acquire(plan, out, 1)
                call.assert_not_called()

    def test_empty_native_windows_recorded_without_fabrication_or_retry(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); plan = self.plan(root); out = root/'out'
            def empty(filename, bounds, path):
                path.with_suffix('.catalog.json').write_text('{}')
                raise ValueError('Native tile has no valid pixels in the requested window')
            with patch('capture_lidarbc_plan.capture', side_effect=empty) as call:
                result = acquire(plan, out, 2)
                self.assertEqual(result['empty_native_requests'], [0, 1])
                self.assertEqual(result['completed'], 0)
                acquire(plan, out, 2)
                self.assertEqual(call.call_count, 2)
            self.assertEqual(list(out.glob('*.npz')), [])

    def test_incomplete_capture_and_live_lock_are_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); plan = self.plan(root); out = root/'out'; out.mkdir()
            lock = out/'capture.lock'; lock.write_text('live')
            with self.assertRaises(FileExistsError):
                acquire(plan, out)
            self.assertEqual(lock.read_text(), 'live')
            lock.unlink()
            def partial(filename, bounds, path):
                path.with_suffix('.catalog.json').write_text('{}')
                raise RuntimeError('network failure')
            with patch('capture_lidarbc_plan.capture', side_effect=partial):
                with self.assertRaises(RuntimeError): acquire(plan, out)
            with patch('capture_lidarbc_plan.capture') as call:
                with self.assertRaisesRegex(ValueError, 'Incomplete capture preserved'):
                    acquire(plan, out)
                call.assert_not_called()
            self.assertTrue((out/'request_0000.catalog.json').exists())

    def test_request_cannot_expand_past_native_intersection(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); plan = self.plan(root)
            data = json.loads(plan.read_text()); data['capture_requests'][0]['window_utm'][2] = 3
            plan.write_text(json.dumps(data))
            with self.assertRaisesRegex(ValueError, 'native intersection'): checked_plan(plan)


if __name__ == '__main__':
    unittest.main()
