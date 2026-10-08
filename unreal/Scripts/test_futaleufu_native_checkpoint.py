import copy
import unittest
import numpy as np
from resume_futaleufu_native_checkpoint import require_terminal_audit, exact_state


class NativeCheckpointTests(unittest.TestCase):
    def test_only_terminal_independent_route_audit_is_eligible(self):
        audit = dict(schema='raftsim.futaleufu_native_continuation_audit.v1', terminal_run_audited=True,
                     errors=[], numerical_geographic_checks_passed=True,
                     frames=[dict(common_original_route_components=[1], dry_cross_sections=[], wet_closed_exterior_faces=[])])
        self.assertEqual(require_terminal_audit(audit), audit['frames'][-1])
        for change in (dict(terminal_run_audited=False), dict(errors=['failed']), dict(frames=[]),
                       dict(numerical_geographic_checks_passed=False)):
            with self.assertRaises(ValueError): require_terminal_audit({**audit, **change})
        for field in ('dry_cross_sections', 'wet_closed_exterior_faces'):
            bad = copy.deepcopy(audit); bad['frames'][0][field] = [dict(failure=True)]
            with self.assertRaises(ValueError): require_terminal_audit(bad)

    def test_restart_state_is_checked_not_clipped_or_filled(self):
        h, u, v = [np.ones((2, 2)) for _ in range(3)]
        exact_state(h, u, v, (2, 2))
        for bad in (np.full((2, 2), -1.), np.full((2, 2), 11.), np.full((2, 2), np.nan), np.ones((1, 2))):
            with self.assertRaises(ValueError): exact_state(bad, u, v, (2, 2))
        with self.assertRaises(ValueError): exact_state(h, u*21, v, (2, 2))
        np.testing.assert_array_equal(h, np.ones((2, 2)))


if __name__ == '__main__': unittest.main()
