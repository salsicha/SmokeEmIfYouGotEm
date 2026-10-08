import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import numpy as np

import refine_colorado_terminal_bend as module
from anchor_colorado_terminal_frame import anchor_terminal,source_end_caps
from build_colorado_shared_hydraulic_frame import shared_frame,select_window
from build_colorado_catalog_evidence import sha


class TerminalBend(unittest.TestCase):
    def fixture(self):
        rows=[dict(easting=1000+s,northing=2000+50*np.exp(-((s-4300)/90)**2)) for s in np.arange(0,5000,10.)]
        arrays,receipt=anchor_terminal(shared_frame(rows),rows)
        return rows,arrays,receipt

    def test_prefix_endpoint_and_source_immutability(self):
        rows,old,_=self.fixture();saved=copy.deepcopy(old)
        new,receipt=module.refine(old,1200.,90.)
        for key in old:
            np.testing.assert_array_equal(old[key],saved[key])
            np.testing.assert_array_equal(new[key][:receipt['unchanged_prefix_points']],old[key][:receipt['unchanged_prefix_points']])
        np.testing.assert_array_equal(new['east_north_m'][-1],old['east_north_m'][-1])
        np.testing.assert_array_equal(new['normal_east_north'][-1],old['normal_east_north'][-1])
        self.assertEqual(new['source_global_station_m'][-1],source_end_caps(rows)['stations'][-1])
        self.assertTrue((np.diff(new['source_global_station_m'])>0).all())
        self.assertTrue((np.diff(new['station_m'])==2).all())
        self.assertGreater(receipt['maximum_numerical_axis_displacement_m'],1.)
        self.assertFalse(receipt['terrain_modified'])

    def test_shared_overlaps_remain_exact(self):
        _,old,_=self.fixture();new,_=module.refine(old,1200.,90.)
        windows=[select_window(new,dict(schema='raftsim.colorado_continuous_source_window.v1',source_halo_interval_m=interval)) for interval in ([3300,4400],[4100,4990])]
        _,first,second=np.intersect1d(windows[0][0],windows[1][0],return_indices=True)
        for k in range(4):np.testing.assert_array_equal(windows[0][k][first],windows[1][k][second])

    def test_invalid_configuration_and_arrays_refused(self):
        _,old,_=self.fixture()
        for window,sigma in ((599,90),(1201,90),(3002,90),(600,300),(1200,60),(1200,float('nan')),(float('inf'),90)):
            with self.subTest(window=window,sigma=sigma),self.assertRaises(ValueError):module.refine(old,window,sigma)
        for key in old:
            bad=copy.deepcopy(old);bad[key][-1]=np.nan
            with self.assertRaises(ValueError):module.refine(bad,1200,90)

    def disk_fixture(self,root):
        rows,old,anchor=self.fixture();original=root/'original';original.mkdir()
        source=root/'source.csv';source.write_text('fixture source identity\n')
        np.savez_compressed(original/'frame.npz',**old)
        (original/'coordinate_map.json').write_text(json.dumps(dict(horizontal_origin_epsg6404_m=[1000,2000],mapping_policy='fixture')))
        manifest=dict(schema='raftsim.colorado_shared_hydraulic_frame.v1',source_endpoint_anchor=anchor,
            source_profile='source.csv',source_profile_sha256=sha(source),limitations=[],
            files_sha256={n:sha(original/n) for n in ('frame.npz','coordinate_map.json')})
        (original/'manifest.json').write_text(json.dumps(manifest))
        return rows,original

    def test_build_preserves_endpoint_and_binds_parent(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);rows,original=self.disk_fixture(root)
            with patch.object(module,'ROOT',root),patch.object(module,'read_profile',return_value=rows):
                result=module.build(original,root/'new')
                self.assertFalse(result['runtime_ready'])
                self.assertEqual(result['terminal_bend_refinement']['parent_manifest_sha256'],sha(original/'manifest.json'))
                for n,h in result['files_sha256'].items():self.assertEqual(sha(root/'new'/n),h)
                with self.assertRaisesRegex(ValueError,'Fresh'):module.build(original,root/'new')
                with self.assertRaisesRegex(ValueError,'without a terminal-bend'):module.build(root/'new',root/'again')

    def test_changed_source_and_terminal_anchor_refused(self):
        for kind in ('source','frame','caps'):
            with self.subTest(kind=kind),tempfile.TemporaryDirectory() as directory:
                root=Path(directory);rows,original=self.disk_fixture(root)
                if kind=='source':(root/'source.csv').write_text('changed')
                elif kind=='frame':(original/'frame.npz').write_bytes(b'changed')
                else:
                    p=original/'manifest.json';m=json.loads(p.read_text());m['source_endpoint_anchor']['source_end_caps']['positions'][-1][0]+=1;p.write_text(json.dumps(m))
                with patch.object(module,'ROOT',root),patch.object(module,'read_profile',return_value=rows):
                    with self.assertRaises(ValueError):module.build(original,root/'new')
                self.assertFalse((root/'new').exists())


if __name__=='__main__':unittest.main()
