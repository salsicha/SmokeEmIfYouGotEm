import unittest

import numpy as np
from rasterio.windows import Window

from extract_colorado_bed_windows import read_survey_window


class Source:
    width=4
    height=3
    def read(self, band, window, masked):
        assert window.intersection(Window(0,0,4,3))==window
        a=np.ma.array(np.full((int(window.height),int(window.width)),800.,dtype='float32'),mask=False)
        a.mask[0,0]=True
        return a


class BedWindows(unittest.TestCase):
    def test_partial_extent_preserves_unknown_and_nodata(self):
        bed,covered=read_survey_window(Source(),Window(-1,-1,6,5),True)
        self.assertEqual(covered,12)
        self.assertEqual(np.isfinite(bed).sum(),11)
        self.assertTrue(np.isnan(bed[0]).all())
        self.assertTrue(np.isnan(bed[:,0]).all())
        self.assertTrue(np.isnan(bed[1,1]))
        self.assertEqual(bed[2,2],800)

    def test_default_refuses_off_raster_read(self):
        with self.assertRaises(ValueError):
            read_survey_window(Source(),Window(-1,0,3,3))

    def test_absent_survey_is_not_fabricated(self):
        bed,covered=read_survey_window(Source(),Window(8,8,3,3),True)
        self.assertEqual(covered,0)
        self.assertTrue(np.isnan(bed).all())

    def test_bound_is_checked_before_allocation(self):
        with self.assertRaises(ValueError):
            read_survey_window(Source(),Window(0,0,10000,10000),True)


if __name__=='__main__':
    unittest.main()
