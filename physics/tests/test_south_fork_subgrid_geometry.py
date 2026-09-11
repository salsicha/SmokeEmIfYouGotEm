from pathlib import Path
import sys
import unittest
import numpy as np

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from audit_south_fork_subgrid_geometry import capacity


class SubgridCapacityTests(unittest.TestCase):
    def test_planar_wet_bed_preserves_storage(self):
        coarse=np.array([[1.,2.],[3.,4.]])
        fine=np.repeat(np.repeat(coarse,2,axis=0),2,axis=1)
        result=capacity(coarse,fine,2,5.,np.ones((2,2),dtype=bool),2.,3.)
        self.assertEqual(result['coarse_storage_m3'],60.)
        self.assertEqual(result['fine_sampled_storage_m3'],60.)
        self.assertEqual(result['maximum_absolute_section_area_difference_m2'],0.)
        self.assertEqual(result['coarse_wet_area_m2'],24.)

    def test_subgrid_rock_not_erased_by_averaging_bed_before_depth(self):
        # Mean fine bed equals coarse bed, yet the dry rock clips negative
        # water depths: averaging bed first would incorrectly hide this change.
        coarse=np.array([[1.]])
        fine=np.array([[0.,0.],[0.,4.]])
        result=capacity(coarse,fine,2,2.,np.ones((1,1),dtype=bool),1.,1.)
        self.assertEqual(result['coarse_storage_m3'],1.)
        self.assertEqual(result['fine_sampled_storage_m3'],1.5)
        self.assertEqual(result['fine_sampled_wet_area_m2'],.75)
        self.assertEqual(result['coarse_cell_area_with_mixed_fine_wet_dry_m2'],1.)
        self.assertEqual(result['coarse_wet_cell_area_with_some_fine_dry_rock_m2'],1.)

    def test_coarse_dry_sample_can_miss_open_water(self):
        result=capacity(np.array([[4.]]),np.array([[0.,4.],[4.,4.]]),2,2.,np.ones((1,1),dtype=bool),1.,1.)
        self.assertEqual(result['coarse_dry_cell_area_with_some_fine_water_m2'],1.)
        self.assertEqual(result['fine_sampled_storage_m3'],.5)

    def test_mask_limits_both_area_and_section(self):
        result=capacity(np.zeros((2,2)),np.zeros((4,4)),2,2.,np.array([[True,False],[False,False]]),2.,3.)
        self.assertEqual(result['fine_sampled_storage_m3'],12.)
        self.assertEqual(result['fine_sampled_section_area_m2'],[6.,0.])

    def test_bad_inputs_rejected(self):
        for fine,stage,mask,dx in ((np.zeros((3,4)),1.,np.ones((2,2),dtype=bool),1.),
            (np.full((4,4),np.nan),1.,np.ones((2,2),dtype=bool),1.),
            (np.zeros((4,4)),float('nan'),np.ones((2,2),dtype=bool),1.),
            (np.zeros((4,4)),1.,np.zeros((2,2),dtype=bool),1.),
            (np.zeros((4,4)),1.,np.ones((2,2),dtype=bool),-1.)):
            with self.subTest(stage=stage,dx=dx):
                with self.assertRaises(ValueError):capacity(np.zeros((2,2)),fine,2,stage,mask,dx,1.)
