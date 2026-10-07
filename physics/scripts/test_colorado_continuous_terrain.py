import unittest
import json
import tempfile
from unittest.mock import patch
from pathlib import Path
import numpy as np
from export_colorado_continuous_terrain import (TerrainMosaic,encode_height,HEIGHT_BASE,HEIGHT_RANGE,
    LandscapeTriangles,VERTICES,SPACING,SPAN,sha,write_png_u16,SourceGridCache,LazySourceGrid)


class ContinuousTerrain(unittest.TestCase):
    def test_mosaic_samples_only_covered_queries_with_identical_owner_rule(self):
        from scipy.ndimage import map_coordinates
        sources=[self.source(0,[0,20]),self.source(10,[20,30])]
        east,north=np.meshgrid(np.arange(-100,100,.5),np.arange(-10,30,.5))
        expected=np.full(east.shape,np.nan);owner=np.full(east.shape,-1);score=np.full(east.shape,np.inf)
        for i,s in enumerate(sources):
            g=s['grid'];x,y=g['corner_east_north_m'];h,w=g['bed_ellipsoid_m'].shape
            covered=(east>=x)&(east<=x+w)&(north>=y-h)&(north<=y)
            rows=np.clip(y-north-.5,0,h-1);cols=np.clip(east-x-.5,0,w-1)
            station=map_coordinates(g['station_m'],[rows,cols],order=1,mode='nearest',prefilter=False)+s['origin']
            distance=np.maximum(s['core'][0]-station,0)+np.maximum(station-s['core'][1],0)
            take=covered&(distance<score)
            z=map_coordinates(g['bed_ellipsoid_m'],[rows,cols],order=1,mode='nearest',prefilter=False)
            expected[take]=z[take];owner[take]=i;score[take]=distance[take]
        with patch('export_colorado_continuous_terrain.map_coordinates',wraps=map_coordinates) as sampler:
            actual,actual_owner=TerrainMosaic(sources).sample(east,north)
        np.testing.assert_array_equal(actual,expected);np.testing.assert_array_equal(actual_owner,owner)
        self.assertTrue(all(call.args[1][0].size<east.size//10 for call in sampler.call_args_list))
        value,who=TerrainMosaic(sources).sample(5.,5.)
        self.assertEqual(value,800.5);self.assertEqual(who,0)
        value,who=TerrainMosaic(sources).sample(np.nan,5.)
        self.assertTrue(np.isnan(value));self.assertEqual(who,-1)

    def test_indexed_triangle_lookup_matches_exhaustive_edges_and_missing_coverage(self):
        from export_colorado_catalog_runtime import landscape_sample
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp);self.write_chunks(folder);terrain=LandscapeTriangles(folder)
            rng=np.random.default_rng(23)
            random=rng.uniform([999.,1999.],[1505.,2253.],size=(10000,2))
            edges=np.array([[x,y] for x in (1000.,1252.,1504.) for y in (2000.,2126.,2252.)])
            xy=np.concatenate([random,edges,edges+[1e-7,-1e-7],edges+[-1e-7,1e-7],
                               [[np.nan,2000],[1000,np.inf],[1e30,-1e30]]])
            expected=np.full(len(xy),np.nan)
            for corner,height in terrain.chunks:
                rows=(corner[1]-xy[:,1])/SPACING;cols=(xy[:,0]-corner[0])/SPACING
                inside=(rows>=0)&(rows<=VERTICES-1)&(cols>=0)&(cols<=VERTICES-1)
                expected[inside]=landscape_sample(height,rows[inside],cols[inside])
            np.testing.assert_array_equal(terrain.sample(xy),expected)
            np.testing.assert_array_equal(terrain.sample(xy[0]),expected[0])
            self.assertEqual(terrain.sample(np.empty((0,2))).shape,(0,))
            # Remove a tile without changing bounding-box metadata: a hole is
            # still missing, and only its shared edge may use the neighbour.
            terrain.by_key.pop(1)
            actual=terrain.sample(np.array([[1252,2100],[1252.01,2100],[1400,2100]]))
            self.assertTrue(np.isfinite(actual[0]));self.assertTrue(np.isnan(actual[1:]).all())

    def test_bounded_sources_preserve_samples_and_owner_after_eviction(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache=SourceGridCache(7000);eager=[];lazy=[]
            for i in range(6):
                s=self.source(i*10,[i*10,(i+1)*10]);eager.append(s)
                path=Path(tmp)/f'{i}.npz';np.savez_compressed(path,**s['grid'])
                grid=LazySourceGrid(path,cache)
                lazy.append(dict(s,grid=grid,bounds=(*s['grid']['corner_east_north_m'],20,20)))
            a=TerrainMosaic(eager);b=TerrainMosaic(lazy)
            # Reverse traversal forces reloads after eviction. No source array
            # or sample is downsampled to fit the memory budget.
            for i in list(range(6))+list(reversed(range(6))):
                x,y=np.meshgrid(np.arange(i*10,i*10+11),np.arange(3,17))
                expected,owner=a.sample(x,y);actual,lazy_owner=b.sample(x,y)
                np.testing.assert_array_equal(actual,expected)
                np.testing.assert_array_equal(lazy_owner,owner)
                self.assertLessEqual(cache.resident_bytes,cache.max_bytes)

    def test_indexed_lookup_handles_negative_tile_indices_and_four_way_corners(self):
        from export_colorado_catalog_runtime import landscape_sample
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp)
            self.write_chunks(folder,[(i,j) for i in (-1,0,1) for j in (-1,0,1) if (i,j)!=(0,0)])
            terrain=LandscapeTriangles(folder)
            x,y=np.meshgrid([748.,1000.,1252.,1504.],[1748.,2000.,2252.,2504.])
            corners=np.column_stack([x.ravel(),y.ravel()])
            points=np.concatenate([corners,corners+[1e-7,1e-7],corners-[1e-7,1e-7],
                np.random.default_rng(2).uniform([747,1747],[1505,2505],(4000,2))])
            expected=np.full(len(points),np.nan)
            for corner,height in terrain.chunks:
                rows=(corner[1]-points[:,1])/SPACING;cols=(points[:,0]-corner[0])/SPACING
                inside=(rows>=0)&(rows<=126)&(cols>=0)&(cols<=126)
                expected[inside]=landscape_sample(height,rows[inside],cols[inside])
            np.testing.assert_array_equal(terrain.sample(points),expected)

    def test_bounded_source_refuses_mid_assembly_change(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'grid.npz';s=self.source(0,[0,20])
            np.savez_compressed(path,**s['grid']);grid=LazySourceGrid(path,SourceGridCache())
            grid['bed_ellipsoid_m']
            path.write_bytes(b'changed source')
            with self.assertRaisesRegex(ValueError,'changed during'):
                grid['bed_ellipsoid_m']

    def write_chunks(self,folder,indices=((0,0),(1,0))):
        chunks=[]
        for i,j in indices:
            r,c=np.indices((VERTICES,VERTICES))
            # Non-planar quads distinguish triangle interpolation from bilinear.
            encoded=(20000+(c+i*126)*3+(r-j*126)*2+(r%2)*(c%2)*40).astype('uint16')
            name=f'height_{i}.png' if j==0 else f'height_{i}_{j}.png';write_png_u16(folder/name,encoded)
            chunks.append(dict(chunk=[i,j],heightfield=name,sha256=sha(folder/name),
                               origin_epsg6404_m=[1000+i*SPAN,2000+(j+1)*SPAN]))
        manifest=dict(schema='raftsim.colorado_continuous_landscape.v1',
            horizontal_origin_epsg6404_m=[1000,2000],chunks=chunks,
            landscape=dict(vertices=VERTICES,spacing_m=SPACING,span_m=SPAN,
                           height_base_ellipsoid_m=HEIGHT_BASE,height_range_m=HEIGHT_RANGE))
        (folder/'manifest.json').write_text(json.dumps(manifest))
        return manifest

    def test_encoded_triangles_match_on_shared_edge_and_do_not_extrapolate(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp);self.write_chunks(folder);terrain=LandscapeTriangles(folder)
            xy=np.array([[1252,2201.3],[1252-1e-7,2201.3],[1252+1e-7,2201.3],
                         [999,2200],[float('nan'),2200]])
            z=terrain.sample(xy)
            np.testing.assert_allclose(z[:3],z[0],atol=1e-6,rtol=0)
            self.assertTrue(np.isnan(z[3:]).all())
            # At quarter-x, three-quarter-y the NW-SE triangle contributes
            # 25% of the southeast 40-unit perturbation, not bilinear 18.75%.
            sample=terrain.sample(np.array([[1000+.25*2,2252-.75*2]]))[0]
            expected=HEIGHT_BASE+(20000+.25*3+.75*2+.25*40)*HEIGHT_RANGE/65535
            self.assertAlmostEqual(sample,expected,places=10)

    def test_height_identity_and_geographic_lattice_are_checked(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp);m=self.write_chunks(folder)
            m['chunks'][0]['origin_epsg6404_m'][0]+=1
            (folder/'manifest.json').write_text(json.dumps(m))
            with self.assertRaisesRegex(ValueError,'shifted'):LandscapeTriangles(folder)
            m=self.write_chunks(folder)
            m['chunks'][0]['sha256']='0'*64
            (folder/'manifest.json').write_text(json.dumps(m))
            with self.assertRaisesRegex(ValueError,'Changed'):LandscapeTriangles(folder)

    def test_mismatched_shared_edge_rejected_even_with_updated_hash(self):
        with tempfile.TemporaryDirectory() as tmp:
            from PIL import Image
            folder=Path(tmp);m=self.write_chunks(folder)
            path=folder/m['chunks'][1]['heightfield']
            with Image.open(path) as image:encoded=np.array(image).astype('uint16')
            encoded[10,0]+=1;write_png_u16(path,encoded)
            m['chunks'][1]['sha256']=sha(path)
            (folder/'manifest.json').write_text(json.dumps(m))
            with self.assertRaisesRegex(ValueError,'discontinuous'):LandscapeTriangles(folder)

    def test_legacy_export_cannot_replace_common_grid_with_stretched_terrain(self):
        from export_colorado_catalog_runtime import export
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp)
            (folder/'build_report.json').write_text(json.dumps(dict(continuous_terrain={'manifest':'shared'})))
            with self.assertRaisesRegex(ValueError,'common-grid runtime assembly'):
                export(folder,folder/'cook',folder/'review.json',folder/'runtime')
            self.assertFalse((folder/'runtime').exists())

    def source(self,x,core):
        station=np.tile(np.arange(x,x+20)+.5,(20,1))
        return dict(core=core,origin=0,grid=dict(corner_east_north_m=[x,20],
            station_m=station,bed_ellipsoid_m=800+station*.1))

    def test_source_choice_is_independent_of_query_chunk(self):
        m=TerrainMosaic([self.source(10,[20,30]),self.source(0,[0,20])])
        east,north=np.meshgrid(np.arange(5,26),np.arange(5,16))
        z,owner=m.sample(east,north)
        edge,edge_owner=m.sample(east[:,-1:],north[:,-1:])
        np.testing.assert_array_equal(encode_height(z)[:,-1:],encode_height(edge))
        np.testing.assert_array_equal(owner[:,-1:],edge_owner)

    def test_missing_source_stays_missing(self):
        z,owner=TerrainMosaic([self.source(0,[0,20])]).sample(np.array([5,25]),np.array([5,5]))
        self.assertTrue(np.isnan(z[1]));self.assertEqual(owner[1],-1)
        with self.assertRaises(ValueError):encode_height(z)

    def test_common_encoding_not_per_tile_normalization(self):
        a=encode_height(np.array([500.,800.,900.]))
        b=encode_height(np.array([800.,900.,1200.]))
        np.testing.assert_array_equal(a[1:],b[:2])
        decoded=HEIGHT_BASE+a.astype(float)*HEIGHT_RANGE/65535
        self.assertLess(abs(decoded-np.array([500,800,900])).max(),.019)
        with self.assertRaises(ValueError):encode_height(np.array([3000.]))


if __name__=='__main__':unittest.main()
