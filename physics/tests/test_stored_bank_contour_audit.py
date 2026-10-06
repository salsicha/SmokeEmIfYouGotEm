"""Exact stored-world geometry audit controls; no Unreal process required."""
import copy
from fractions import Fraction as F
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))
from audit_stored_bank_contour import audit_case
from three_wet_bank_envelope import value


class StoredBankContourAuditTests(unittest.TestCase):
    def case(self):
        return dict(bed=["2", "0", "0", "0"], depth=["0", "1", "1", "1"],
                    origin_cm=["0", "0"], render_origin_cm=["0", "0"], end_cm=["0.125", "0.125"], width_cm="0.1",
                    boundary_buffer_cm=[["0.09375", "0"], ["0", "0.09375"]],
                    inner_local=[["0.25", "0"], ["0", "0.25"]],
                    polygon_buffer_cm=[["0.125", "0.125"], ["0.125", "0"],
                                      ["0.09375", "0"], ["0", "0.09375"], ["0", "0.125"]],
                    triangles=[[0, 1, 2], [0, 2, 3], [0, 3, 4]])

    def test_positive_full_certificate(self):
        report = audit_case(self.case())
        self.assertTrue(report["whole_gpu_geometry_certified"])
        self.assertEqual(report["triangles"], 3)
        self.assertEqual(report["exact_maximum_band_cm"], "1/16")

    def test_reflected_map(self):
        c = self.case()
        for key in ("end_cm",):
            c[key][0] = str(-float(c[key][0]))
        for key in ("boundary_buffer_cm", "polygon_buffer_cm"):
            for p in c[key]:
                p[0] = str(-float(p[0]))
        self.assertTrue(audit_case(c)["whole_gpu_geometry_certified"])

    def test_nonradial_witness_still_requires_complete_partition(self):
        c = self.case()
        c["boundary_buffer_cm"].insert(1, ["0.0625", "0.0625"])
        c["polygon_buffer_cm"].insert(3, ["0.0625", "0.0625"])
        c["inner_local"].insert(1, ["0.1", "0.3"])
        c["triangles"] = [[0, 1, 2], [0, 2, 3], [0, 3, 4], [0, 4, 5]]
        self.assertTrue(audit_case(c)["whole_gpu_geometry_certified"])

    def test_inner_boundary_must_close_on_cell_axes(self):
        c = self.case()
        c["inner_local"][0][1] = "0.01"
        with self.assertRaisesRegex(ValueError, "Inner boundary"):
            audit_case(c)

    def test_exact_render_translation(self):
        c = self.case()
        c["origin_cm"] = ["10000000", "-10000000"]
        c["end_cm"] = ["10000000.125", "-9999999.875"]
        c["render_origin_cm"] = copy.copy(c["origin_cm"])
        self.assertTrue(audit_case(c)["whole_gpu_geometry_certified"])

    def test_missing_render_translation_rejected(self):
        c = self.case()
        c["origin_cm"] = ["10000000", "-10000000"]
        c["end_cm"] = ["10000000.125", "-9999999.875"]
        with self.assertRaisesRegex(ValueError, "Nonrepresentable source coordinate"):
            audit_case(c)

    def test_captured_fold_is_not_componentwise_monotone(self):
        b = tuple(map(F, [8.711944580078125, 8.45587158203125,
                          8.5344696044921875, 8.3977813720703125]))
        h = tuple(map(F, [0., .061720576137304306, .17600621283054352, .16925844550132751]))
        # Original failed native GPU neighbor pair; increasing X can turn
        # actual wet geometry dry even though all three donors are positive.
        self.assertGreater(value(b, h, (F(46,1600), F(468,3200))), 0)
        self.assertLess(value(b, h, (F(47,1600), F(468,3200))), 0)

    def test_missing_triangle(self):
        c = self.case(); c["triangles"].pop()
        with self.assertRaisesRegex(ValueError, "Incomplete stored-polygon"):
            audit_case(c)

    def test_duplicated_triangle(self):
        c = self.case(); c["triangles"][1] = copy.copy(c["triangles"][0])
        with self.assertRaises(ValueError):
            audit_case(c)

    def test_reversed_triangle(self):
        c = self.case(); c["triangles"][1].reverse()
        with self.assertRaisesRegex(ValueError, "not wholly certified wet"):
            audit_case(c)

    def test_invalid_index(self):
        c = self.case(); c["triangles"][0][0] = 99
        with self.assertRaisesRegex(ValueError, "Invalid triangle index"):
            audit_case(c)

    def test_float_rounding_mismatch(self):
        c = self.case(); c["boundary_buffer_cm"][0][0] = "0.09375000000000001"
        with self.assertRaisesRegex(ValueError, "GPU conversion"):
            audit_case(c)

    def test_narrower_band_rejects_original_geometry(self):
        c = self.case(); c["width_cm"] = "0.04"
        with self.assertRaisesRegex(ValueError, "exceeds original geometric band"):
            audit_case(c)

    def test_wet_omitted_region_rejected(self):
        c = self.case(); c["inner_local"] = [["0.625", "0"], ["0", "0.625"]]
        with self.assertRaisesRegex(ValueError, "not certified dry"):
            audit_case(c)

    def test_changed_source_contract_rejected(self):
        c = self.case(); c["depth"][0] = "1e-12"
        with self.assertRaisesRegex(ValueError, "donor contract"):
            audit_case(c)

    def test_outside_cell(self):
        c = self.case(); c["polygon_buffer_cm"][0][0] = "0.25"
        with self.assertRaisesRegex(ValueError, "outside original hydraulic cell"):
            audit_case(c)

    def test_lost_shared_edge(self):
        c = self.case(); c["boundary_buffer_cm"][0][1] = "0.001953125"
        c["polygon_buffer_cm"][2] = copy.copy(c["boundary_buffer_cm"][0])
        with self.assertRaisesRegex(ValueError, "Lost canonical shared-edge"):
            audit_case(c)


if __name__ == "__main__":
    unittest.main()
