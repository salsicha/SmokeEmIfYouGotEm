import sys
from pathlib import Path
import unittest
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from audit_liquid_stage_order import compare


class StageOrderTest(unittest.TestCase):
    def fixture(self,substeps=1):
        count=714*substeps
        ages=np.r_[np.linspace(.1,12,count+1),np.full(35,12)]
        delta=np.r_[0,np.diff(ages)]
        capture=dict(simulation_steps=720,simulation_substeps_per_frame=substeps,complete=True,
                     error=None,secondary_current_surface_compiled=True)
        report=dict(secondary_first_stage_events=count,reconstruction_before_secondary_updates=count,
                    updates_with_simulation_tick=count,gpu_update_count=len(ages),current_surface_before_secondary=True,
                    error='',diagnostics=[0]*4,max_secondary_steps_per_graph=substeps)
        return capture,report,np.stack((ages,delta,np.zeros_like(ages),(delta>0).astype(float)),axis=-1)

    def test_all_steps_and_batched_history(self):
        for substeps in (1,2):
            c,r,t=self.fixture(substeps);result=compare(c,r,t,12.)
            self.assertTrue(result['scheduling_verified'])
            self.assertEqual(result['batched_graph_history_exercised'],substeps==2)

    def test_missing_first_stage_not_accepted(self):
        c,r,t=self.fixture();del r['secondary_first_stage_events']
        self.assertFalse(compare(c,r,t,12.)['scheduling_verified'])

    def test_recorded_ticks_cannot_conceal_skipped_steps(self):
        c,r,t=self.fixture();r['updates_with_simulation_tick']-=1;r['reconstruction_before_secondary_updates']-=1
        self.assertFalse(compare(c,r,t,12.)['scheduling_verified'])

    def test_coalesced_gpu_time_rejected_despite_valid_total_age(self):
        c,r,t=self.fixture();t[50,0]=t[49,0];t[:,1]=np.r_[0,np.diff(t[:,0])]
        self.assertFalse(compare(c,r,t,12.)['gpu_per_step_clock_verified'])

    def test_pause_compilation_and_validation_required(self):
        c,r,t=self.fixture()
        self.assertFalse(compare(c,r,t,12.,['RHI error'])['scheduling_verified'])
        self.assertFalse(compare(dict(c,secondary_current_surface_compiled=False),r,t,12.)['scheduling_verified'])
        t[-1,0]+=.001;t[-1,1]=.001
        self.assertFalse(compare(c,r,t,12.)['gpu_per_step_clock_verified'])

    def test_two_steps_must_actually_share_graph_for_batched_claim(self):
        c,r,t=self.fixture(2);r['max_secondary_steps_per_graph']=1
        result=compare(c,r,t,12.)
        self.assertTrue(result['scheduling_verified'])
        self.assertFalse(result['batched_graph_history_exercised'])

    def test_invalid_clock_and_schedule(self):
        c,r,t=self.fixture()
        with self.assertRaises(ValueError):compare(c,r,[[float('nan')]*4]*2,12.)
        with self.assertRaises(ValueError):compare(dict(c,simulation_steps=0),r,t,12.)


if __name__=='__main__':unittest.main()
