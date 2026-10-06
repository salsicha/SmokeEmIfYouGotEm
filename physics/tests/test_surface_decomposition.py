import csv
import json
from pathlib import Path
import subprocess
import sys
import numpy as np
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/audit_surface_decomposition.py"


def fixture(tmp_path, hole=False, invalid_sum=False, smoothed_base=False):
    rows = []
    for y in range(3592, 3621):
        for x in range(-5444, -5415):
            if hole and (x, y) == (-5430, 3606):
                continue
            base = 5+.1*(x+5430)
            crest = .5*np.exp(-(x+5430)**2/4)
            rows.append(dict(field_x_m=x, field_y_m=y, raw_eta_m=base, raw_depth_m=1,
                             filtered_eta_m=base+(.5 if smoothed_base else 0), hydraulic_relief_m=0,
                             shared_crest_m=crest, other_relief_m=.1,
                             target_z_m=base+crest+.12+(.01 if invalid_sum else 0)+(.5 if smoothed_base else 0),
                             flow_x_mps=2, flow_y_mps=0))
    path = tmp_path/"source.csv"
    with path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    crests = tmp_path/"crests.json"
    crests.write_text(json.dumps(dict(sites=[dict(station_m=-5430, lateral_m=3606,
                                                flow_direction_x=1, flow_direction_y=0)])))
    return [sys.executable, str(SCRIPT), str(path), str(crests),
            "--render-lift-m", ".02", "--report", str(tmp_path/"report.json")]


class SurfaceDecompositionTest(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix="raftsim-decomposition-")
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name)

    def test_actual_component_sum_and_profile(self):
        subprocess.run(fixture(self.path), check=True, capture_output=True)
        result = json.loads((self.path/"report.json").read_text())
        profile = result["profiles"][0]
        self.assertLess(result["maximum_sum_residual_m"], 1.e-12)
        self.assertEqual(profile["missing_samples"], 0)
        self.assertLess(abs(profile["components"]["raw_eta_m"]["endpoint_detrended_peak_m"]), 1.e-12)
        self.assertAlmostEqual(profile["components"]["shared_crest_m"]["endpoint_detrended_peak_m"], .5)
        self.assertIs(result["visual_accepted"], False)

    def test_missing_wet_corner_is_not_filled(self):
        subprocess.run(fixture(self.path, hole=True), check=True, capture_output=True)
        profile = json.loads((self.path/"report.json").read_text())["profiles"][0]
        self.assertGreater(profile["missing_samples"], 0)
        self.assertTrue(all(row["distance_m"] != 0 for row in profile["samples"]))

    def test_inconsistent_component_sum_rejected(self):
        result = subprocess.run(fixture(self.path, invalid_sum=True), capture_output=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((self.path/"report.json").exists())

    def test_report_never_overwritten(self):
        command = fixture(self.path)
        report = self.path/"report.json"
        report.write_text("retained evidence")
        self.assertNotEqual(subprocess.run(command, capture_output=True).returncode, 0)
        self.assertEqual(report.read_text(), "retained evidence")

    def test_native_stage_gate_rejects_consistent_but_smoothed_geometry(self):
        command = fixture(self.path, smoothed_base=True)
        self.assertNotEqual(subprocess.run(command+["--require-native-stage"], capture_output=True).returncode, 0)
        self.assertFalse((self.path/"report.json").exists())
        subprocess.run(command, check=True, capture_output=True)
        self.assertAlmostEqual(json.loads((self.path/"report.json").read_text())["maximum_base_native_stage_error_m"], .5)


if __name__ == "__main__":
    unittest.main()
