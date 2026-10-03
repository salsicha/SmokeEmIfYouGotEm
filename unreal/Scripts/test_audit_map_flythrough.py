"""Parser-only fabricated fixtures. Never runtime/performance evidence."""
import copy
import csv
import tempfile
import unittest
from pathlib import Path

from audit_map_flythrough import REQUIRED, audit, read_frames


class FlythroughAuditTests(unittest.TestCase):
    def setUp(self):
        self.receipt = dict(schema="raftsim.native_map_flythrough.v1", map="L_Hance",
                            mode="camera_only_no_boat_guidance", complete=True,
                            start_m=0, end_m=20, whole_authored_axis=True, failure="", native_route_ticks=5)
        self.frames = []
        for number, station in enumerate((0, 5, 10, 15, 20), 1):
            self.frames.append(dict(zip(REQUIRED, (40, 25, 30, 1, station, 0, 20, 1, 0, 50, number))))

    def test_all_frames_required(self):
        result = audit(self.frames, self.receipt)
        self.assertTrue(result["passes_every_route_frame_20fps"])
        self.assertFalse(result["all_map_water_and_boat_validation_accepted"])
        self.assertEqual(result["live_water_at_camera_frames"], 0)

    def test_single_slow_frame_not_hidden_by_percentile(self):
        self.frames[2]["FrameTime"] = 50.001
        result = audit(self.frames, self.receipt)
        self.assertFalse(result["passes_every_route_frame_20fps"])
        self.assertEqual(result["first_slow_station_m"], 10)

    def test_endpoint_slow_frame_not_trimmed(self):
        self.frames[0]["FrameTime"] = 120
        self.assertEqual(audit(self.frames, self.receipt)["frames_below_20fps"], 1)

    def test_exact_budget_is_allowed(self):
        self.frames[-1]["FrameTime"] = 50
        self.assertTrue(audit(self.frames, self.receipt)["passes_every_route_frame_20fps"])

    def test_missing_endpoints(self):
        for frames in (self.frames[1:], self.frames[:-1]):
            with self.assertRaises(ValueError):
                audit(frames, self.receipt)

    def test_gap_and_backtrack_rejected(self):
        for value in (11, -1):
            frames = copy.deepcopy(self.frames)
            frames[1]["RaftSimRoute/StationM"] = value
            with self.assertRaises(ValueError):
                audit(frames, self.receipt)

    def test_inactive_hole_rejected(self):
        self.frames[2]["RaftSimRoute/Active"] = 0
        with self.assertRaises(ValueError):
            audit(self.frames, self.receipt)

    def test_partial_and_failed_receipts_rejected(self):
        for key, value in (("whole_authored_axis", False), ("complete", False),
                           ("failure", "lost camera"), ("mode", "guided_boat")):
            receipt = dict(self.receipt, **{key: value})
            with self.assertRaises(ValueError):
                audit(self.frames, receipt)

    def test_mismatched_bounds_rejected(self):
        self.frames[1]["RaftSimRoute/EndM"] = 19
        with self.assertRaises(ValueError):
            audit(self.frames, self.receipt)

    def test_lost_tick_and_duplicated_sequence_rejected(self):
        with self.assertRaises(ValueError):
            audit(self.frames, dict(self.receipt, native_route_ticks=6))
        self.frames[2]["RaftSimRoute/Sequence"] = 2
        with self.assertRaises(ValueError):
            audit(self.frames, self.receipt)

    def write_fixture(self, folder, frames, header=REQUIRED):
        path = Path(folder) / "fixture.csv"
        with path.open("w", newline="", encoding="utf-8") as stream:
            writer = csv.writer(stream)
            writer.writerow(("EVENTS", *header))
            for frame in frames:
                writer.writerow(("", *(frame[name] for name in header)))
            writer.writerow(("EVENTS", *header))
        return path

    def test_native_footer_reader(self):
        with tempfile.TemporaryDirectory() as folder:
            frames = read_frames(self.write_fixture(folder, self.frames))
            self.assertEqual(audit(frames, self.receipt)["audited_frames"], 5)

    def test_nonfinite_and_zero_time_rejected(self):
        for value in (float("nan"), float("inf"), 0, -1):
            frames = copy.deepcopy(self.frames)
            frames[2]["FrameTime"] = value
            with tempfile.TemporaryDirectory() as folder, self.assertRaises(ValueError):
                read_frames(self.write_fixture(folder, frames))

    def test_missing_and_duplicate_columns_rejected(self):
        for header in (REQUIRED[:-1], REQUIRED + ("FrameTime",)):
            with tempfile.TemporaryDirectory() as folder, self.assertRaises(ValueError):
                read_frames(self.write_fixture(folder, self.frames, header))


if __name__ == "__main__":
    unittest.main()
