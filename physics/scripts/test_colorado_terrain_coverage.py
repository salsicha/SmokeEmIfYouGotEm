import unittest
import numpy as np
from blend_colorado_terrain_coverage import combine,blend,verify_catalog_absence
from fetch_colorado_terrain_windows import nominal_resolution_matches,fine_source_selection


class CoverageTests(unittest.TestCase):
    def test_catalogue_roundoff_is_not_a_different_native_resolution(self):
        for value in (1,1.,0.9999999999999971,1.000000000000003):
            self.assertTrue(nominal_resolution_matches(value,1))
            source=dict(LowPS=value,OBJECTID=64838,VerticalDatum='NAVD88')
            self.assertEqual(fine_source_selection([dict(attributes=source)],1),[source])
            self.assertEqual(source['LowPS'],value)
        for value in (None,True,'1',0,-1,float('nan'),float('inf'),.99,1.000001,2,10):
            self.assertFalse(nominal_resolution_matches(value,1))
        with self.assertRaises(ValueError):
            fine_source_selection([dict(attributes=dict(LowPS=1.000001,OBJECTID=1,VerticalDatum='NAVD88'))],1)

    def test_valid_fine_values_preserved_and_fallback_labelled(self):
        a=np.array([[900.,0.,np.nan,901.]])
        values,resolution=combine(a,[[True,True,True,False]],np.array([[800.,810.,820.,830.]]),10)
        np.testing.assert_array_equal(values,[[900.,810.,820.,830.]])
        np.testing.assert_array_equal(resolution,[[1.,10.,10.,10.]])
        self.assertEqual(a[0,1],0.)

    def test_missing_fallback_cannot_fill_a_gap(self):
        for value in (0.,np.nan):
            with self.assertRaises(ValueError):combine([[0.]],[[True]],[[value]],10)

    def test_missing_fallback_does_not_replace_valid_fine_source(self):
        values,resolution=combine([[900.]],[[True]],[[np.nan]],10)
        self.assertEqual(values[0,0],900.)
        self.assertEqual(resolution[0,0],1.)

    def test_absent_fine_coverage_uses_only_labelled_coarse_data(self):
        values,resolution=combine([[0.,np.nan]],[[True,False]],[[800.,810.]],10)
        np.testing.assert_array_equal(values,[[800.,810.]])
        np.testing.assert_array_equal(resolution,[[10.,10.]])

    def test_different_grids_refused(self):
        with self.assertRaisesRegex(ValueError,'grids'):combine([[900.]],[[True]],[[900.,901.]],10)

    def absent_fixture(self,root,catalogue=None):
        import json
        from build_colorado_catalog_evidence import sha
        fine=root/'fine';coarse=root/'coarse';fine.mkdir();coarse.mkdir()
        catalog=fine/'source.json'
        catalog.write_text(json.dumps(catalogue if catalogue is not None else
                                      dict(features=[dict(attributes=dict(LowPS=10))])))
        row=dict(name='one',cell_m=1,file=None,url=None,sha256=None,response_sha256=None,bytes=0,
                 valid_pixel_coverage_verified=False,valid_native_pixels=0,missing_native_pixels=400,
                 partial_fine_capture=True,native_coverage_absent=True,locked_native_sources=[],
                 source_absence_reason='complete_catalog_has_no_native_fine_source',
                 bounds_epsg6404=[0,0,20,20],shape=[20,20],
                 source_catalog=dict(file='source.json',sha256=sha(catalog)))
        return fine,coarse,row

    def test_absent_raster_blends_only_verified_coarse_pixels(self):
        import json
        import tempfile
        from pathlib import Path
        import rasterio
        from rasterio.transform import from_origin
        from build_colorado_catalog_evidence import sha
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);fine,coarse,row=self.absent_fixture(root)
            p=coarse/'one.tif'
            with rasterio.open(p,'w',driver='GTiff',width=2,height=2,count=1,dtype='float32',
                               crs='EPSG:6404',transform=from_origin(0,20,10,10),nodata=-99999.) as target:
                target.write(np.full((2,2),900.,dtype='float32'),1)
            header=dict(source_service='https://elevation.nationalmap.gov/arcgis/rest/services/3DEPElevation/ImageServer',
                        vertical_reference='NAVD88 orthometric metres (CONUS 3DEP)',source_credit='test',rights_scope='test')
            source_hash=sha(p)
            (fine/'manifest.json').write_text(json.dumps(dict(header,windows=[row])))
            coarse_row=dict(name='one',file='one.tif',sha256=source_hash,cell_m=10,bounds_epsg6404=[0,0,20,20])
            (coarse/'manifest.json').write_text(json.dumps(dict(header,windows=[coarse_row])))
            result=blend(fine,coarse,root/'mixed')['windows'][0]
            self.assertEqual(result['native_fine_cells'],0);self.assertEqual(result['coarse_fallback_cells'],400)
            self.assertTrue(result['native_source_catalog_absent'])
            with rasterio.open(root/'mixed/one.tif') as src:
                np.testing.assert_array_equal(src.read(1),np.full((20,20),900.))
            with rasterio.open(root/'mixed'/result['source_resolution_mask']['file']) as src:
                np.testing.assert_array_equal(src.read(1),np.full((20,20),10.))
            self.assertEqual(sha(p),source_hash)

    def test_absence_rejects_fine_incomplete_unknown_or_changed_catalogue(self):
        import tempfile
        from pathlib import Path
        cases=[dict(features=[],exceededTransferLimit=True),
               dict(features=[dict(attributes=dict(LowPS=1,OBJECTID=1,VerticalDatum='NAVD88'))]),
               dict(features=[dict(attributes=dict(LowPS=None))])]
        for catalogue in cases:
            with tempfile.TemporaryDirectory() as temporary:
                fine,_,row=self.absent_fixture(Path(temporary),catalogue)
                with self.assertRaises(ValueError):verify_catalog_absence(fine,row)
        with tempfile.TemporaryDirectory() as temporary:
            fine,_,row=self.absent_fixture(Path(temporary))
            row['source_catalog']['sha256']='not-the-source'
            with self.assertRaisesRegex(ValueError,'Changed'):verify_catalog_absence(fine,row)

    def test_locked_fine_raster_path_still_preserves_valid_pixels(self):
        import json
        import tempfile
        from pathlib import Path
        import rasterio
        from rasterio.transform import from_origin
        from build_colorado_catalog_evidence import sha
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);fine=root/'fine';coarse=root/'coarse';fine.mkdir();coarse.mkdir()
            header=dict(source_service='https://elevation.nationalmap.gov/arcgis/rest/services/3DEPElevation/ImageServer',
                        vertical_reference='NAVD88 orthometric metres (CONUS 3DEP)',source_credit='test',rights_scope='test')
            for folder,spacing in ((fine,1),(coarse,10)):
                width=20//spacing;a=np.full((width,width),900.,dtype='float32')
                if spacing==1:a[:10,:]=901.;a[10:,:]=-99999.
                p=folder/'one.tif'
                with rasterio.open(p,'w',driver='GTiff',width=width,height=width,count=1,dtype='float32',
                                   crs='EPSG:6404',transform=from_origin(0,20,spacing,spacing),nodata=-99999.) as target:
                    target.write(a,1)
                row=dict(name='one',file='one.tif',sha256=sha(p),cell_m=spacing,shape=[width,width],
                         bounds_epsg6404=[0,0,20,20],source_catalog=None,
                         locked_native_sources=[dict(LowPS=0.9999999999999971,OBJECTID=64838)])
                (folder/'manifest.json').write_text(json.dumps(dict(header,windows=[row])))
            result=blend(fine,coarse,root/'mixed')['windows'][0]
            self.assertEqual(result['native_fine_cells'],200);self.assertEqual(result['coarse_fallback_cells'],200)
            self.assertFalse(result['native_source_catalog_absent'])
            with rasterio.open(root/'mixed/one.tif') as src:
                values=src.read(1)
            self.assertTrue(np.all(values[:10,:]==901.));self.assertTrue(np.all(values[10:,:]==900.))


if __name__=='__main__':unittest.main()
