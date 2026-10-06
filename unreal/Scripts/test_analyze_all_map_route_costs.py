"""Synthetic parser refusal controls. These fixtures are NOT native game/FPS evidence."""
import csv
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from audit_map_flythrough import MAPS, REQUIRED, audit, read_frames
from analyze_all_map_route_costs import analyze, rest_key_observation


class RouteCostEvidenceTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.index = self.root / "index.json"
        runs = []
        for map_name in MAPS:
            out = self.root / map_name
            out.mkdir()
            csv_path = out / "native.csv"
            header = ["EVENTS", *REQUIRED, "RaftSimSurface/GameThread/FoamTransport", "RaftSimSurface/GameThread/Missing"]
            with csv_path.open("w", newline="", encoding="utf-8") as stream:
                writer = csv.writer(stream)
                writer.writerow(header)
                for sequence, frame_ms, station in ((1, 40, 0), (2, 60, 4), (3, 45, 8)):
                    values = {"FrameTime": frame_ms, "GameThreadTime": frame_ms - 5, "GPUTime": 8,
                        "RaftSimRoute/Active": 1, "RaftSimRoute/StationM": station,
                        "RaftSimRoute/StartM": 0, "RaftSimRoute/EndM": 8, "RaftSimRoute/WetBaseline": 1,
                        "RaftSimRoute/LiveWaterAtCamera": 0, "RaftSimRoute/BoatDistanceM": station,
                        "RaftSimRoute/Sequence": sequence}
                    writer.writerow(["", *(values[name] for name in REQUIRED), .5, ""])
                writer.writerow(header)
            receipt = {"schema": "raftsim.native_map_flythrough.v1", "map": map_name,
                "mode": "camera_only_no_boat_guidance", "complete": True, "failure": "",
                "start_m": 0, "end_m": 8, "whole_authored_axis": True, "native_route_ticks": 3}
            receipt_path = out / "receipt.json"
            self.write(receipt_path, receipt)
            saved = audit(read_frames(csv_path), receipt)
            saved.update(csv=str(csv_path), csv_sha256=hashlib.sha256(csv_path.read_bytes()).hexdigest(),
                         native_receipt=str(receipt_path))
            saved_path = out / "audit.json"
            self.write(saved_path, saved)
            self.write(out / "launch.json", {"schema": "raftsim.map_flythrough_launch.v1", "map": map_name,
                "binary_sha256": {"unit-fixture-NOT-real-game": "fixture-only"}, "exit_code": 0,
                "recording": False, "screenshots": False, "boat_guidance": False})
            runs.append({"map": map_name, "complete": True, "native_route_complete": True,
                         "same_native_binaries_as_collection": True, "audit": str(saved_path)})
        self.write(self.index, {"all_eight_routes_complete": True, "all_eight_native_routes_complete": True, "runs": runs})

    @staticmethod
    def write(path, value):
        path.write_text(json.dumps(value), encoding="utf-8")

    def mutate(self, path, function):
        value = json.loads(path.read_text())
        function(value)
        self.write(path, value)

    def test_all_slow_frames_retained_and_missing_optional_not_zero(self):
        result = analyze(self.index)
        self.assertEqual(len(result["maps"]), 8)
        self.assertFalse(result["all_eight_every_frame_20fps"])
        self.assertFalse(result["all_map_physical_feature_acceptance"])
        for item in result["maps"]:
            self.assertEqual(item["active_frames"], 3)
            self.assertEqual(item["frames_below_20fps"], 1)
            self.assertEqual(item["actual_worst_frame"]["native_sequence"], 2)
            self.assertEqual(item["whole_route_mean_stage_ms"]["RaftSimSurface/GameThread/FoamTransport"], .5)
            self.assertNotIn("RaftSimSurface/GameThread/Missing", item["whole_route_mean_stage_ms"])
            self.assertEqual(item["unqualified_optional_mean_stages"]["RaftSimSurface/GameThread/Missing"]["qualified_samples"], 0)

    def test_partial_collection_refused(self):
        self.mutate(self.index, lambda value: value.update(all_eight_native_routes_complete=False))
        with self.assertRaises(ValueError): analyze(self.index)

    def test_duplicate_map_refused(self):
        self.mutate(self.index, lambda value: value["runs"][1].update(map=MAPS[0]))
        with self.assertRaises(ValueError): analyze(self.index)

    def test_changed_csv_refused(self):
        path = self.root / MAPS[0] / "native.csv"
        path.write_text(path.read_text() + "changed")
        with self.assertRaises(ValueError): analyze(self.index)

    def test_different_binary_refused(self):
        self.mutate(self.root / MAPS[1] / "launch.json", lambda value: value.update(binary_sha256={"fixture": "different"}))
        with self.assertRaises(ValueError): analyze(self.index)

    def test_bad_native_exit_refused(self):
        self.mutate(self.root / MAPS[0] / "launch.json", lambda value: value.update(exit_code=1))
        with self.assertRaises(ValueError): analyze(self.index)

    def test_guided_or_recorded_run_refused(self):
        self.mutate(self.root / MAPS[0] / "launch.json", lambda value: value.update(boat_guidance=True))
        with self.assertRaises(ValueError): analyze(self.index)

    def test_missing_launch_flags_refused(self):
        self.mutate(self.root / MAPS[0] / "launch.json", lambda value: value.pop("recording"))
        with self.assertRaises(ValueError): analyze(self.index)

    def test_mismatched_saved_audit_refused(self):
        self.mutate(self.root / MAPS[0] / "audit.json", lambda value: value.update(audited_frames=4))
        with self.assertRaises(ValueError): analyze(self.index)

    def test_skipped_native_route_tick_refused(self):
        self.mutate(self.root / MAPS[0] / "receipt.json", lambda value: value.update(native_route_ticks=4))
        with self.assertRaises(ValueError): analyze(self.index)


