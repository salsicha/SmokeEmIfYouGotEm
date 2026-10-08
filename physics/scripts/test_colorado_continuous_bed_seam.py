import unittest
import numpy as np
from review_colorado_continuous_bed_seam import compare,screen


class BedSeam(unittest.TestCase):
    def tile(self,x,local_origin):
        xx=np.tile(np.arange(x,x+10),(4,1)).astype(float)
        return dict(corner_east_north_m=np.array([x,4.]),cell_m=np.array([1.,1.]),
            bed_ellipsoid_m=800-xx,reference_surface_ellipsoid_m=810-xx,
            station_m=xx-local_origin,classified_water_mask=np.ones(xx.shape,bool),
            measured_pool_bed_mask=np.zeros(xx.shape,bool))

    def test_different_local_stations_match_at_same_world_cells(self):
        result=compare(self.tile(0,0),self.tile(5,5),0,5,7,2)
        self.assertEqual(result['bed_difference']['maximum_m'],0)
        self.assertEqual(result['shared_wet_cells'],20)
        self.assertTrue(screen(result))

    def test_real_height_error_not_hidden_by_source_identity(self):
        b=self.tile(5,5);b['bed_ellipsoid_m']+=.5
        result=compare(self.tile(0,0),b,0,5,7,2)
        self.assertEqual(result['bed_difference']['maximum_m'],.5)
        self.assertFalse(screen(result))

    def test_reference_jump_rejected_even_when_bed_matches(self):
        b=self.tile(5,5);b['reference_surface_ellipsoid_m']+=.5
        result=compare(self.tile(0,0),b,0,5,7,2)
        self.assertEqual(result['bed_difference']['maximum_m'],0)
        self.assertFalse(screen(result))

    def test_empty_nonfinite_and_changed_shoreline_rejected(self):
        import copy
        result=compare(self.tile(0,0),self.tile(5,5),0,5,7,2)
        for key in ('bed_difference','reference_surface_difference'):
            for value in (float('nan'),float('inf'),-.1):
                changed=copy.deepcopy(result);changed[key]['maximum_m']=value
                self.assertFalse(screen(changed))
        for key,value in (('shared_wet_cells',0),('shoreline_disagreement_cells',1)):
            changed=copy.deepcopy(result);changed[key]=value
            self.assertFalse(screen(changed))

    def test_missing_overlap_and_shifted_lattice_refused(self):
        for x in (10,.5):
            with self.assertRaises(ValueError):
                compare(self.tile(0,0),self.tile(x,x),0,x,7,2)


if __name__=='__main__':unittest.main()
