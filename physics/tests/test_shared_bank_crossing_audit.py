"""Reject unsafe stored GPU crossings without introducing a depth tolerance."""
import importlib.util
from pathlib import Path
import unittest

SCRIPT = Path(__file__).parents[1] / "scripts" / "audit_shared_bank_crossing.py"
SPEC = importlib.util.spec_from_file_location("shared_bank_audit", SCRIPT)
AUDIT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUDIT)


class SharedBankCrossingAuditTests(unittest.TestCase):
    def case(self, **changes):
        item = dict(wet_position_cm="0", dry_position_cm="100", wet_bed_m="0",
                    dry_bed_m="2", depth_m="1", position_cm="50", fraction="0.5",
                    retreat_bound_cm="0", width_cm="0.1")
        item.update(changes)
        return item

    def test_exact_root(self):
        self.assertEqual(AUDIT.audit_case(self.case())["exact_nonnegative_depth_m"], "0")

    def test_negative_direction(self):
        AUDIT.audit_case(self.case(dry_position_cm="-100", position_cm="-50"))

    def test_wet_retreat(self):
        p = 49.9375
        AUDIT.audit_case(self.case(position_cm=str(p), fraction=str(p / 100), retreat_bound_cm="0.0625"))

    def test_dry_point_rejected(self):
        with self.assertRaisesRegex(ValueError, "physically dry"):
            AUDIT.audit_case(self.case(position_cm="50.0625", fraction="0.500625"))

    def test_double_only_coordinate_rejected(self):
        with self.assertRaisesRegex(ValueError, "GPU conversion"):
            AUDIT.audit_case(self.case(position_cm="49.99999999999999"))

    def test_band_violation_rejected(self):
        with self.assertRaisesRegex(ValueError, "retreat"):
            AUDIT.audit_case(self.case(position_cm="49", fraction="0.49", retreat_bound_cm="1"))

    def test_false_bound_rejected(self):
        with self.assertRaisesRegex(ValueError, "retreat"):
            AUDIT.audit_case(self.case(position_cm="49.9375", fraction="0.499375"))

    def test_attribute_mismatch_rejected(self):
        with self.assertRaisesRegex(ValueError, "Attribute fraction"):
            AUDIT.audit_case(self.case(fraction="0.49999"))

    def test_nonfinite_rejected(self):
        with self.assertRaisesRegex(ValueError, "Nonfinite"):
            AUDIT.audit_case(self.case(depth_m="NaN"))

    def test_zero_donor_rejected(self):
        with self.assertRaisesRegex(ValueError, "Invalid high-bank"):
            AUDIT.audit_case(self.case(depth_m="0"))

    def test_outside_original_edge_rejected(self):
        with self.assertRaisesRegex(ValueError, "outside original edge"):
            AUDIT.audit_case(self.case(position_cm="-1"))

    def test_binary32_overflow_rejected(self):
        with self.assertRaisesRegex(ValueError, "Unrepresentable GPU"):
            AUDIT.audit_case(self.case(wet_position_cm="1e100"))


if __name__ == "__main__":
    unittest.main()
