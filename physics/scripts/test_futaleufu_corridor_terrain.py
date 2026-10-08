import json
from pathlib import Path
import tempfile
import unittest

import numpy as np
import shapely

from export_futaleufu_corridor_terrain import encode, chunk_indices, TerrainBed
from export_colorado_continuous_terrain import LandscapeTriangles, write_png_u16, sha
from test_futaleufu_corridor_bed import fixture


class TerrainTests(unittest.TestCase):
    def test_low_elevation_encoding_is_not_colorado_clamp(self):
        z=np.array([0.,137.,145.5,206.14389,1589.,2400.])
        np.testing.assert_allclose(encode(z).astype(float)*2400/65535,z,atol=2400/65535/2)
        for bad in (-.001,2400.001,np.nan):
            with self.assertRaises(ValueError):encode([bad])

    def test_all_branch_chunks_and_shared_origin(self):
        lines=[shapely.LineString([(0,0),(1000,0)]),shapely.LineString([(500,0),(500,1000)])]
        indices=chunk_indices(lines,[0,0],100,2.)
        for line in lines:
            for p in np.asarray(line.coords):
                self.assertIn(tuple(np.floor(p/252).astype(int)),indices)
        self.assertEqual(len(indices),len(set(indices)))
        for spacing in (0,3,True):
            with self.assertRaises(ValueError):chunk_indices(lines,[0,0],100,spacing)

    def test_lattice_adapter_preserves_exact_samples(self):
        bed=fixture();adapter=TerrainBed(bed)
        xy=np.array([[[-70,0],[70,0]],[[0,70],[40,0]]])
        for k,v in adapter.sample(xy).items():
            np.testing.assert_array_equal(v.ravel(),bed.sample(xy.reshape(-1,2))[k])

    def make_terrain(self, folder):
        chunks=[]
        for i in (0,1):
            r,c=np.indices((127,127));z=137.+.02*(c+i*126)-.03*r
            name=f'height_{i}_0.png';write_png_u16(folder/name,encode(z))
            chunks.append(dict(chunk=[i,0],heightfield=name,sha256=sha(folder/name),origin_m=[1000+i*252,2252]))
        m=dict(schema='raftsim.continuous_landscape.v1',river_id='futaleufu_river_chile',
            horizontal_crs='EPSG:32718',vertical_reference='EGM2008',horizontal_origin_m=[1000,2000],
            landscape=dict(vertices=127,spacing_m=2.,span_m=252.,height_base_m=0.,height_range_m=2400.),chunks=chunks)
        (folder/'manifest.json').write_text(json.dumps(m))
        return m

    def test_reader_uses_correct_datum_and_exact_shared_edge(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp);self.make_terrain(folder)
            reader=LandscapeTriangles(folder)
            values=reader.sample([[1000,2252],[1252,2252],[1504,2000]])
            np.testing.assert_allclose(values,[137.,139.52,138.26],atol=2400/65535/2)
            self.assertTrue(np.isnan(reader.sample([[999,2000]])[0]))
            reader.verify_unchanged()

    def test_wrong_frame_and_height_base_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp);original=self.make_terrain(folder)
            for key,value in [('horizontal_crs','EPSG:3157'),('vertical_reference','ellipsoid'),('river_id','unknown')]:
                m=dict(original);m[key]=value
                (folder/'manifest.json').write_text(json.dumps(m))
                with self.assertRaises(ValueError):LandscapeTriangles(folder)
            original['landscape']['height_base_m']=200
            (folder/'manifest.json').write_text(json.dumps(original))
            with self.assertRaises(ValueError):LandscapeTriangles(folder)

    def test_shared_edge_mismatch_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp);m=self.make_terrain(folder)
            path=folder/m['chunks'][1]['heightfield']
            write_png_u16(path,np.full((127,127),5000,dtype='uint16'))
            m['chunks'][1]['sha256']=sha(path)
            (folder/'manifest.json').write_text(json.dumps(m))
            with self.assertRaisesRegex(ValueError,'boundary is discontinuous'):LandscapeTriangles(folder)


if __name__=='__main__':unittest.main()
