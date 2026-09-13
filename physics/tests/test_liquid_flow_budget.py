import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from diagnose_liquid_flow_budget import budget


class FlowBudgetTest(unittest.TestCase):
    def data(self):
        plan={1:{0:100},2:{0:3},3:{0:2},4:{0:3}}
        rows=[];live=100
        for step,outgoing in [(2,1),(3,4),(4,0)]:
            n=live+sum(plan[step].values());live=n-outgoing
            exits=[0]*60;exits[1]=exits[4]=outgoing
            rows.append(dict(native_step=step,issued=True,full_audit_retained=False,retained_summary_bytes=304,
                control=[1,0,n,outgoing],counts=[live]+[0]*11,exit_counts=exits))
        return rows,plan

    def test_exact_storage_and_interval_balance(self):
        rows,plan=self.data();r=budget(rows,plan,100,.25,.5)
        self.assertEqual(r['survivors_after_last_verified_commit'],103)
        self.assertEqual(r['verified_births'],8);self.assertEqual(r['approved_exit_count'],5)
        self.assertEqual(r['nominal_storage_change_m3'],.75)
        self.assertEqual(len(r['intervals']),2)
        self.assertEqual(r['intervals'][0]['nominal_storage_change_m3'],0)
        self.assertTrue(r['full_recorded_commit_sequence_verified'])
        self.assertFalse(r['physical_discharge_or_steady_flow_acceptance'])

    def test_failure_preserved_later_success_not_counted(self):
        rows,plan=self.data();rows[1]['control']=[0,64,104,4]
        r=budget(rows,plan,100,.25,.5)
        self.assertEqual(r['first_failed_native_step'],3)
        self.assertEqual(r['verified_compact_commits'],1)
        self.assertEqual(r['survivors_after_last_verified_commit'],102)
        self.assertFalse(r['full_recorded_commit_sequence_verified'])

    def test_invalid_pre_failure_accounting_rejected(self):
        rows,plan=self.data();rows[0]['counts'][0]+=1
        with self.assertRaises(ValueError):budget(rows,plan,100,.25,.5)

    def test_initial_failure_never_claims_a_verified_interval(self):
        rows,plan=self.data();rows[0]['control']=[0,64,103,1]
        r=budget(rows,plan,100,.25,.5)
        self.assertEqual(r['intervals'],[]);self.assertEqual(r['verified_compact_commits'],0)

    def test_invalid_units_rejected(self):
        rows,plan=self.data()
        for v,dt in [(0,.1),(.25,0),(.25,float('nan')),(-1,.1)]:
            with self.assertRaises(ValueError):budget(rows,plan,100,v,dt)


if __name__=='__main__':unittest.main()
