import unittest
import numpy as np
from review_colorado_catalog_cook import compare,core_reviews


class CookReviewTests(unittest.TestCase):
    def test_joined_average_cannot_hide_bad_core(self):
        source=np.zeros((10,101),bool);source[2:8]=True
        wet=source.copy();wet[:,:10]=True
        ref=dict(classified_water=source,reference_surface=np.full(101,100.),
                 station=np.arange(101)*2.,source_station=np.arange(101)*2.)
        f=dict(h=wet.astype(float),eta=np.full(wet.shape,100.),u=wet.astype(float),v=np.zeros(wet.shape))
        self.assertGreater(compare(ref,f,f,2.)['wet_intersection_over_union'],.9)
        cores=core_reviews(ref,f,f,np.full(102,20.),20.,2.,[(0,20),(20,200)])
        self.assertFalse(cores[0]['construction_screen_passed'])
        self.assertTrue(cores[1]['construction_screen_passed'])

    def test_missing_registered_core_refused(self):
        with self.assertRaisesRegex(ValueError,'registered core'):
            core_reviews(dict(source_station=np.arange(10)),{},{},np.ones(11),1.,2.,[(20,30)])

    def test_partial_core_overlap_is_not_full_coverage(self):
        for interval in [(-1,5),(4,12),(-1,12),(5,5),(8,3),(0,np.inf)]:
            with self.subTest(interval=interval), self.assertRaisesRegex(ValueError,'registered core'):
                core_reviews(dict(source_station=np.arange(10)),{},{},np.ones(11),1.,2.,[interval])

    def test_invalid_source_station_axis_refused(self):
        for stations in [[0,1,1,3],[0,2,1,3],[0,np.nan,3],[],[[0,1],[2,3]]]:
            with self.subTest(stations=stations), self.assertRaisesRegex(ValueError,'registered core'):
                core_reviews(dict(source_station=np.array(stations)),{},{},np.ones(5),1.,2.,[(0,3)])

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
