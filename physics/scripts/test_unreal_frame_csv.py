import io
import unittest
from audit_unreal_frame_csv import parse_capture, summarize, WATER_SCOPES, PUBLISH_SCOPES, SMOOTHING_SCOPES

HEADER = "FrameTime,GameThreadTime,RenderThreadTime,RHIThreadTime,GPUTime\n"
FOOTER = HEADER + "[HasHeaderRowAtEnd],1\n"


class UnrealFrameCsvTest(unittest.TestCase):
    def test_same_frame_scopes_and_inactive_rows(self):
        scopes = WATER_SCOPES + PUBLISH_SCOPES + SMOOTHING_SCOPES
        header = HEADER.rstrip() + "," + ",".join(scopes) + "\n"
        rows = "20,18,4,2,5," + ",".join(["8"] * len(scopes)) + "\n"
        rows += "10,8,3,1,4," + ",".join(["0"] * len(scopes)) + "\n"
        footer = header + "[HasHeaderRowAtEnd],1\n"
        samples, _ = parse_capture(io.StringIO(header + rows + footer), True)
        stats = summarize(samples, 0, 1)
        for scope in scopes:
            self.assertEqual(stats[scope]["count"], 2)
            self.assertEqual(stats[scope]["positive_sample_count"], 1)
            self.assertEqual(stats[scope]["mean_ms"], 4)
            self.assertEqual(stats[scope]["mean_positive_ms"], 8)
        for value in ("nan", "-1"):
            with self.assertRaises(ValueError):
                parse_capture(io.StringIO(header + rows.replace(",8,8", "," + value + ",8", 1) + footer), True)
        with self.assertRaises(ValueError):
            parse_capture(io.StringIO(HEADER + "10,8,3,1,4\n" + FOOTER), True)
        legacy, _ = parse_capture(io.StringIO(HEADER + "10,8,3,1,4\n" + FOOTER))
        self.assertNotIn(WATER_SCOPES[0], summarize(legacy, 0, 0))
        self.assertNotIn(SMOOTHING_SCOPES[0], summarize(legacy, 0, 0))

    def test_duplicate_unrelated_columns_are_rejected(self):
        header = HEADER.rstrip() + ",FMsgLogf/FMsgLogfCount,FMsgLogf/FMsgLogfCount\n"
        with self.assertRaises(ValueError):
            parse_capture(io.StringIO(header + "10,8,3,1,4,0,1\n" + header + "[HasHeaderRowAtEnd],1\n"))

    def test_completed_capture_and_warmed_interval(self):
        rows = "1000,900,800,10,700\n10,7,6,2,5\n20,14,12,4,10\n"
        samples, metadata = parse_capture(io.StringIO(HEADER + rows + HEADER +
            "[HasHeaderRowAtEnd],1,[rhiname],D3D12,[loginid],not-for-report\n"))
        stats = summarize(samples, 1, 2)
        self.assertEqual(stats["FrameTime"]["mean_ms"], 15)
        self.assertEqual(stats["FrameTime"]["p95_ms_nearest_rank"], 20)
        self.assertAlmostEqual(stats["elapsed_frame_fps"], 1000 / 15)
        self.assertFalse(stats["frame_p95_within_60fps_budget"])
        self.assertEqual(metadata, {"rhiname": "D3D12"})
        self.assertEqual(stats["GameThreadTime"]["mean_ms"], 10.5)

    def test_missing_nonfinite_truncated_and_concatenated_captures_rejected(self):
        bad = ["FrameTime\n10\n", HEADER + "10,7,6,2,5\n",
               HEADER + "10,7,6,2,5\n" + HEADER,
               HEADER + "nan,7,6,2,5\n" + HEADER,
               HEADER + "10,7,6,2\n" + HEADER,
               HEADER + "10,7,6,2,5\n" + HEADER + "10,7,6,2,5\n"]
        for text in bad:
            with self.subTest(text=text), self.assertRaises(ValueError):
                parse_capture(io.StringIO(text))

    def test_missing_interval_and_zero_frame_time_rejected(self):
        samples, _ = parse_capture(io.StringIO(HEADER + "0,0,0,0,0\n" + FOOTER))
        for first, last in [(0, 0), (0, 1), (-1, 0), (1, 0)]:
            with self.subTest(interval=(first, last)), self.assertRaises(ValueError):
                summarize(samples, first, last)


if __name__ == "__main__":
    unittest.main()
