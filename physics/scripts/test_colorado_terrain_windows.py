import unittest
from fetch_colorado_terrain_windows import fine_source_selection,verify_colorado_pixels,fine_coverage


class FineSourceTests(unittest.TestCase):
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
