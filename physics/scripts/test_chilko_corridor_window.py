import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np

from mosaic_lidarbc_crops import sha
from verify_chilko_corridor_window import verify


class WindowVerificationTests(unittest.TestCase):
    def fixture(self,root):
        full,window=root/'full',root/'window'
        result={}
        for folder,cols,start,is_full in ((full,5,0,True),(window,3,2,False)):
            (folder/'scenario').mkdir(parents=True)
            (folder/'source.txt').write_text('unchanged source')
            h=np.ones((3,cols))
            np.savez_compressed(folder/'scenario/initial_state.npz',depth=h,eta=100+h)
            b=dict(full_route_hydraulic_inputs=is_full,continuous_terrain=dict(manifest_sha256='same'))
            r=dict(station=np.arange(cols)*2.+start,channel=np.ones((3,cols),bool),lateral=np.arange(3)*2.)
            result[folder]=(b,dict(grid=dict(nx=cols,ny=3)),dict(chart='same'),None,
                            np.full((3,cols),100.),r,{'source.txt':sha(folder/'source.txt')})
        return full,window,result

    def test_exact_slice_passes_without_claiming_engine_or_hydraulics(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);full,window,data=self.fixture(root)
            with patch('verify_chilko_corridor_window.read_inputs',side_effect=lambda p:data[p]):
                result=verify(full,window,root/'result.json')
            self.assertTrue(result['local_initial_state_and_reference_exact_full_slice'])
            self.assertFalse(result['engine_validated']);self.assertFalse(result['hydraulic_solution'])
            self.assertEqual(result['initial_point_clearance']['deficient_sections'],[])
            self.assertEqual(result,json.loads((root/'result.json').read_text()))

    def test_changed_bed_reference_chart_or_initial_state_refused(self):
        for field in ('bed','reference','chart','initial'):
            with self.subTest(field=field), tempfile.TemporaryDirectory() as directory:
                root=Path(directory);full,window,data=self.fixture(root)
                if field=='bed':data[window][4][0,0]+=1.
                elif field=='reference':data[window][5]['channel'][0,0]=False
                elif field=='chart':data[window][2]['chart']='different'
                else:np.savez_compressed(window/'scenario/initial_state.npz',depth=np.zeros((3,3)),eta=np.ones((3,3))*101)
                with patch('verify_chilko_corridor_window.read_inputs',side_effect=lambda p:data[p]):
                    with self.assertRaises((AssertionError,ValueError)):verify(full,window,root/'result.json')
                self.assertFalse((root/'result.json').exists())

    def test_clearance_diagnostic_does_not_turn_into_false_source_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);full,window,data=self.fixture(root)
            h=np.ones((3,5));h[0,2]=.1
            np.savez_compressed(full/'scenario/initial_state.npz',depth=h,eta=100+h)
            np.savez_compressed(window/'scenario/initial_state.npz',depth=h[:,1:4],eta=100+h[:,1:4])
            with patch('verify_chilko_corridor_window.read_inputs',side_effect=lambda p:data[p]):
                data[full][5]['evidence_station']=np.arange(5)*2.+100
                data[window][5]['evidence_station']=np.arange(3)*2.+102
                result=verify(full,window,root/'result.json')
            self.assertEqual(len(result['initial_point_clearance']['deficient_sections']),1)
            self.assertTrue(result['local_initial_state_and_reference_exact_full_slice'])


if __name__=='__main__':unittest.main()
