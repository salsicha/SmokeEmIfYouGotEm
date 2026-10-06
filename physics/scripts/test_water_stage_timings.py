import tempfile
import unittest
from pathlib import Path

from audit_water_stage_timings import summarize


class WaterStageTimingsTest(unittest.TestCase):
    def read(self, text, first=30, last=33):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "engine.log"
            path.write_text(text, encoding="utf-8")
            return summarize(path, first, last)

    def test_interval_and_nested_scopes(self):
        lines = ["WaterPerf scope=tick frame=1 total_ms=999"]
        for frame, value in enumerate([1, 2, 3, 40], 30):
            lines += [f"WaterPerf scope=tick frame={frame} total_ms={value} refresh_ms=1",
                      f"WaterPerf scope=refresh frame={frame} total_ms=1 source_samples_ms=0.2"]
        result = self.read("\n".join(lines))
        self.assertEqual(result["stages"]["tick"]["total_ms"]["count"], 4)
        self.assertEqual(result["stages"]["tick"]["total_ms"]["median"], 2.5)
        self.assertEqual(result["stages"]["tick"]["total_ms"]["p95_nearest_rank"], 40)
        self.assertEqual(result["stages"]["refresh"]["total_ms"]["mean"], 1)
        self.assertEqual(len(result["sha256"]), 64)

    def test_duplicate_frame_rejected(self):
        with self.assertRaisesRegex(ValueError, "duplicate"):
            self.read("WaterPerf scope=tick frame=30 total_ms=1\n" * 2)

    def test_empty_or_incomplete_log_rejected(self):
        for text in ["", "WaterPerf scope=tick frame=30 total_ms=1"]:
            with self.assertRaisesRegex(ValueError, "no tick/refresh"):
                self.read(text)

    def test_missing_tick_rejected(self):
        text='\n'.join(f'WaterPerf scope=tick frame={f} total_ms=1' for f in (30,31,33))
        with self.assertRaisesRegex(ValueError,'incomplete tick'):
            self.read(text+'\nWaterPerf scope=refresh frame=30 total_ms=1')

    def test_invalid_values_and_duplicate_keys(self):
        for metrics in ('total_ms=nan','total_ms=inf','total_ms=-1','total_ms=1 total_ms=2','work_ms=1'):
            with self.assertRaises(ValueError):
                self.read(f'WaterPerf scope=tick frame=30 {metrics}')

    def test_changed_metric_set_rejected(self):
        with self.assertRaisesRegex(ValueError,'changed metrics'):
            self.read('WaterPerf scope=tick frame=30 total_ms=1 work_ms=0.5\n'
                      'WaterPerf scope=tick frame=31 total_ms=1')

    def test_sparse_refresh_records_its_actual_frames(self):
        text='\n'.join(f'WaterPerf scope=tick frame={f} total_ms=1' for f in range(30,34))
        report=self.read(text+'\nWaterPerf scope=refresh frame=31 total_ms=0.0')
        self.assertTrue(report['complete_tick_coverage'])
        self.assertEqual(report['scope_frames']['refresh'],[31])
        self.assertEqual(report['stages']['refresh']['total_ms']['count'],1)

    def test_invalid_interval(self):
        with self.assertRaisesRegex(ValueError,'invalid frame interval'):
            self.read('',first=33,last=30)


if __name__ == "__main__":
    unittest.main()
