import copy
import unittest
from recover_futaleufu_native_checkpoint import recovery_checkpoint, INTERRUPTIONS
from resume_futaleufu_native_checkpoint import require_terminal_audit


class InterruptedRecovery(unittest.TestCase):
    def fixture(self):
        frames=[dict(step=step,time_seconds=32+step*.01,common_original_route_components=[1],
            dry_cross_sections=[],wet_closed_exterior_faces=[],arrays_sha256={k:'a'*64 for k in ('h','u','v')})
            for step in (0,3000)]
        return [dict(schema='raftsim.futaleufu_native_continuation_audit.v1',producer_outcome='interrupted',
                    terminal_run_audited=False,restart_authorized=False,errors=[],
                    numerical_geographic_checks_passed=True,frames=frames),
                dict(failure=sorted(INTERRUPTIONS)[0],exit_code=1),
                dict(steps=30000,command=['solver','source','output','30000','3000','4'],
                     source_time_seconds=32.,target_time_seconds=332.,dt_seconds=.01),
                dict(initial_time_seconds=32.,dt_seconds=.01),[0,3000]]

    def test_uses_latest_complete_audited_state_without_mutating_failure(self):
        values=self.fixture();before=copy.deepcopy(values)
        self.assertEqual(recovery_checkpoint(*values)['step'],3000)
        self.assertEqual(values,before)
        with self.assertRaises(ValueError):require_terminal_audit(values[0])

    def test_never_relabels_failed_or_incomplete_evidence(self):
        for key,value in (('producer_outcome','completed'),('terminal_run_audited',True),
                          ('restart_authorized',True),('errors',['flooded bank']),
                          ('numerical_geographic_checks_passed',False)):
            values=self.fixture();values[0][key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):recovery_checkpoint(*values)
        for reason in ('Native state gate failed','nonfinite water','',None):
            values=self.fixture();values[1]['failure']=reason
            with self.assertRaises(ValueError):recovery_checkpoint(*values)
        values=self.fixture();values[1]['exit_code']=0
        with self.assertRaises(ValueError):recovery_checkpoint(*values)

    def test_missing_extra_and_unaudited_later_snapshots_refused(self):
        for complete in ([],[3000],[0,6000],[0,3000,6000]):
            values=self.fixture();values[-1]=complete
            with self.assertRaises(ValueError):recovery_checkpoint(*values)

    def test_each_snapshot_retains_clock_route_and_array_checks(self):
        for index in (0,1):
            for key,value in (('time_seconds',float('nan')),('time_seconds',100.),
                              ('common_original_route_components',[]),('dry_cross_sections',[4]),
                              ('wet_closed_exterior_faces',[5]),('arrays_sha256',{'h':'a'*64})):
                values=self.fixture();values[0]['frames'][index][key]=value
                with self.subTest(index=index,key=key),self.assertRaises(ValueError):recovery_checkpoint(*values)


if __name__=='__main__':unittest.main()
