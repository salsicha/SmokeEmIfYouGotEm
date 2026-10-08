import copy
import json
import io
import struct
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np

from export_colorado_continuous_runtime import (registered_queries,registered_query_blocks,
    validate_runtime_geometry,write_fields,export,_export,BAND,sha)


def legacy_field_bytes(grid,station,frame,bed):
    """Frozen pre-streaming serialization oracle, not a runtime alternative."""
    wet=frame['wet']>.5;h=frame['h'];speed=np.hypot(frame['u'],frame['v'])
    result={}
    for name,array,dtype in [('bed',bed,'<f4'),('h',h,'<f4'),
            ('u',np.where(wet,frame['u'],0),'<f4'),('v',np.where(wet,frame['v'],0),'<f4'),
            ('wet_mask',wet,'u1')]:
        stream=io.BytesIO();np.save(stream,np.ascontiguousarray(array,dtype=dtype))
        result[f'{BAND}/{name}.npy']=stream.getvalue()
    froude=np.where(h>.05,speed/np.sqrt(9.81*np.maximum(h,.05)),0)
    energy=np.clip(.6*np.clip((speed-.5)/2.5,0,1)+.4*np.clip((froude-.5)/.5,0,1),0,1)
    support_wet=wet&(h>.05);stream=io.BytesIO()
    stream.write(struct.pack('<IIiiff',0x52534246,1,*bed.shape,grid['origin_y'],grid['dy']))
    for array,dtype in [(station,'<f4'),(np.where(support_wet,frame['eta'],bed).T,'<f4'),
                        (energy.T,'<f4'),(support_wet.T,'u1')]:
        array=np.ascontiguousarray(array,dtype=dtype)
        stream.write(struct.pack('<i',array.size));stream.write(array.tobytes())
    result[f'support_band_field_{BAND}.bin']=stream.getvalue()
    return result


