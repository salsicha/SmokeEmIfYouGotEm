"""Check source identity, visible footprint coordinates and honest coverage."""
import json
from pathlib import Path
import sys
import tempfile
import unittest

import numpy as np
import rasterio

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'physics/scripts'))
from archive_horn_creek_imagery import MAP, MAP_HASH, IMAGE_HASH, archive, native_projection, sha

SOURCE=ROOT/'physics/data/real_world/colorado_river_grand_canyon_rowing/horn_creek_sources_2026_10/imagery_2021'

class ProjectionTests(unittest.TestCase):
    def test_left_positive_north_for_eastward_chart(self):
        chart=dict(horizontal_origin_epsg6404_m=[100,200],points=[[0,0,0,0,1],[10,10,0,0,1]])
        result,error=native_projection([104,203],chart)
        np.testing.assert_allclose(result,[4,3])
        self.assertEqual(error,0)

    def test_world_y_sign_not_applied_to_geographic_xy(self):
        chart=dict(world_y_sign=-1,horizontal_origin_epsg6404_m=[100,200],points=[[0,0,0,-1,0],[10,0,10,-1,0]])
        result,error=native_projection([97,206],chart)
        np.testing.assert_allclose(result,[6,3])
        self.assertEqual(error,0)

    def test_refuse_beyond_chart_end(self):
        chart=dict(horizontal_origin_epsg6404_m=[0,0],points=[[0,0,0,0,1],[10,10,0,0,1]])
        with self.assertRaises(ValueError):native_projection([12,3],chart)

    def test_refuse_degenerate_chart(self):
        chart=dict(horizontal_origin_epsg6404_m=[0,0],points=[[0,0,0,0,1],[10,0,0,0,1]])
        with self.assertRaises(ValueError):native_projection([1,3],chart)

    def test_never_overwrite_archive(self):
        with tempfile.TemporaryDirectory() as path:
            with self.assertRaises(ValueError):archive(Path('nonexistent'),Path(path))

    def test_refuse_nonfinite_point(self):
        chart=dict(horizontal_origin_epsg6404_m=[0,0],points=[[0,0,0,0,1],[10,10,0,0,1]])
        with self.assertRaises(ValueError):native_projection([float('nan'),3],chart)

    def test_refuse_zero_normal(self):
        chart=dict(horizontal_origin_epsg6404_m=[0,0],points=[[0,0,0,0,0],[10,10,0,0,0]])
        with self.assertRaises(ValueError):native_projection([4,3],chart)

class CapturedEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest=json.loads((SOURCE/'manifest.json').read_text())
        cls.mapping=json.loads((ROOT/MAP).read_text())

    def test_hashes(self):
        self.assertEqual(sha(ROOT/MAP),MAP_HASH)
        self.assertEqual(sha(SOURCE/'horn_creek_2021_0p2m.tif'),IMAGE_HASH)
        for name,digest in self.manifest['files'].items():
            self.assertEqual(sha(SOURCE/name),digest,name)

    def test_pixel_to_native_round_trip(self):
        with rasterio.open(SOURCE/'horn_creek_2021_0p2m.tif') as src:
            for feature in self.manifest['features']:
                xy=np.asarray([src.xy(r,c) for c,r in feature['pixel_column_row']])
                np.testing.assert_allclose(xy,feature['exposed_cap_polygon_epsg6404_m'],atol=1e-8,rtol=0)
                actual=[native_projection(q,self.mapping)[0] for q in xy]
                np.testing.assert_allclose(actual,feature['native_station_left_lateral_polygon_m'],atol=1e-8,rtol=0)
                self.assertLess(feature['max_chart_projection_residual_m'],.002)
                local=xy-xy[0]
                area=abs(np.sum(local[:,0]*np.roll(local[:,1],-1)-local[:,1]*np.roll(local[:,0],-1))*.5)
                self.assertAlmostEqual(area,feature['exposed_cap_area_m2'],places=6)

    def test_no_fabricated_underwater_geometry(self):
        features=self.manifest['features']
        self.assertEqual(len(features),2)
        for feature in features:
            self.assertIsNone(feature['height_m'])
            self.assertIsNone(feature['submerged_volume'])
            self.assertFalse(feature['collision_ready'])
            self.assertGreater(feature['exposed_cap_area_m2'],10)
            self.assertLess(feature['exposed_cap_area_m2'],20)
        self.assertLess(features[0]['native_vertex_mean_station_left_lateral_m'][0],features[1]['native_vertex_mean_station_left_lateral_m'][0])

    def test_zero_border_not_claimed_as_source_coverage(self):
        coverage=self.manifest['coverage']
        with rasterio.open(SOURCE/'horn_creek_2021_0p2m.tif') as src:
            actual=float(np.any(src.read()!=0,axis=0).mean())
            self.assertAlmostEqual(actual,coverage['nonzero_any_band_fraction'],places=12)
        self.assertGreater(coverage['dataset_mask_valid_fraction'],coverage['nonzero_any_band_fraction'])
        self.assertGreater(coverage['nonzero_any_band_fraction'],.94)
        self.assertEqual(coverage['source_chart_centreline_samples'],251)
        self.assertEqual(coverage['source_chart_centreline_nonzero_fraction'],1)

if __name__=='__main__':unittest.main()
