import unittest
import numpy as np
from review_colorado_catalog_cook import compare


class CookReviewTests(unittest.TestCase):
    def test_exact_match_reports_no_error_or_spreading(self):
        source=np.zeros((8,10),bool);source[2:6]=True
        ref=dict(classified_water=source,reference_surface=np.full(10,100.),station=np.arange(10)*2.)
        fields=dict(h=source.astype(float),eta=np.full(source.shape,100.),u=np.zeros(source.shape),v=np.zeros(source.shape))
        result=compare(ref,fields,fields,2.)
        self.assertEqual(result['wet_intersection_over_union'],1.)
        self.assertEqual(result['surface_error_abs_p95_m'],0.)
        self.assertEqual(result['extra_wet_cells_over_4m_from_source'],0)
        self.assertEqual(result['depth_change_max_m'],0.)

    def test_missing_surface_sections_remain_missing(self):
        source=np.ones((2,3),bool)
        h=np.ones((2,3));h[:,1]=0
        ref=dict(classified_water=source,reference_surface=np.full(3,100.),station=np.arange(3)*2.)
        fields=dict(h=h,eta=np.full(h.shape,100.),u=np.zeros(h.shape),v=np.zeros(h.shape))
        result=compare(ref,fields,fields,2.)
        self.assertEqual(result['surface_sections_missing'],1)
        self.assertIsNone(result['surface_error_per_station_m'][1])


if __name__=='__main__':unittest.main()
