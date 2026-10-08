import copy
import json
from pathlib import Path
import tempfile
import unittest

from audit_futaleufu_native_snapshots import snapshot_schedule,completed_prefix,producer_outcome
from resume_futaleufu_native_checkpoint import require_terminal_audit


class NativeSnapshotSchedule(unittest.TestCase):
    def request(self,steps):
        return dict(command=['native.exe','input.json','native',str(steps),str(steps//10),'4'],
            steps=steps,dt_seconds=.01,source_time_seconds=32.)

    def test_both_actual_native_schedules(self):
        for steps in (3000,30000):
            request=self.request(steps)
            self.assertEqual(snapshot_schedule(request,dict(dt_seconds=.01,initial_time_seconds=32.)),list(range(0,steps+1,steps//10)))

    def test_long_request_interval_and_clock_are_not_short_run_defaults(self):
        manifest=dict(dt_seconds=.01,initial_time_seconds=32.)
        request=self.request(30000);request.update(snapshot_interval_steps=3000,target_time_seconds=332.)
        self.assertEqual(snapshot_schedule(request,manifest)[-1],30000)
        for key,value in [('snapshot_interval_steps',300),('target_time_seconds',62.),('steps',True),
                          ('source_time_seconds',2.),('dt_seconds',.02),('target_time_seconds',float('nan'))]:
            bad=copy.deepcopy(request);bad[key]=value
            with self.assertRaises(ValueError):snapshot_schedule(bad,manifest)
        bad=copy.deepcopy(request);bad['command'][4]='300'
        with self.assertRaises(ValueError):snapshot_schedule(bad,manifest)

    def frames(self,root,steps):
        for step in steps:
            folder=root/('frame_%06d'%step);folder.mkdir()
            (folder/'complete.json').write_text('{}')

    def test_interrupted_prefix_is_not_complete_run(self):
        with tempfile.TemporaryDirectory() as name:
            root=Path(name);self.frames(root,[0,3000])
            expected=list(range(0,30001,3000))
            self.assertEqual(completed_prefix(root,expected,False),[0,3000])
            with self.assertRaises(ValueError):completed_prefix(root,expected,True)
            (root/'frame_006000').mkdir() # Incomplete snapshot is never invented.
            self.assertEqual(completed_prefix(root,expected,False),[0,3000])

    def test_missing_or_unexpected_complete_frame_refused(self):
        for steps in ([3000],[0,6000],[0,300]):
            with tempfile.TemporaryDirectory() as name:
                root=Path(name);self.frames(root,steps)
                with self.assertRaises(ValueError):completed_prefix(root,[0,3000,6000],False)

    def test_terminal_receipts_are_exclusive_and_preserved(self):
        with tempfile.TemporaryDirectory() as name:
            root=Path(name)
            with self.assertRaises(ValueError):producer_outcome(root)
            (root/'failure.json').write_text(json.dumps(dict(failure='Shared engine appeared',exit_code=1)))
            self.assertEqual(producer_outcome(root)[0],'interrupted')
            (root/'completed.json').write_text(json.dumps(dict(exit_code=0,native_restart_fields_and_clock_exact=True)))
            with self.assertRaises(ValueError):producer_outcome(root)

    def test_interrupted_audit_does_not_bypass_runtime_or_restart_gate(self):
        report=dict(schema='raftsim.futaleufu_native_continuation_audit.v1',producer_outcome='interrupted',
            terminal_run_audited=False,numerical_geographic_checks_passed=True,errors=[],frames=[dict(step=3000)])
        with self.assertRaises(ValueError):require_terminal_audit(report)


if __name__=='__main__':unittest.main()