class NativeRestKeyCounterTest(unittest.TestCase):
    header = ["RaftSimHull/RestKeySealedChecks", "RaftSimHull/RestKeyReferenceChecks"]

    def test_all_rows_preserved_including_reference_and_no_step_frames(self):
        result = rest_key_observation(self.header, [["8", "0"], ["7", "1"], ["0", "0"]], True)
        self.assertEqual(result["active_frames_observed"], 3)
        self.assertEqual(result["sealed_checks_sum"], 15)
        self.assertEqual(result["reference_checks_sum"], 1)
        self.assertEqual(result["active_frames_with_sealed_checks"], 2)
        self.assertEqual(result["active_frames_with_reference_checks"], 1)
        self.assertEqual(result["active_frames_without_key_checks"], 1)
        self.assertFalse(result["every_active_frame_used_sealed_key"])

    def test_all_observed_sealed(self):
        result = rest_key_observation(self.header, [["8", "0"], ["8", "0"]], True)
        self.assertTrue(result["every_active_frame_used_sealed_key"])
        self.assertEqual(result["mean_sealed_checks_per_active_frame"], 8)

    def test_legacy_missing_is_null_not_fabricated_zero(self):
        self.assertIsNone(rest_key_observation(["FrameTime"], [["40"]]))
        with self.assertRaises(ValueError):
            rest_key_observation(["FrameTime"], [["40"]], True)

    def test_reference_only_cannot_prove_optimized_map(self):
        with self.assertRaises(ValueError):
            rest_key_observation(self.header, [["0", "8"]], True)

    def test_missing_ambiguous_incomplete_and_nonfinite_rows_refused(self):
        cases = [
            (self.header[:1], [["8"]]),
            (self.header + self.header[:1], [["8", "0", "8"]]),
            (self.header, []),
            (self.header, [["8"]]),
            (self.header, [["8", ""]]),
            (self.header, [["NaN", "0"]]),
            (self.header, [["Infinity", "0"]]),
            (self.header, [["-1", "0"]]),
            (self.header, [["8.5", "0"]]),
        ]
        for header, rows in cases:
            with self.subTest(header=header, rows=rows), self.assertRaises(ValueError):
                rest_key_observation(header, rows, True)


if __name__ == "__main__": unittest.main()
