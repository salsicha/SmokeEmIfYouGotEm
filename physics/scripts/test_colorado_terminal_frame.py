import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import numpy as np
import anchor_colorado_terminal_frame as module
import build_colorado_shared_hydraulic_frame as shared
from build_colorado_catalog_evidence import sha
from build_colorado_shared_hydraulic_frame import shared_frame,select_window
from anchor_colorado_terminal_frame import anchor_terminal,anchor_initial,source_end_caps


class TerminalFrame(unittest.TestCase):
    def fixture(self):
        rows=[dict(easting=1000+s,northing=2000+5*np.sin(s/240)) for s in np.arange(0,2600,10.)]
        return rows,shared_frame(rows)

    def test_exact_source_endpoint_and_normal_without_source_edits(self):
        rows,before=self.fixture();original=copy.deepcopy(rows)
        after,r=anchor_terminal(before,rows)
        caps=source_end_caps(rows);n=r['unchanged_prefix_points']
        for key in before:np.testing.assert_array_equal(before[key][:n],after[key][:n])
        self.assertEqual(rows,original)
        self.assertEqual(after['source_global_station_m'][-1],caps['stations'][-1])
        np.testing.assert_array_equal(after['east_north_m'][-1],caps['positions'][-1])
        t=np.array(caps['directions'][-1]);np.testing.assert_array_equal(after['normal_east_north'][-1],[-t[1],t[0]])
        np.testing.assert_array_equal(np.diff(after['station_m']),np.full(len(after['station_m'])-1,2.))
        tangent=np.column_stack([after['normal_east_north'][:,1],-after['normal_east_north'][:,0]])
        expected=tangent[:,0]*np.gradient(tangent[:,1],2)-tangent[:,1]*np.gradient(tangent[:,0],2)
        self.assertEqual(after['curvature_per_m'][-1],expected[-1])
        self.assertTrue(np.all(np.diff(after['source_global_station_m'])>0))
        p=dict(schema='raftsim.colorado_continuous_source_window.v1',source_halo_interval_m=[2000,caps['stations'][-1]])
        selected=select_window(after,p)
        self.assertEqual(selected[4][-1]+2000,caps['stations'][-1])

    def test_no_second_anchor_missing_source_extension_or_large_correction(self):
        rows,a=self.fixture();anchored,_=anchor_terminal(a,rows)
        with self.assertRaises(ValueError):anchor_terminal(anchored,rows)
        for delta in (-10,10):
            bad=copy.deepcopy(a);bad['source_global_station_m'][-1]+=delta
            with self.assertRaises(ValueError):anchor_terminal(bad,rows)
        bad=copy.deepcopy(a);bad['east_north_m'][:,1]+=100
        with self.assertRaises(ValueError):anchor_terminal(bad,rows)

    def test_initial_anchor_preserves_downstream_chart_and_both_source_ends(self):
        rows,a=self.fixture();terminal,_=anchor_terminal(a,rows)
        after,r=anchor_initial(terminal,rows);caps=source_end_caps(rows)
        for key in a:np.testing.assert_array_equal(after[key][r['unchanged_suffix_from_point']:],terminal[key][r['unchanged_suffix_from_point']:])
        np.testing.assert_array_equal(after['east_north_m'][[0,-1]],caps['positions'])
        direction=np.array(caps['directions'][0]);np.testing.assert_array_equal(after['normal_east_north'][0],[-direction[1],direction[0]])
        np.testing.assert_array_equal(after['source_global_station_m'],terminal['source_global_station_m'])

    def test_invalid_chart_source_and_blend_refused(self):
        rows,a=self.fixture()
        for blend in (0,99,201,602,float('nan')):
            with self.assertRaises(ValueError):anchor_terminal(a,rows,blend)
        for key in a:
            bad=copy.deepcopy(a);bad[key][-1]=np.nan
            with self.assertRaises(ValueError):anchor_terminal(bad,rows)
        bad=copy.deepcopy(rows);bad[-1]['easting']+=200
        with self.assertRaises(ValueError):anchor_terminal(a,bad)

    def disk_fixture(self,root):
        rows,a=self.fixture();original=root/'original';original.mkdir()
        (root/'source.csv').write_text('source identity\n')
        np.savez_compressed(original/'frame.npz',**a)
        (original/'coordinate_map.json').write_text(json.dumps(dict(horizontal_origin_epsg6404_m=[1000,2000],mapping_policy='fixture',points=[])))
        m=dict(schema='raftsim.colorado_shared_hydraulic_frame.v1',grid_step_m=2.,source_profile='source.csv',
            source_profile_sha256=sha(root/'source.csv'),limitations=[],
            files_sha256={n:sha(original/n) for n in ('frame.npz','coordinate_map.json')})
        (original/'manifest.json').write_text(json.dumps(m))
        return rows,original

    def test_export_and_loader_bind_endpoint_to_the_captured_source(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);rows,original=self.disk_fixture(root);out=root/'anchored'
            with patch.object(module,'ROOT',root),patch.object(module,'read_profile',return_value=rows),patch.object(shared,'ROOT',root),patch.object(shared,'read_profile',return_value=rows):
                m=module.build(original,out)
                self.assertFalse(m['runtime_ready'])
                for name,h in m['files_sha256'].items():self.assertEqual(h,sha(out/name))
                p=dict(schema='raftsim.colorado_continuous_source_window.v1',source_halo_interval_m=[0,source_end_caps(rows)['stations'][-1]])
                shared.load(out,p)
                both=root/'both';module.build(out,both,endpoint='start')
                shared.load(both,p)
                with self.assertRaisesRegex(ValueError,'prior anchor'):module.build(both,root/'duplicate',endpoint='start')
                with self.assertRaisesRegex(ValueError,'Fresh'):module.build(original,out)
                m['source_endpoint_anchor']['source_end_caps']['positions'][-1][0]+=1
                (out/'manifest.json').write_text(json.dumps(m))
                with self.assertRaisesRegex(ValueError,'captured endpoint'):shared.load(out,p)

    def test_changed_source_or_parent_chart_refused_before_output(self):
        for name in ('source.csv','original/frame.npz'):
            with self.subTest(name=name),tempfile.TemporaryDirectory() as folder:
                root=Path(folder);rows,original=self.disk_fixture(root)
                (root/name).write_bytes(b'changed')
                with patch.object(module,'ROOT',root),patch.object(module,'read_profile',return_value=rows):
                    with self.assertRaisesRegex(ValueError,'Changed'):module.build(original,root/'anchored')
                self.assertFalse((root/'anchored').exists())


if __name__=='__main__':unittest.main()
