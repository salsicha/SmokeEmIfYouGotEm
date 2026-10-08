import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import numpy as np
import refine_colorado_shared_hydraulic_frame as module
from build_colorado_catalog_evidence import sha
from build_colorado_shared_hydraulic_frame import shared_frame,select_window
from refine_colorado_shared_hydraulic_frame import refined_arrays


class RefinedFrame(unittest.TestCase):
    def setUp(self):
        self.rows=[dict(easting=1000+s,northing=2000+60*np.exp(-((s-2400)/90)**2)) for s in np.arange(0,5000,10.)]
        self.patch=[dict(source_plateau_interval_m=[1900,2900],taper_m=600,smoothing_m=90)]

    def test_baseline_matches_original_and_preserves_source_and_upstream(self):
        saved=copy.deepcopy(self.rows)
        baseline,after,receipt=refined_arrays(self.rows,self.patch)
        expected=shared_frame(self.rows)
        for key in expected:np.testing.assert_array_equal(baseline[key],expected[key])
        self.assertEqual(saved,self.rows)
        n=receipt['upstream_identical_point_count']
        for key in baseline:np.testing.assert_array_equal(baseline[key][:n],after[key][:n])
        self.assertGreater(receipt['maximum_numerical_axis_displacement_m'],1.)
        self.assertFalse(receipt['captured_geometry_modified'])
        self.assertTrue(np.all(np.diff(after['source_global_station_m'])>0))
        self.assertLess(np.abs(after['curvature_per_m']).max(),np.abs(baseline['curvature_per_m']).max())

    def test_all_overlapping_windows_use_same_grid(self):
        _,a,_=refined_arrays(self.rows,self.patch)
        first=select_window(a,dict(schema='raftsim.colorado_continuous_source_window.v1',source_halo_interval_m=[1500,3200]))
        second=select_window(a,dict(schema='raftsim.colorado_continuous_source_window.v1',source_halo_interval_m=[2100,3500]))
        _,ia,ib=np.intersect1d(first[0],second[0],return_indices=True)
        for i in range(4):np.testing.assert_array_equal(first[i][ia],second[i][ib])

    def test_invalid_or_overlapping_refinements_rejected(self):
        cases=[[],self.patch*2,[{}]]
        for key,value in [('smoothing_m',60),('smoothing_m',float('nan')),('smoothing_m',301),('taper_m',0),
                          ('source_plateau_interval_m',[10,400]),('source_plateau_interval_m',[1900,5500]),
                          ('source_plateau_interval_m',[2900,1900])]:
            p=copy.deepcopy(self.patch);p[0][key]=value;cases.append(p)
        for case in cases:
            with self.subTest(case=case),self.assertRaises(ValueError):refined_arrays(self.rows,case)

    def test_disconnected_and_nonfinite_sources_rejected(self):
        for rows in (self.rows[:1],[dict(easting=0,northing=0),dict(easting=100,northing=0),dict(easting=110,northing=0)],
                     [dict(easting=0,northing=0),dict(easting=1,northing=0),dict(easting=2,northing=0)],
                     [dict(easting=0,northing=0),dict(easting=10,northing=float('nan')),dict(easting=20,northing=0)]):
            with self.assertRaises(ValueError):refined_arrays(rows,self.patch)

    def fixture(self,root):
        original=root/'original';original.mkdir()
        (root/'source.csv').write_text('synthetic source identity\n')
        spec=root/'spec.json';spec.write_text(json.dumps(self.patch))
        np.savez_compressed(original/'frame.npz',**shared_frame(self.rows))
        (original/'coordinate_map.json').write_text(json.dumps(dict(horizontal_origin_epsg6404_m=[1000,2000],points=[])))
        manifest=dict(schema='raftsim.colorado_shared_hydraulic_frame.v1',grid_step_m=2,
            source_profile='source.csv',source_profile_sha256=sha(root/'source.csv'),limitations=[],
            files_sha256={n:sha(original/n) for n in ('frame.npz','coordinate_map.json')})
        (original/'manifest.json').write_text(json.dumps(manifest))
        return original,spec

    def test_export_binds_sources_and_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);original,spec=self.fixture(root)
            with patch.object(module,'ROOT',root),patch.object(module,'read_profile',return_value=self.rows):
                result=module.build(original,spec,root/'candidate')
                self.assertFalse(result['runtime_ready'])
                self.assertEqual(result['numerical_chart_refinement']['specification_sha256'],sha(spec))
                for name,h in result['files_sha256'].items():self.assertEqual(sha(root/'candidate'/name),h)
                with self.assertRaisesRegex(ValueError,'Fresh'):module.build(original,spec,root/'candidate')

    def test_changed_sources_and_unreconstructable_baseline_are_rejected(self):
        for changed in ('source','frame_hash','baseline'):
            with self.subTest(changed=changed),tempfile.TemporaryDirectory() as folder:
                root=Path(folder);original,spec=self.fixture(root)
                if changed=='source':(root/'source.csv').write_text('changed source\n')
                elif changed=='frame_hash':(original/'frame.npz').write_bytes(b'changed')
                else:
                    arrays=shared_frame(self.rows);arrays['east_north_m'][100,0]+=1
                    np.savez_compressed(original/'frame.npz',**arrays)
                    manifest=json.loads((original/'manifest.json').read_text())
                    manifest['files_sha256']['frame.npz']=sha(original/'frame.npz')
                    (original/'manifest.json').write_text(json.dumps(manifest))
                with patch.object(module,'ROOT',root),patch.object(module,'read_profile',return_value=self.rows):
                    with self.assertRaises(ValueError):module.build(original,spec,root/'candidate')
                    self.assertFalse((root/'candidate').exists())


if __name__=='__main__':unittest.main()
