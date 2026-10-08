import unittest
from fetch_colorado_terrain_windows import fine_source_selection,verify_colorado_pixels,fine_coverage


class FineSourceTests(unittest.TestCase):
    def test_explicit_padding_bounds_preserve_default_and_outward_coverage(self):
        from fetch_colorado_terrain_windows import capture_bounds
        self.assertEqual(capture_bounds([1.,-19.,252.,233.]),(-400,-420,660,640))
        self.assertEqual(capture_bounds([1.,-19.,252.,233.],10),(-10,-30,270,250))
        self.assertEqual(capture_bounds([0,0,250,250],0),(0,0,250,250))
        for bounds,margin in (([0,0,0,1],10),([0,0,float('nan'),1],10),
                              ([0,0,1,1],-10),([0,0,1,1],11),([0,0,1,1],1001)):
            with self.assertRaises(ValueError):capture_bounds(bounds,margin)

    def test_partial_capture_explicitly_not_composable(self):
        result=fine_coverage([[900.,0.,float('nan'),901.]],[[True,True,True,False]],True)
        self.assertFalse(result['valid_pixel_coverage_verified'])
        self.assertTrue(result['partial_fine_capture'])
        self.assertEqual(result['valid_native_pixels'],1)
        self.assertEqual(result['missing_native_pixels'],3)
        with self.assertRaises(ValueError):
            fine_coverage([[900.,0.]],[[True,True]])

    def test_empty_fine_capture_refused_even_with_partial_option(self):
        with self.assertRaisesRegex(ValueError,'no usable'):
            fine_coverage([[0.,float('nan')]],[[True,True]],True)

    def test_explicit_empty_capture_is_absence_not_valid_terrain(self):
        result=fine_coverage([[0.,float('nan')]],[[True,True]],True,True)
        self.assertTrue(result['native_coverage_absent'])
        self.assertTrue(result['partial_fine_capture'])
        self.assertFalse(result['valid_pixel_coverage_verified'])
        self.assertEqual(result['valid_native_pixels'],0)
        self.assertEqual(result['missing_native_pixels'],2)
        with self.assertRaisesRegex(ValueError,'requires explicit partial'):
            fine_coverage([[0.]],[[True]],False,True)

    def test_zero_filled_pixels_with_valid_mask_are_refused(self):
        with self.assertRaisesRegex(ValueError,'zero-filled'):
            verify_colorado_pixels([[900.,0.]],[[True,True]])

    def test_missing_and_nonfinite_pixels_are_refused(self):
        for values,valid in (([[900.]],[[False]]),([[float('nan')]],[[True]])):
            with self.assertRaises(ValueError):verify_colorado_pixels(values,valid)

    def test_positive_valid_corridor_accepted(self):
        verify_colorado_pixels([[900.,901.]],[[True,True]])

    def row(self, key, resolution, date=0, datum='North American Vertical Datum of 1988 (NAVD 88)'):
        return dict(attributes=dict(OBJECTID=key,LowPS=resolution,AcquisitionDate=date,VerticalDatum=datum))

    def test_fine_export_cannot_fall_back_to_coarse_source(self):
        result=fine_source_selection([self.row(1,10.),self.row(2,1.)],1)
        self.assertEqual([r['OBJECTID'] for r in result],[2])

    def test_only_coarse_or_unknown_resolution_refused(self):
        for resolution in (10.,None,float('nan'),0.,-1.):
            with self.assertRaisesRegex(ValueError,'No native'):
                fine_source_selection([self.row(1,resolution)],1)

    def test_explicit_absence_requires_known_coarse_or_empty_catalogue(self):
        self.assertEqual(fine_source_selection([],1,True),[])
        self.assertEqual(fine_source_selection([self.row(1,10.)],1,True),[])
        for resolution in (None,float('nan'),float('inf'),0.,-1.):
            with self.assertRaisesRegex(ValueError,'Unknown source resolution'):
                fine_source_selection([self.row(1,resolution)],1,True)
        with self.assertRaisesRegex(ValueError,'datum'):
            fine_source_selection([self.row(1,1.,datum='ellipsoidal')],1,True)

    def test_absent_catalogue_does_not_request_an_unlocked_export(self):
        import json
        import tempfile
        from pathlib import Path
        from unittest.mock import patch
        from fetch_colorado_terrain_windows import capture
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);windows=root/'windows';windows.mkdir()
            (windows/'index.json').write_text(json.dumps(dict(windows=[dict(name='one',bounds_epsg6404=[0,0,10,10])])))
            (windows/'one.json').write_text(json.dumps(dict(name='one')))
            service=dict(bandCount=1,pixelType='F32',copyrightText='test',spatialReference=dict(wkid=6404))
            catalogue=dict(features=[self.row(1,10.)])
            responses=[json.dumps(v).encode() for v in (service,catalogue)]
            with patch('fetch_colorado_terrain_windows.read',side_effect=responses) as reader:
                manifest=capture(windows,root/'capture',['one'],'3dep',1,True,True)
            self.assertEqual(reader.call_count,2)
            self.assertTrue(all('exportImage' not in call.args[0] for call in reader.call_args_list))
            row=manifest['windows'][0]
            self.assertIsNone(row['file']);self.assertEqual(row['locked_native_sources'],[])
            self.assertFalse(list((root/'capture').glob('*.tif')))
            self.assertTrue(row['native_coverage_absent'])

    def test_unreviewed_datum_refused(self):
        with self.assertRaisesRegex(ValueError,'datum'):
            fine_source_selection([self.row(1,1.,datum='ellipsoidal')],1)

    def test_newer_catalog_acquisition_preferred(self):
        result=fine_source_selection([self.row(1,1.,100),self.row(2,1.,200)],1)
        self.assertEqual([r['OBJECTID'] for r in result],[2,1])

    def test_missing_raster_identity_refused(self):
        with self.assertRaisesRegex(ValueError,'identity'):
            fine_source_selection([self.row(None,1.)],1)


if __name__=='__main__':unittest.main()
