import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import numpy as np
import colorado_frame_compatibility as module
from build_colorado_catalog_evidence import sha


class FrameCompatibility(unittest.TestCase):
    def make(self,root,name,alter=None):
        folder=root/name;folder.mkdir();s=np.arange(200)*2.
        a=dict(station_m=s,east_north_m=np.column_stack([s+1000,s*0+2000]),
            normal_east_north=np.tile([0.,1.],(200,1)),curvature_per_m=s*0,source_global_station_m=s.copy())
        if alter:alter(a)
        np.savez_compressed(folder/'frame.npz',**a)
        points=np.column_stack([a['station_m'],a['east_north_m']-[1000,2000],a['normal_east_north']])
        (folder/'coordinate_map.json').write_text(json.dumps(dict(schema='raftsim.curved_river_coordinate_map.v1',world_y_sign=-1,
            vertical_datum_m=100.,horizontal_origin_epsg6404_m=[1000,2000],mapping_policy=name,points=points.tolist())))
        manifest=dict(schema='raftsim.colorado_shared_hydraulic_frame.v1',grid_step_m=2,source_profile='source.csv',
            source_profile_sha256=sha(root/'source.csv'),files_sha256={n:sha(folder/n) for n in ('frame.npz','coordinate_map.json')})
        (folder/'manifest.json').write_text(json.dumps(manifest))
        report=dict(shared_hydraulic_frame=dict(manifest=f'{name}/manifest.json',sha256=sha(folder/'manifest.json')),
            files_sha256={'coordinate_map.json':sha(folder/'coordinate_map.json')})
        return folder,report

    def test_unused_chart_change_allows_exact_old_source_without_modifying_it(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'source.csv').write_text('captured source')
            old,report=self.make(root,'old');new,_=self.make(root,'new',lambda a:a['east_north_m'].__setitem__((150,1),2001.))
            before={p:sha(p) for p in old.iterdir()}
            with patch.object(module,'ROOT',root):
                checker=module.SharedFrameCompatibility(new)
                result=checker.check(report,dict(nx=50,dx=2,dy=2,origin_x=100.))
                self.assertTrue(result['all_frame_arrays_and_render_coordinates_bit_identical'])
                checker.verify_unchanged()
            self.assertTrue(all(sha(p)==h for p,h in before.items()))

    def test_every_used_frame_component_must_be_exact(self):
        for key in ('east_north_m','curvature_per_m','source_global_station_m','normal_east_north'):
            with self.subTest(key=key),tempfile.TemporaryDirectory() as directory:
                root=Path(directory);(root/'source.csv').write_text('source');_,report=self.make(root,'old')
                def alter(a):
                    if key=='normal_east_north':a[key][60]=[.6,.8]
                    else:a[key][60]+=1e-7
                new,_=self.make(root,'new',alter)
                with patch.object(module,'ROOT',root):
                    checker=module.SharedFrameCompatibility(new)
                    with self.assertRaisesRegex(ValueError,'rebuild input'):
                        checker.check(report,dict(nx=50,dx=2,dy=2,origin_x=100.))

    def test_fractional_or_missing_lattice_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'source.csv').write_text('source');old,report=self.make(root,'old')
            with patch.object(module,'ROOT',root):
                checker=module.SharedFrameCompatibility(old)
                for start in (-2.,100.1,350.):
                    with self.assertRaisesRegex(ValueError,'lattice'):
                        checker.check(report,dict(nx=50,dx=2,dy=2,origin_x=start))

    def test_mismatched_render_map_and_changed_dependencies_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'source.csv').write_text('source');old,report=self.make(root,'old')
            with patch.object(module,'ROOT',root):
                checker=module.SharedFrameCompatibility(old)
                bad=copy.deepcopy(report);bad['files_sha256']['coordinate_map.json']='bad'
                with self.assertRaisesRegex(ValueError,'registered shared map'):
                    checker.check(bad,dict(nx=50,dx=2,dy=2,origin_x=100.))
                (root/'source.csv').write_text('changed')
                with self.assertRaisesRegex(ValueError,'dependency changed'):checker.verify_unchanged()
                with self.assertRaisesRegex(ValueError,'captured chart source'):module.SharedFrameCompatibility(old)


if __name__=='__main__':unittest.main()
