"""Do not mistake CSV overhead or absent instrumentation for solver cost."""
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from compare_south_fork_solver_optimization import reported_timings


class BenchmarkTimingTests(unittest.TestCase):
    def test_old_binary_has_unavailable_not_zero_timings(self):
        self.assertEqual(reported_timings('steps=100\nvalidation_passed=true\n'),{})

    def test_separate_solve_and_export(self):
        self.assertEqual(reported_timings('solve_and_capture_seconds=1.25\nexport_seconds=3.5\n'),
            {'solve_and_capture_seconds':1.25,'export_seconds':3.5})

    def test_invalid_and_duplicate_timings_rejected(self):
        for value in ('nan','inf','-1','bad'):
            with self.subTest(value=value),self.assertRaises(ValueError):
                reported_timings('solve_and_capture_seconds='+value)
        with self.assertRaises(ValueError):
            reported_timings('export_seconds=1\nexport_seconds=2\n')


if __name__=='__main__':unittest.main()