class ContinuousRuntime(unittest.TestCase):
    def setUp(self):
        self.mapping = dict(schema='raftsim.curved_river_coordinate_map.v1', world_y_sign=-1,
            horizontal_origin_epsg6404_m=[200., 300.], vertical_datum_m=310.,
            points=[[s, s, 0., 0., 1.] for s in range(0, 22, 2)])
        self.terrain = dict(horizontal_origin_epsg6404_m=[200., 300.], vertical_datum_m=310.)
        self.grid = dict(nx=4, ny=3, dx=2., dy=2., origin_x=8., origin_y=-2.)

    def test_global_station_subset_is_not_recentred(self):
        station, queries = registered_queries(self.mapping, self.terrain, self.grid)
        np.testing.assert_array_equal(station, [8, 10, 12, 14])
        np.testing.assert_array_equal(queries[0], [[208, 298], [210, 298], [212, 298], [214, 298]])
        np.testing.assert_array_equal(queries[-1, -1], [214, 302])

    def test_wrong_frame_or_normal_refused(self):
        for key, value in [('vertical_datum_m', 0.), ('world_y_sign', 1),
                           ('horizontal_origin_epsg6404_m', [201., 300.])]:
            mapping = dict(self.mapping, **{key: value})
            with self.assertRaisesRegex(ValueError, 'same geographic frame'):
                registered_queries(mapping, self.terrain, self.grid)
        mapping = copy.deepcopy(self.mapping); mapping['points'][5][4] = 2.
        with self.assertRaisesRegex(ValueError, 'Nonunit'):
            registered_queries(mapping, self.terrain, self.grid)

    def test_fractional_or_uncovered_grid_refused(self):
        for origin in (8.1, -2., 20.):
            with self.assertRaisesRegex(ValueError, 'shared hydraulic lattice'):
                registered_queries(self.mapping, self.terrain, dict(self.grid, origin_x=origin))

    def test_fields_and_binary_preserve_station_major_support(self):
        station, _ = registered_queries(self.mapping, self.terrain, self.grid)
        bed = np.arange(12.).reshape(4, 3).T + 920.
        h = np.full(bed.shape, 2.); h[0, 0] = 0.
        frame = dict(h=h, eta=bed+h, u=h*.2, v=h*.1, wet=h > 0)
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)/'fields'
            arrays, baseline = write_fields(folder, self.grid, station, frame, bed)
            for key, expected in [('bed', bed), ('h', h), ('u', frame['u']), ('v', frame['v'])]:
                actual = np.load(folder/BAND/(key+'.npy'))
                np.testing.assert_allclose(actual, expected, rtol=1e-7)
                self.assertTrue(actual.flags.c_contiguous)
                self.assertEqual(arrays[key]['shape'], [3, 4])
            with (folder/baseline['file']).open('rb') as stream:
                self.assertEqual(struct.unpack('<IIiiff', stream.read(24)), (0x52534246, 1, 3, 4, -2., 2.))
                decoded = []
                for dtype in ('<f4', '<f4', '<f4', 'u1'):
                    count, = struct.unpack('<i', stream.read(4))
                    decoded.append(np.frombuffer(stream.read(count*np.dtype(dtype).itemsize), dtype=dtype))
                self.assertEqual(stream.read(), b'')
            np.testing.assert_array_equal(decoded[0], station)
            np.testing.assert_array_equal(decoded[1].reshape(4, 3), frame['eta'].T)
            np.testing.assert_array_equal(decoded[3].reshape(4, 3), frame['wet'].T)

    def test_failed_cook_cannot_create_runtime(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); out = root/'export'
            with patch('export_colorado_continuous_runtime.checked_cook', side_effect=ValueError('Cook did not pass its construction screen')):
                with self.assertRaisesRegex(ValueError, 'construction screen'):
                    export(root/'inputs', root/'cook', root/'review.json', out)
            self.assertFalse(out.exists())

    def test_complete_export_counts_real_terrain_files_before_creating_output(self):
        # Exercise the full orchestrator, not just write_fields: a Path was
        # accidentally indexed as a dictionary in the terrain-size guard.
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);inputs=root/'inputs';inputs.mkdir()
            terrain=root/'terrain';terrain.mkdir();shared=root/'shared';shared.mkdir()
            mapping=json.dumps(self.mapping)
            (inputs/'coordinate_map.json').write_text(mapping)
            (shared/'coordinate_map.json').write_text(mapping)
            (shared/'manifest.json').write_text('{}')
            manifest=dict(self.terrain,chunks=[dict(heightfield='tile.png')])
            (terrain/'manifest.json').write_text(json.dumps(manifest))
            tile=b'fixture terrain payload';(terrain/'tile.png').write_bytes(tile)
            review=root/'review.json';review.write_text('{}')
            (inputs/'build_report.json').write_text('{}')
            build=dict(name='Colorado fixture',source_core_interval_m=[8.,14.],
                continuous_terrain=dict(manifest='terrain/manifest.json',sha256=sha(terrain/'manifest.json')),
                shared_hydraulic_frame=dict(manifest='shared/manifest.json',sha256=sha(shared/'manifest.json')))
            bed=np.ones((3,4));frame=dict(h=bed,eta=bed*2,u=bed,v=bed*0,wet=bed)
            scenario=dict(grid=self.grid,fixed_dt=.05,roughness=.04)
            native=dict(scenario_id='fixture')
            receipt=dict(solver_sha256='fixture',statistics=dict(exact_face_discharge_target_m3s=226.5))
            class Terrain:
                def __init__(self,folder):self.manifest=manifest
                def sample(self,points):return np.ones(points.shape[:2])
            required=12*26+4*4+len(tile)+len(mapping.encode())+1048576
            with patch('export_colorado_continuous_runtime.ROOT',root), \
                 patch('export_colorado_continuous_runtime.checked_cook',return_value=(build,receipt,native,scenario,frame,bed)), \
                 patch('export_colorado_continuous_runtime.LandscapeTriangles',Terrain), \
                 patch('export_colorado_continuous_runtime.shutil.disk_usage') as usage:
                usage.return_value.free=40*1024**3+required-1
                with self.assertRaisesRegex(ValueError,'terrain/field disk headroom'):
                    _export(inputs,root/'cook',review,root/'too-small','colorado_river_grand_canyon_rowing')
                self.assertFalse((root/'too-small').exists())
                usage.return_value.free=40*1024**3+required
                out=root/'export'
                result=_export(inputs,root/'cook',review,out,'colorado_river_grand_canyon_rowing')
            self.assertEqual((out/'terrain/tile.png').read_bytes(),tile)
            self.assertEqual((out/'coordinate_map.json').read_text(),mapping)
            self.assertFalse(result['engine_validated']);self.assertFalse(result['full_river_coverage'])
            for name,digest in result['files_sha256'].items():self.assertEqual(sha(out/name),digest)
            for name,data in legacy_field_bytes(self.grid,np.array([8.,10.,12.,14.]),frame,bed).items():
                self.assertEqual((out/'cooked_flow_fields'/name).read_bytes(),data)

    def test_flow_band_is_explicit_and_cannot_escape_export(self):
        station,_=registered_queries(self.mapping,self.terrain,self.grid)
        bed=np.ones((3,4));frame=dict(h=bed,eta=bed*2,u=bed,v=bed*0,wet=bed)
        with tempfile.TemporaryDirectory() as directory:
            folder=Path(directory)/'fields'
            arrays,baseline=write_fields(folder,self.grid,station,frame,bed,'lidar_flight_window_inferred')
            self.assertTrue(arrays['bed']['file'].startswith('lidar_flight_window_inferred/'))
            self.assertNotIn(BAND,baseline['file'])
            with self.assertRaisesRegex(ValueError,'Unsafe flow band'):
                write_fields(Path(directory)/'other',self.grid,station,frame,bed,'../bad')

    def test_blocked_queries_exact_original_arithmetic(self):
        mapping=copy.deepcopy(self.mapping)
        for row in mapping['points']:
            angle=row[0]/123.;row[1]=np.sin(angle)*212.25;row[2]=np.cos(angle)*98.17
            row[3]=np.sin(angle);row[4]=np.cos(angle)
        station,expected=registered_queries(mapping,self.terrain,self.grid)
        for size in (3,7,12,100):
            actual=np.empty_like(expected);count=0
            for sl,queries in registered_query_blocks(mapping,self.terrain,self.grid,block_cells=size):
                self.assertLessEqual(queries.shape[0]*queries.shape[1],size)
                actual[:,sl]=queries;count+=queries.shape[1]
            self.assertEqual(count,len(station));np.testing.assert_array_equal(actual,expected)
        with self.assertRaisesRegex(ValueError,'complete cross-section'):
            list(registered_query_blocks(mapping,self.terrain,self.grid,block_cells=2))

    def test_streamed_bytes_equal_legacy_for_all_block_sizes(self):
        rng=np.random.default_rng(987123);ny,nx=7,19
        # Noncontiguous and negative strides match disk-backed and transposed callers.
        bed=(rng.random((nx,ny))*2300+100.).T[:,::-1]
        h=(rng.random((nx,ny))*3).T;h[0,:5]=[0.,.049,.05,.051,2.]
        frame=dict(h=h,eta=bed+h,u=rng.normal(size=(nx,ny)).T*6,
                   v=rng.normal(size=(nx,ny)).T*3,wet=(h>.049).astype(float))
        station=np.arange(nx)*2.+12000.
        grid=dict(nx=nx,ny=ny,origin_y=-6.,dy=2.)
        expected=legacy_field_bytes(grid,station,frame,bed)
        with tempfile.TemporaryDirectory() as directory:
            for size in (19,41,500):
                folder=Path(directory)/str(size)
                write_fields(folder,grid,station,frame,bed,block_cells=size)
                for name,data in expected.items():
                    self.assertEqual((folder/name).read_bytes(),data,name)

    def test_geometry_checks_every_block_and_keeps_original_gates(self):
        _,queries=registered_queries(self.mapping,self.terrain,self.grid)
        bed=queries[:,:,0]+queries[:,:,1];frame=dict(wet=np.ones(bed.shape))
        class Terrain:
            manifest=self.terrain
            def sample(self,points):return points[:,:,0]+points[:,:,1]
        triangles=Terrain()
        station,error=validate_runtime_geometry(self.mapping,triangles,self.grid,frame,bed,block_cells=3)
        self.assertEqual(error,0.);self.assertEqual(len(station),4)
        for column in (0,1,3):
            changed=bed.copy();changed[2,column]+=.001
            with self.assertRaisesRegex(ValueError,'terrain triangles'):
                validate_runtime_geometry(self.mapping,triangles,self.grid,frame,changed,block_cells=3)
            wet=frame['wet'].copy();wet[:,column]=0
            with self.assertRaisesRegex(ValueError,'Dry cross-section'):
                validate_runtime_geometry(self.mapping,triangles,self.grid,dict(wet=wet),bed,block_cells=3)

    def test_nonfinite_or_low_disk_refused_before_fields_created(self):
        station,_=registered_queries(self.mapping,self.terrain,self.grid)
        bed=np.ones((3,4));frame=dict(h=bed,eta=bed*2,u=bed,v=bed*0,wet=bed)
        with tempfile.TemporaryDirectory() as directory:
            folder=Path(directory)/'fields'
            for key in frame:
                bad={k:v.copy() for k,v in frame.items()};bad[key][-1,-1]=np.nan
                with self.assertRaisesRegex(ValueError,'Nonfinite'):
                    write_fields(folder,self.grid,station,bad,bed,block_cells=4)
                self.assertFalse(folder.exists())
            with patch('export_colorado_continuous_runtime.shutil.disk_usage') as usage:
                usage.return_value.free=40*1024**3
                with self.assertRaisesRegex(ValueError,'forty GiB reserve'):
                    write_fields(folder,self.grid,station,frame,bed)
            self.assertFalse(folder.exists())


if __name__ == '__main__':
    unittest.main()
