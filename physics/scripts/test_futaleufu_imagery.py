import copy
import hashlib
from pathlib import Path
import tempfile
import unittest

import numpy as np
from futaleufu_imagery import grid, sampling_points, load_reflectance, require_sample_support, sample_cover, BANDS


class ImageryTests(unittest.TestCase):
    def item(self):
        band=dict(x0=733140.,y0=5215170.,cell_m=10.,shape=[4,5],
                  raster_bands=[dict(scale=.0001,offset=-.1,nodata=0)])
        return dict(epsg=32718,bands={k:copy.deepcopy(band) for k in BANDS},
                    window_utm_m=dict(xmin=733144.4082054063,ymax=5215168.964582899))

    def test_actual_pixel_centres_ignore_requested_rectangle(self):
        item=self.item()
        r,c=sampling_points(np.array([[733145.,733175.]]),np.array([[5215165.],[5215145.]]),item)
        np.testing.assert_array_equal(r,[[0,0],[2,2]])
        np.testing.assert_array_equal(c,[[0,3],[0,3]])
        item['window_utm_m']=dict(xmin=-1e9,ymax=1e9)
        rr,cc=sampling_points(np.array([[733145.,733175.]]),np.array([[5215165.],[5215145.]]),item)
        np.testing.assert_array_equal(r,rr);np.testing.assert_array_equal(c,cc)

    def test_cover_uses_native_grid_not_requested_rectangle(self):
        item=self.item();cover=np.zeros((4,5),bool);cover[1,1]=True;valid=np.ones_like(cover)
        east=np.array([733152.5,733160.5]);north=5215159.5
        np.testing.assert_array_equal(sample_cover(cover,valid,east,north,item),[True,False])
        # Former formula assigned the first position to the adjacent west pixel.
        old_col=((east-item['window_utm_m']['xmin'])/10).astype(int)
        self.assertEqual(old_col[0],0)
        shifted=item.copy();shifted['window_utm_m']=dict(xmin=0,ymax=0)
        np.testing.assert_array_equal(sample_cover(cover,valid,east,north,shifted),[True,False])

    def test_cover_refuses_missing_or_misaligned_evidence(self):
        item=self.item();cover=np.ones((4,5),bool);valid=cover.copy();valid[0,0]=False
        with self.assertRaises(ValueError):sample_cover(cover,valid,733145.,5215165.,item)
        with self.assertRaises(ValueError):sample_cover(cover,np.ones_like(cover),733144.,5215165.,item)
        with self.assertRaises(ValueError):sample_cover(cover.astype(float),np.ones_like(cover),733145.,5215165.,item)

    def test_outside_and_nonfinite_never_clamp(self):
        for e,n in ((733144.,5215165.),(733186.,5215165.),(733145.,5215166.),
                    (733145.,5215134.),(float('nan'),5215165.)):
            with self.assertRaises(ValueError):sampling_points(e,n,self.item())

    def test_grid_frame_alignment_and_encoding_required(self):
        for key,value in [('x0',733141),('shape',[4,6]),('cell_m',20),
                          ('raster_bands',[dict(scale=.0001,offset=0,nodata=0)])]:
            item=self.item();item['bands']['red'][key]=value
            with self.assertRaises(ValueError):grid(item)
        item=self.item();item['epsg']=32618
        with self.assertRaises(ValueError):grid(item)

    def test_nodata_neighbour_refused_and_edge_supported(self):
        valid=np.ones((4,5),bool)
        require_sample_support(valid,np.array([3.]),np.array([4.]))
        valid[2,3]=False
        with self.assertRaises(ValueError):require_sample_support(valid,np.array([1.5]),np.array([2.5]))

    def test_loaded_bytes_shape_and_radiometry_verified(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'mosaic.npz';item=self.item()
            arrays={k:np.full((4,5),2500,dtype=np.uint16) for k in BANDS}
            arrays['nir'][2,3]=0
            np.savez_compressed(path,**arrays)
            item.update(npz=path.name,npz_sha256=hashlib.sha256(path.read_bytes()).hexdigest())
            refl,valid=load_reflectance(Path(td),item)
            self.assertAlmostEqual(float(refl['blue'][0,0]),.15,places=6)
            self.assertFalse(valid[2,3]);self.assertEqual(int(valid.sum()),19)
            item['npz_sha256']='0'*64
            with self.assertRaises(ValueError):load_reflectance(Path(td),item)

    def test_wrong_array_shape_and_dtype_refused(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'mosaic.npz';item=self.item()
            for wrong in (np.ones((4,6),dtype=np.uint16),np.ones((4,5),dtype=np.float32)):
                arrays={k:np.full((4,5),2500,dtype=np.uint16) for k in BANDS}
                arrays['red']=wrong
                np.savez_compressed(path,**arrays)
                item.update(npz=path.name,npz_sha256=hashlib.sha256(path.read_bytes()).hexdigest())
                with self.assertRaises(ValueError):load_reflectance(Path(td),item)


if __name__=='__main__':unittest.main()
