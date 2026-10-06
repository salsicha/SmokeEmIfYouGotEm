import unittest
import numpy as np
from build_colorado_catalog_evidence import compose, infer_depth, project


class ConstructionEvidenceTests(unittest.TestCase):
    def test_projection_is_continuous_and_left_positive(self):
        s,n,d=project([[2,3],[8,-4],[10,0]],[[0,0],[5,0],[10,0]],[0,5,10],chunk=1)
        np.testing.assert_allclose(s,[2,8,10]); np.testing.assert_allclose(n,[3,-4,0])
        np.testing.assert_allclose(d,[3,4,0])

    def test_reject_duplicate_and_unordered_centerline(self):
        for line,station in (([[0,0],[0,0]],[0,1]),([[0,0],[2,0]],[1,0])):
            with self.assertRaises(ValueError): project([[1,1]],line,station)

    def fixture(self):
        wet=np.zeros((30,40),bool);wet[10:20]=True
        bed=np.full(wet.shape,np.nan);bed[14,20]=96.
        water=dict(classified_water_mask=wet,corner_east_north_m=np.array([0,30]),cell_m=np.ones(2))
        measured=dict(elevation_ellipsoid_m=bed,measured_pool_bed_mask=np.isfinite(bed),
                      corner_east_north_m=np.array([0,30]),cell_m=np.ones(2))
        profile=dict(samples=[dict(easting=s,northing=15,local_arc_station_m=s,ws_nonincreasing=100-.005*s)
                              for s in (0,10,20,30,40)])
        return profile,water,measured,np.full(wet.shape,105.)

    def test_survey_preserved_and_inference_separate(self):
        args=self.fixture(); result,receipt=compose(*args)
        self.assertEqual(result['bed_ellipsoid_m'][14,20],96.)
        self.assertEqual(receipt['supported_survey_bed_cells'],1)
        self.assertEqual(receipt['measured_bed_max_change_m'],0.)
        self.assertGreater(receipt['inferred_wet_bed_cells'],0)
        np.testing.assert_array_equal(result['original_survey_bed_ellipsoid_m'],args[2]['elevation_ellipsoid_m'])

    def test_dem_water_is_not_bathymetry(self):
        args=self.fixture(); first,_=compose(*args)
        args[3][args[1]['classified_water_mask']]=-999.
        second,_=compose(*args)
        np.testing.assert_array_equal(first['bed_ellipsoid_m'],second['bed_ellipsoid_m'])

    def test_profile_conflict_is_retained_and_flagged(self):
        args=self.fixture(); args[2]['elevation_ellipsoid_m'][14,20]=101.
        result,receipt=compose(*args)
        self.assertEqual(receipt['source_bed_profile_conflicts'],1)
        self.assertEqual(result['original_survey_bed_ellipsoid_m'][14,20],101.)
        self.assertTrue(result['inferred_rapid_bed_mask'][14,20])

    def test_shore_modelling_not_silently_measured(self):
        args=self.fixture();args[3][9,20]=97.
        result,receipt=compose(*args)
        self.assertTrue(result['inferred_shore_stabilization_mask'][9,20])
        self.assertEqual(result['regional_terrain_ellipsoid_m'][9,20],97.)
        self.assertEqual(result['class_code'][9,20],3)

    def test_registration_mismatch_refused(self):
        args=self.fixture();args[2]['corner_east_north_m'][0]=1
        with self.assertRaises(ValueError):compose(*args)

    def test_shore_clearance_changes_only_labelled_inferred_dry_land(self):
        args=self.fixture();args[3][9,20]=97.
        baseline,_=compose(*args)
        raised,receipt=compose(*args,shore_clearance_m=1.)
        changed=raised['bed_ellipsoid_m']!=baseline['bed_ellipsoid_m']
        self.assertTrue(changed.any())
        self.assertFalse((changed & args[1]['classified_water_mask']).any())
        self.assertTrue(raised['inferred_shore_stabilization_mask'][changed].all())
        self.assertTrue((raised['class_code'][changed]==3).all())
        np.testing.assert_array_equal(raised['original_survey_bed_ellipsoid_m'],baseline['original_survey_bed_ellipsoid_m'])
        self.assertEqual(receipt['measured_bed_max_change_m'],0.)

    def test_unbounded_shore_clearance_is_refused(self):
        for clearance in (.149,2.01,float('nan'),float('inf')):
            with self.assertRaises(ValueError):compose(*self.fixture(),shore_clearance_m=clearance)


if __name__=='__main__':unittest.main()
