import copy
import sys
import unittest
from pathlib import Path
import numpy as np

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from liquid_region_state import partition
from prepare_liquid_reservoir import reservoir_columns, buffer_owners, classify_buffer_columns
from merge_liquid_reservoir_state import preserved_edges


class ReservoirLayoutTest(unittest.TestCase):
    def setUp(self):
        self.domain=dict(physical_cells=[4,4,4],cell_size_m=[.5,.5,.25],
            native_face_bounds_m=[[0,0],[2,2]])
        self.regions,_=partition(self.domain,(2,2))

    def test_ring_includes_corners_once_without_core_water(self):
        p=reservoir_columns(self.domain,2)
        self.assertEqual(p.shape,(16*16-8*8,2))
        self.assertEqual(len(np.unique(p,axis=0)),len(p))
        self.assertFalse(np.any(np.all((p>=0)&(p<=2),axis=1)))
        self.assertTrue(np.any(np.all(p<0,axis=1)))
        np.testing.assert_array_equal(p.min(axis=0),[-.875,-.875])
        np.testing.assert_array_equal(p.max(axis=0),[2.875,2.875])

    def test_owner_expansion_does_not_move_internal_cuts(self):
        expanded=buffer_owners(self.domain,self.regions,2)
        for old,new in zip(self.regions,expanded):
            self.assertEqual(new['core_cell_bounds_xy'],old['cell_bounds_xy'])
            for side in (0,1):
                for axis in (0,1):
                    old_edge=old['cell_bounds_xy'][side][axis]
                    if old_edge==2:self.assertEqual(new['cell_bounds_xy'][side][axis],2)
        np.testing.assert_array_equal(expanded[0]['cell_bounds_xy'],[[-2,-2],[2,2]])
        np.testing.assert_array_equal(expanded[3]['cell_bounds_xy'],[[2,2],[6,6]])

    def test_all_ring_water_has_unique_owner(self):
        expanded=buffer_owners(self.domain,self.regions,2)
        owners=classify_buffer_columns(reservoir_columns(self.domain,2),self.domain,expanded)
        np.testing.assert_array_equal(np.bincount(owners),[48,48,48,48])

    def test_reject_core_points_instead_of_double_seeding(self):
        expanded=buffer_owners(self.domain,self.regions,2)
        for p in ([[1,1]],[[0,1]],[[2,1]]):
            with self.assertRaises(ValueError):classify_buffer_columns(p,self.domain,expanded)

    def test_reject_outside_support_instead_of_clamping(self):
        expanded=buffer_owners(self.domain,self.regions,2)
        with self.assertRaises(ValueError):classify_buffer_columns([[-1.01,1]],self.domain,expanded)

    def test_reject_overlapping_owner_boxes(self):
        expanded=buffer_owners(self.domain,self.regions,2)
        expanded.append(copy.deepcopy(expanded[0]))
        with self.assertRaises(ValueError):classify_buffer_columns([[-.5,.5]],self.domain,expanded)

    def test_reject_missing_core_owner_before_expansion(self):
        with self.assertRaises(ValueError):buffer_owners(self.domain,self.regions[:-1],2)

    def test_reject_insufficient_or_unbounded_layers(self):
        for n in (0,1,17,True,2.5):
            with self.assertRaises(ValueError):reservoir_columns(self.domain,n)

    def test_reject_bad_metrics(self):
        d=copy.deepcopy(self.domain);d['cell_size_m'][0]=.51
        with self.assertRaises(ValueError):reservoir_columns(d,2)

    def test_existing_voxel_cap_applies_to_expanded_not_core_size(self):
        d=dict(physical_cells=[128,64,24],cell_size_m=[.5,.5,1/3],native_face_bounds_m=[[0,0],[64,32]])
        r,_=partition(d)
        buffer_owners(d,r,2)
        with self.assertRaises(ValueError):buffer_owners(d,r,16)

    def test_translation_and_anisotropic_spacing(self):
        d=dict(physical_cells=[4,4,4],cell_size_m=[1,2,.25],native_face_bounds_m=[[-10,8],[-6,16]])
        r,_=partition(d,(2,2));p=reservoir_columns(d,2)
        o=classify_buffer_columns(p,d,buffer_owners(d,r,2))
        np.testing.assert_array_equal(np.bincount(o),[48,48,48,48])

    def test_explicit_expanded_partition_preserves_world_cuts(self):
        edges=preserved_edges(self.regions,2,[8,8,4])
        self.assertEqual(edges,[[0,4,8],[0,4,8]])
        outer=dict(physical_cells=[8,8,4],cell_size_m=[.5,.5,.25],native_face_bounds_m=[[-1,-1],[3,3]])
        regions,interfaces=partition(outer,(2,2),cell_edges=edges)
        self.assertEqual(len(regions),4);self.assertEqual(len(interfaces),4)
        self.assertEqual(regions[0]['bounds_station_lateral_m'][1],[1,1])

    def test_explicit_partition_rejects_holes_and_bad_spans(self):
        for edges in ([[1,2,4],[0,2,4]],[[0,2,5],[0,2,4]],[[0,1,4],[0,2,4]],
                      [[0,2.5,4],[0,2,4]],[[0,2,4]],[[0,2,4],[0,3,4]]):
            with self.assertRaises(ValueError):partition(self.domain,cell_edges=edges)
