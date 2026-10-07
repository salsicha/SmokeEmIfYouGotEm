import unittest
import numpy as np
from condition_chilko_terrain_seams import condition
from audit_chilko_corridor_terrain import check_tile


class TerrainSeamTests(unittest.TestCase):
    def grids(self):
        x,y=np.meshgrid(np.arange(50),np.arange(30))
        coarse=(100+.1*x+.05*y).astype(np.float32)
        kind=np.where(x<25,2,1).astype(np.uint8)
        height=np.where(kind==1,coarse+7,coarse).astype(np.float32)
        return height,kind,coarse

    def test_native_preserved_and_coarse_boundary_step_removed(self):
        h,k,c=self.grids();original=h.copy()
        out,kind,delta=condition(h,k,c,20)
        np.testing.assert_array_equal(out[k==1],h[k==1])
        np.testing.assert_array_equal(h,original)
        np.testing.assert_array_equal(out[:,:6],h[:,:6])
        self.assertLess(float(np.max(out[:,25]-out[:,24])),.16)
        self.assertTrue((kind[:,6:25]==3).all());self.assertTrue((delta[k==1]==0).all())
        self.assertLess(float(np.max(abs(np.diff(out,axis=1)))), .63)

    def test_missing_pixels_not_filled(self):
        h,k,c=self.grids();h[10,24]=np.nan;k[10,24]=0
        out,kind,d=condition(h,k,c,20)
        self.assertTrue(np.isnan(out[10,24]));self.assertEqual(kind[10,24],0);self.assertEqual(d[10,24],0)

    def test_tile_halo_equals_whole_domain(self):
        h,k,c=self.grids();whole=condition(h,k,c,8)
        # The tested inner region has >radius support in every direction.
        local=condition(h[1:29,10:40],k[1:29,10:40],c[1:29,10:40],8)
        for a,b in zip(whole,local):
            np.testing.assert_array_equal(a[10:20,20:30],b[9:19,10:20])

    def test_no_boundary_is_unchanged_and_bad_overlap_refused(self):
        h,k,c=self.grids();k[:]=2
        out,kind,d=condition(h,k,c,20)
        np.testing.assert_array_equal(out,h);np.testing.assert_array_equal(kind,k);self.assertFalse(d.any())
        h,k,c=self.grids();c[:,25]=np.nan
        with self.assertRaisesRegex(ValueError,'overlap'):condition(h,k,c,20)
        h,k,c=self.grids()
        with self.assertRaisesRegex(ValueError,'limit'):condition(h,k,c,20,2)
        for radius in (0,np.nan,513):
            with self.assertRaises(ValueError):condition(h,k,c,radius)

    def test_audit_checks_actual_native_pixels_and_correction(self):
        h,k,c=self.grids();out,kind,d=condition(h,k,c,20)
        source=dict(height_m=h,source_kind=k,native_crop_owner=(k==1).astype(np.uint16))
        result=dict(source,height_m=out,source_kind=kind,seam_correction_m=d)
        self.assertEqual(check_tile(source,result),(750,570))
        result['height_m']=out.copy();result['height_m'][0,30]+=1
        with self.assertRaisesRegex(ValueError,'outside'):check_tile(source,result)
        result['height_m']=out.copy();result['height_m'][0,24]+=1
        with self.assertRaisesRegex(ValueError,'correction'):check_tile(source,result)
        result['height_m']=out;result['native_crop_owner']=np.zeros_like(source['native_crop_owner'])
        with self.assertRaisesRegex(ValueError,'provenance'):check_tile(source,result)


if __name__=='__main__':unittest.main()
