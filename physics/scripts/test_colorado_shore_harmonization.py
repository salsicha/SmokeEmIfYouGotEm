import copy
import unittest
import numpy as np
from harmonize_colorado_shore_sources import unchanged_water_and_ground


class ShoreHarmonization(unittest.TestCase):
    def fixture(self):
        before=dict(bed_ellipsoid_m=np.array([[900.,901.,902.,903.]]),
            inferred_shore_stabilization_mask=np.array([[False,False,False,True]]),
            classified_water_mask=np.array([[True,True,False,False]]),
            measured_pool_bed_mask=np.array([[True,False,False,False]]),
            class_code=np.array([[1,2,0,3]]),station_m=np.array([[0.,1.,2.,3.]]))
        after=copy.deepcopy(before)
        after['bed_ellipsoid_m'][0,2:]+=[.5,.85]
        after['class_code'][0,2]=3
        after['inferred_shore_stabilization_mask'][0,2]=True
        return before,after

    def test_bounded_dry_change_preserves_all_source_fields(self):
        a,b=self.fixture();result=unchanged_water_and_ground(a,b,.15)
        self.assertEqual(result['changed_inferred_dry_cells'],2)
        self.assertTrue(result['classified_water_and_measured_bed_identical'])

    def test_wet_or_measured_bed_cannot_change(self):
        for col in (0,1):
            a,b=self.fixture();b['bed_ellipsoid_m'][0,col]+=.1
            with self.assertRaises(ValueError):unchanged_water_and_ground(a,b,.15)

    def test_source_mask_coordinates_and_unbounded_changes_refused(self):
        for field in ('classified_water_mask','station_m','measured_pool_bed_mask'):
            a,b=self.fixture();b[field][0,0]=0 if field!='station_m' else 9
            with self.assertRaises(ValueError):unchanged_water_and_ground(a,b,.15)
        for value in (-.1,.86,float('nan')):
            a,b=self.fixture();b['bed_ellipsoid_m'][0,2]=a['bed_ellipsoid_m'][0,2]+value
            with self.assertRaises(ValueError):unchanged_water_and_ground(a,b,.15)

    def test_dry_classes_and_removed_ownership_refused(self):
        a,b=self.fixture();b['class_code'][0,0]=2
        with self.assertRaises(ValueError):unchanged_water_and_ground(a,b,.15)
        a,b=self.fixture();b['inferred_shore_stabilization_mask'][0,3]=False
        with self.assertRaises(ValueError):unchanged_water_and_ground(a,b,.15)


if __name__=='__main__':unittest.main()
