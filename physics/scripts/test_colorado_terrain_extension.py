import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np
import rasterio
from rasterio.transform import from_origin
from extend_colorado_continuous_terrain import (
    sample_raster,profile_conversion,CapturedPadding,fill_unowned,validate_additive_manifest,run,select_extension_chunks)
from export_colorado_continuous_terrain import encode_height,write_png_u16,sha,LandscapeTriangles


class TerrainExtensionTests(unittest.TestCase):
    def test_partial_acquisition_never_becomes_full_coverage(self):
        review={'missing_chunk_indices':[[0,0],[0,1],[0,2]]}
        launch={'existing_full_extent_tiles':[[0,0]]}
        receipt=dict(captures_complete=False,errors=[{'error':'502'}],expected_windows=2,
            completed_windows=[dict(needed_chunks=[[0,1]])])
        with self.assertRaisesRegex(ValueError,'Incomplete'):select_extension_chunks(review,launch,receipt)
        selected,pending=select_extension_chunks(review,launch,receipt,True)
        self.assertEqual(selected,[[0,0],[0,1]]);self.assertEqual(pending[0]['chunk'],[0,2])

    def test_real_additive_export_keeps_original_bytes_and_shared_edges(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);base=root/'base';evidence=root/'evidence';dem=root/'dem';job=root/'job'
            for path in (base,evidence,dem,job):path.mkdir()
            profile=root/'profile.json'
            profile.write_text(json.dumps(dict(schema='raftsim.colorado_continuous_source_window.v1',
                source_core_interval_m=[0,400],source_halo_interval_m=[0,400],samples=[dict(
                    easting=0.,northing=y,local_arc_station_m=y,geoid18_value=-20.,ws_nonincreasing=880.) for y in (0.,400.)])))
            np.savez_compressed(evidence/'evidence_grid.npz',bed_ellipsoid_m=np.full((400,400),900.),
                station_m=np.broadcast_to((400-np.arange(400))[:,None],(400,400)).astype(float),
                corner_east_north_m=[0.,400.],cell_m=[1.,1.])
            for name,value in (('terrain.tif',920.),('resolution.tif',1.)):
                with rasterio.open(dem/name,'w',driver='GTiff',width=600,height=600,count=1,dtype='float32',
                        crs='EPSG:6404',transform=from_origin(0,600,1,1)) as dst:dst.write(np.full((600,600),value,dtype='float32'),1)
            (dem/'manifest.json').write_text(json.dumps(dict(
                source_service='https://elevation.nationalmap.gov/arcgis/rest/services/3DEPElevation/ImageServer',
                vertical_reference='NAVD88 orthometric metres (CONUS 3DEP)',windows=[dict(
                    file='terrain.tif',sha256=sha(dem/'terrain.tif'),bounds_epsg6404=[0,0,600,600],
                    source_resolution_mask=dict(file='resolution.tif',sha256=sha(dem/'resolution.tif')))])))
            (evidence/'manifest.json').write_text(json.dumps(dict(horizontal_crs='EPSG:6404',
                vertical_datum='NAD83(2011) ellipsoid',evidence_grid_sha256=sha(evidence/'evidence_grid.npz'),
                source_files_sha256={'profile.json':sha(profile),'dem/terrain.tif':sha(dem/'terrain.tif')})))
            write_png_u16(base/'height_0_0.png',encode_height(np.full((127,127),900.)))
            manifest=dict(schema='raftsim.colorado_continuous_landscape.v1',route_coordinate_map='route',route_sha256='r',
                horizontal_origin_epsg6404_m=[0.,0.],vertical_datum_m=200.,landscape=dict(vertices=127,
                    spacing_m=2.,span_m=252.,height_base_ellipsoid_m=200.,height_range_m=2400.),
                source_inputs=[dict(evidence='evidence',evidence_manifest_sha256=sha(evidence/'manifest.json'),
                    profile='profile.json',profile_sha256=sha(profile))],
                chunks=[dict(chunk=[0,0],heightfield='height_0_0.png',sha256=sha(base/'height_0_0.png'),origin_epsg6404_m=[0.,252.])],
                incomplete_source_chunks=[dict(chunk=[0,1],missing_vertices=1)])
            (base/'manifest.json').write_text(json.dumps(manifest))
            review=root/'review.json';review.write_text(json.dumps(dict(missing_chunk_indices=[[0,1]])))
            (job/'launch.json').write_text(json.dumps(dict(files_sha256={'base/manifest.json':sha(base/'manifest.json'),'review.json':sha(review)})))
            (job/'completion.json').write_text(json.dumps(dict(captures_complete=True,errors=[],completed_windows=[],expected_windows=0)))
            original=(base/'height_0_0.png').read_bytes()
            with patch('extend_colorado_continuous_terrain.ROOT',root),patch('export_colorado_continuous_terrain.ROOT',root),\
                 patch('extend_colorado_continuous_terrain.shutil.disk_usage',return_value=type('Disk',(),{'free':100*1024**3})()):
                receipt=run(base,review,job,root/'extended')
            self.assertEqual(receipt['added_chunks'],1);self.assertEqual(receipt['rejected_chunks'],[])
            self.assertEqual(original,(root/'extended/height_0_0.png').read_bytes())
            self.assertEqual(original,(base/'height_0_0.png').read_bytes())
            terrain=LandscapeTriangles(root/'extended')
            self.assertTrue(np.isfinite(terrain.sample(np.array([[20.,300.],[20.,500.]]))).all())

    def test_raster_sample_is_bilinear_bounded_and_preserves_nodata(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'dem.tif';values=200.+np.arange(4)[None,:]+10*np.arange(4)[:,None]
            values[3,3]=-9999.
            with rasterio.open(path,'w',driver='GTiff',width=4,height=4,count=1,dtype='float64',
                    crs='EPSG:6404',transform=from_origin(0,4,1,1),nodata=-9999.) as dst:dst.write(values,1)
            actual=sample_raster(path,np.array([[.5,3.5],[1.,3.],[0.,4.],[-.001,3.],[3.5,.5]]))
            np.testing.assert_array_equal(actual[:3],[200.,205.5,200.])
            self.assertTrue(np.isnan(actual[3:]).all())
            self.assertEqual(sample_raster(path,np.empty((0,2))).shape,(0,))
            with self.assertRaises(ValueError):sample_raster(path,np.array([[np.nan,1.]]))

    def profile(self,y,geoid):
        return dict(line=np.array([[0.,y],[10.,y]]),station=np.array([0.,10.]),
                    geoid=np.array([geoid,geoid+2.]),stage=np.array([100.,99.]))

    def test_conversion_uses_nearest_actual_segment_and_interpolated_geoid(self):
        profiles=[self.profile(0.,-20.),self.profile(100.,-30.)]
        geoid,stage=profile_conversion(np.array([[5.,1.],[5.,99.],[2000.,0.]]),profiles)
        np.testing.assert_array_equal(geoid[:2],[-19.,-29.])
        np.testing.assert_array_equal(stage[:2],[99.5,99.5])
        self.assertTrue(np.isnan(geoid[-1]) and np.isnan(stage[-1]))

    def test_padding_never_overwrites_source_bed_or_inferred_shore(self):
        class Padding:
            def sample(self,points):
                np.testing.assert_array_equal(points,[[2.,0.]])
                return np.array([115.]),np.array([10.]),np.array([100.])
        z=np.array([[80.,102.,np.nan]]);owner=np.array([[0,3,-1]])
        points=np.array([[[0.,0.],[1.,0.],[2.,0.]]])
        result,stats=fill_unowned(z,owner,points,Padding())
        np.testing.assert_array_equal(result,[[80.,102.,115.]])
        self.assertTrue(np.isnan(z[0,2]));self.assertEqual(stats['resolution_counts'],{'10':1})
        result,stats=fill_unowned(z[:,:2],owner[:,:2],points[:,:2],None)
        self.assertEqual(stats['added_vertices'],0)

    def test_padding_rejects_low_or_unknown_dem_without_raising_it(self):
        for value,resolution,stage in ((100.9,1.,100.),(np.nan,1.,100.),(120.,1.,np.nan),(120.,3.,100.)):
            class Padding:
                def sample(self,points):return np.array([value]),np.array([resolution]),np.array([stage])
            with self.assertRaises(ValueError):
                fill_unowned(np.array([np.nan]),np.array([-1]),np.array([[0.,0.]]),Padding())

    def manifest(self):
        return dict(schema='test',route_coordinate_map='route',route_sha256='r',
            horizontal_origin_epsg6404_m=[0.,0.],vertical_datum_m=200.,landscape={'spacing_m':2},
            source_inputs=[{'source':'a'}],chunks=[{'chunk':[0,0],'sha256':'one','heightfield':'a.png'}])

    def test_additive_contract_rejects_removed_replaced_shifted_or_duplicate_tiles(self):
        base=self.manifest();extension=copy.deepcopy(base)
        extension['chunks'].append(dict(chunk=[0,1],sha256='two',heightfield='b.png'))
        extension['additive_terrain_extension']={'base_manifest_sha256':'hash'}
        validate_additive_manifest(base,extension,'hash')
        for mutation in ('replace','remove','duplicate','frame','sources','hash','noaddition'):
            changed=copy.deepcopy(extension)
            if mutation=='replace':changed['chunks'][0]['sha256']='bad'
            elif mutation=='remove':changed['chunks'].pop(0)
            elif mutation=='duplicate':changed['chunks'].append(changed['chunks'][0])
            elif mutation=='frame':changed['landscape']['spacing_m']=4
            elif mutation=='sources':changed['source_inputs']=[]
            elif mutation=='hash':changed['additive_terrain_extension']['base_manifest_sha256']='bad'
            else:changed['chunks'].pop()
            with self.assertRaises(ValueError):validate_additive_manifest(base,changed,'hash')


if __name__=='__main__':unittest.main()
