import copy
import sys
import unittest
import tempfile
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from diagnose_liquid_first_rejection import decode, json_safe, controls, captured_frame_precision


class FirstRejectionTest(unittest.TestCase):
    def record(self):
        return dict(schema='raftsim.liquid_exit_first_rejection.v1',simulation_generation='test',retained_bytes=1280,words=[0]*320)

    def test_unclaimed_buffer_must_be_entirely_clear(self):
        r=self.record();self.assertFalse(decode(r,'test')['captured'])
        r['words'][100]=7
        with self.assertRaises(ValueError):decode(r,'test')

    def test_full_payload_and_trace_step_are_preserved(self):
        r=self.record();w=r['words'];w[:9]=[15,1,7,24,8,7,2,0,3]
        w[12:15]=[100,90,4]
        w[64:70]=np.asarray([1,2,3,4,5,6],dtype='<f4').view('<u4').tolist()
        w[70:73]=[0x7fc01234,16777217,0x80000001]
        d=decode(r,'test');self.assertEqual(d['native_step'],15)
        self.assertEqual(d['end_cm'],[1,2,3]);self.assertEqual(d['start_cm'],[4,5,6])
        self.assertEqual(d['payload_words'][-3:],w[70:73])

    def test_stale_truncated_noninteger_and_bad_layout_rejected(self):
        r=self.record();r['words'][:9]=[15,1,7,24,8,7,2,0,3];r['words'][12:15]=[100,90,4]
        cases=[]
        for key,value in [('simulation_generation','old'),('retained_bytes',64),('schema','unknown')]:
            bad=copy.deepcopy(r);bad[key]=value;cases.append(bad)
        for index,value in [(3,101),(4,128),(5,129),(8,0),(20,1.5)]:
            bad=copy.deepcopy(r);bad['words'][index]=value;cases.append(bad)
        bad=copy.deepcopy(r);bad['words'].pop();cases.append(bad)
        for bad in cases:
            with self.assertRaises(ValueError):decode(bad,'test')

    def test_nonfinite_debug_values_have_valid_json_representation(self):
        self.assertEqual(json_safe({'point':[1.,float('nan'),float('inf')]}),{'point':[1.,None,None]})
        self.assertIs(type(json_safe(np.int64(224))),int)

    def test_full_and_compact_controls_preserve_actual_failure(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);dest=root/'commit-1'/'handoff-receiving';dest.mkdir(parents=True)
            np.array([0,64,123,4],dtype='<u4').tofile(dest/'assembly-control.bin')
            history=[dict(native_step=2,full_audit_retained=False,control=[1,0,120,0]),
                     dict(native_step=3,full_audit_retained=True,snapshot_directory='commit-1',
                          receiving=dict(control='assembly-control.bin'))]
            self.assertEqual(controls(root,history),[dict(native_step=2,control=[1,0,120,0]),dict(native_step=3,control=[0,64,123,4])])

    def test_full_control_truncation_and_path_escape_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);dest=root/'commit-1'/'handoff-receiving';dest.mkdir(parents=True)
            np.array([0,64,123],dtype='<u4').tofile(dest/'assembly-control.bin')
            h=dict(native_step=3,full_audit_retained=True,snapshot_directory='commit-1',receiving=dict(control='assembly-control.bin'))
            with self.assertRaises(ValueError):controls(root,[h])
            h['snapshot_directory']='../elsewhere'
            with self.assertRaises(ValueError):controls(root,[h])

    def test_malformed_compact_controls_rejected(self):
        for values in ([1,0,20],[1,0,20,-1],[True,0,20,0],[1,0,20,2**32]):
            with self.assertRaises(ValueError):controls(Path('.'),[dict(native_step=2,full_audit_retained=False,control=values)])

    def test_actual_reservoir_frame_distinguishes_arithmetic_loss(self):
        r=dict(gpu_lower_world_cm=[12080.8720703125,312.3059387207031,350],
            gpu_axis_x=[-.929999828338623,-.36755993962287903,0],
            gpu_axis_y=[-.36755993962287903,.929999828338623,0],
            start_cm=[-12066.3134765625,-5790.4296875,647.559814453125],
            end_cm=[-12066.314453125,-5790.42822265625,647.55767822265625],
            gpu_local_start_cm=[24700,3199.994873046875,297.559814453125],
            gpu_local_end_cm=[24700.001953125,3199.9970703125,297.55767822265625])
        result=captured_frame_precision(r)
        self.assertFalse(result['gpu_matches_single_rounding'])
        self.assertLess(result['exact_captured_frame_endpoints_cm'][1][0],24700)
        self.assertEqual(result['rounded_captured_frame_endpoints_cm'][1][0],24700)
        self.assertGreater(result['gpu_arithmetic_error_cm'][1][0],.0019)
        self.assertFalse(result['acceptance'])
        r['gpu_local_start_cm'],r['gpu_local_end_cm']=result['rounded_captured_frame_endpoints_cm']
        self.assertTrue(captured_frame_precision(r)['gpu_matches_single_rounding'])

    def test_captured_frame_shape_is_not_broadcast(self):
        with self.assertRaises((ValueError,KeyError)):
            captured_frame_precision(dict(gpu_lower_world_cm=[0],gpu_axis_x=[1,0,0],
                gpu_axis_y=[0,1,0],start_cm=[0,0,0],end_cm=[1,1,1],
                gpu_local_start_cm=[0,0,0],gpu_local_end_cm=[1,1,1]))


if __name__=='__main__':unittest.main()
