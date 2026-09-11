import copy
import sys
import unittest
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from audit_liquid_native_restart import verify_generation, verify_distinct_generations


class NativeRestartTest(unittest.TestCase):
    def report(self):
        generation = str(uuid4())
        groups = [dict(simulation_generation=generation, complete=True, aligned=True,
                       entries=[dict(owner=o, first=True, reset=s==0, native_rate_spawns=int(o==1), native_event_spawns=0)
                                for o in range(12)]) for s in range(3)]
        return dict(simulation_generation=generation, native_lifetime_failed=False, native_lifetime_steps=3,
                    native_lifetime_births=[0,3]+[0]*10, groups=groups,
                    native_transfer_packet=[dict(simulation_generation=generation)],
                    native_particle_handoff_history=[dict(simulation_generation=generation)])

    def test_two_fresh_generations_allow_reused_local_sequences(self):
        self.assertEqual(len(verify_distinct_generations([self.report(),self.report()])), 2)

    def test_same_generation_cannot_masquerade_as_restart(self):
        r = self.report()
        with self.assertRaisesRegex(ValueError, 'distinct'):
            verify_distinct_generations([r,copy.deepcopy(r)])

    def test_case_change_is_not_a_new_generation(self):
        r = self.report();s = copy.deepcopy(r)
        upper = s['simulation_generation'].upper();s['simulation_generation'] = upper
        for item in s['native_transfer_packet']+s['native_particle_handoff_history']+s['groups']:
            item['simulation_generation'] = upper
        with self.assertRaisesRegex(ValueError, 'distinct'):
            verify_distinct_generations([r,s])

    def test_stale_particle_transfer_or_stage_rejected(self):
        for key in ('native_transfer_packet','native_particle_handoff_history','groups'):
            r = self.report();r[key][0]['simulation_generation'] = str(uuid4())
            with self.assertRaisesRegex(ValueError, 'Stale'):
                verify_generation(r)

    def test_unexpected_native_reset_rejected(self):
        r = self.report();r['groups'][1]['entries'][2]['reset'] = True
        with self.assertRaisesRegex(ValueError, 'Unexpected reset'):
            verify_generation(r)

    def test_birth_step_and_failed_state_mismatch_rejected(self):
        for key, value in (('native_lifetime_steps',4), ('native_lifetime_births',[0]*12), ('native_lifetime_failed',True)):
            r = self.report();r[key] = value
            with self.assertRaises(ValueError):
                verify_generation(r)


if __name__ == '__main__':
    unittest.main()
