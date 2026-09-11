import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from audit_liquid_native_compact import verify_summary


class CompactNativeTest(unittest.TestCase):
    def setUp(self):
        self.plans = {2:{0:0,1:1},3:{0:0,1:1}}
        self.history = []
        for step, n, retired in ((2,4,0),(3,3,2)):
            e = [0]*60;e[7*5+1] = retired;e[7*5+4] = retired
            self.history.append(dict(native_step=step, issued=True, full_audit_retained=False,
                                     retained_summary_bytes=304, control=[1,0,n+retired,retired],
                                     counts=[n]+[0]*11,exit_counts=e))

    def test_births_and_exits_balance(self):
        live, exits = verify_summary(self.history,self.plans,3)
        self.assertEqual(live,3);self.assertEqual(exits[7,1],2)

    def test_invalid_gate_and_lost_water_rejected(self):
        for key in ('control','counts','exit_counts'):
            h=copy.deepcopy(self.history);h[1][key][0]+=1
            with self.assertRaises(ValueError):verify_summary(h,self.plans,3)

    def test_skipped_step_or_missing_summary_rejected(self):
        for key, value in (('native_step',4),('issued',False),('retained_summary_bytes',0),('full_audit_retained',True)):
            h=copy.deepcopy(self.history);h[1][key]=value
            with self.assertRaises(ValueError):verify_summary(h,self.plans,3)


if __name__ == '__main__':unittest.main()
