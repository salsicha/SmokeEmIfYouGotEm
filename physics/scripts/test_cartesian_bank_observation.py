import unittest
from prepare_cartesian_snapshot_restart import validate_bank_observation


class BankObservationTest(unittest.TestCase):
    def test_default_same_step_and_explicit_later(self):
        audit=dict(input_manifest_sha256='input', h_sha256='state', step=2000)
        validate_bank_observation(audit,'input',2000,'state')
        with self.assertRaises(AssertionError):
            validate_bank_observation(audit,'input',0,'state')
        validate_bank_observation(audit,'input',0,'state',True)

    def test_later_flag_does_not_relax_provenance_or_allow_older_observation(self):
        audit=dict(input_manifest_sha256='input', h_sha256='state', step=2000)
        for manifest, step, state in (('other',0,'state'),('input',0,'wrong'),('input',4000,'state')):
            with self.assertRaises(AssertionError):
                validate_bank_observation(audit,manifest,step,state,True)


if __name__ == '__main__':
    unittest.main()
