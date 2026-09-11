from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from liquid_reconstruction_layout import from_report


class ReconstructionLayoutTest(unittest.TestCase):
    def test_legacy_reports_unchanged(self):
        self.assertEqual(from_report({})['half'],[1050.,1050.])
        self.assertTrue(from_report({})['legacy'])

    def test_actual_tail_preserves_rectangle_and_metric(self):
        layout=from_report(dict(solver_cells=[110,38,24],render_cells=[220,76,48],computational_extents_cm=[5500,1900,800]))
        self.assertEqual(layout['half'],[2650.,850.])
        self.assertEqual(layout['render'],[220,76,48])

    def test_rejects_incomplete_truncated_oversized_or_odd_layout(self):
        for report in [dict(solver_cells=[68,68,24]),
            dict(solver_cells=[110,38,24],render_cells=[220,76,47],computational_extents_cm=[5500,1900,800]),
            dict(solver_cells=[494,166,24],render_cells=[988,332,48],computational_extents_cm=[24700,8300,800]),
            dict(solver_cells=[111,38,24],render_cells=[222,76,48],computational_extents_cm=[5500,1900,800])]:
            with self.assertRaises(ValueError): from_report(report)


if __name__=='__main__': unittest.main()
