import io
import unittest
from audit_unreal_frame_csv import parse_capture, summarize, summarize_water_workload, WATER_SCOPES, PUBLISH_SCOPES, SMOOTHING_SCOPES, BREAKING_SCOPES, FOAM_SCOPES, GROUND_SCOPES, RELIEF_SCOPES

HEADER = "FrameTime,GameThreadTime,RenderThreadTime,RHIThreadTime,GPUTime\n"
FOOTER = HEADER + "[HasHeaderRowAtEnd],1\n"


class UnrealFrameCsvTest(unittest.TestCase):
    def test_full_hull_scopes_are_optional_and_do_not_replace_frame_budget(self):
        for name in GROUND_SCOPES[1:]:
            with self.subTest(scope=name):
                header = HEADER.rstrip() + ',' + name + '\n'
                capture = header + '200,190,4,2,70,80\n200,190,4,2,70,0\n' + header + '[HasHeaderRowAtEnd],1\n'
                samples, _ = parse_capture(io.StringIO(capture))
                result = summarize(samples, 0, 1)
                self.assertEqual(result[name]['mean_ms'], 40)
                self.assertEqual(result[name]['positive_sample_count'], 1)
                self.assertEqual(result['elapsed_frame_fps'], 5)
                self.assertFalse(result['frame_p95_within_target_budget'])
                legacy, _ = parse_capture(io.StringIO(HEADER + '20,18,4,2,5\n' + FOOTER))
                self.assertNotIn(name, summarize(legacy, 0, 0))
                for invalid in ('nan', 'inf', '-1'):
                    with self.assertRaises(ValueError):
                        parse_capture(io.StringIO(capture.replace(',80\n', ',' + invalid + '\n')))

    def test_append_only_engine_series_preserve_original_metric_positions(self):
        # Exact append-only layout emitted by Unreal's continuous CSV writer.
        final = HEADER.rstrip() + ',Exclusive/GameThread/EventWait/Effects\n'
        capture = HEADER + '20,18,4,2,5\n10,8,3,1,4,7\n' + final + '[HasHeaderRowAtEnd],1\n'
        samples, _ = parse_capture(io.StringIO(capture))
        self.assertEqual(samples[0]['GPUTime'], 5)
        self.assertEqual(samples[1]['GPUTime'], 4)
        self.assertEqual(summarize(samples, 0, 1)['FrameTime']['mean_ms'], 15)
        self.assertNotIn('Exclusive/GameThread/EventWait/Effects', samples[0])

    def test_appended_columns_do_not_hide_truncation_or_reordered_headers(self):
        final = HEADER.rstrip() + ',NewScope\n'
        rows = '20,18,4,2,5\n10,8,3,1,4,7\n'
        bad = [HEADER + rows + '10,8,3,1,4\n' + final,
               HEADER + rows + HEADER,
               HEADER + rows + final.replace('GameThreadTime,RenderThreadTime', 'RenderThreadTime,GameThreadTime'),
               HEADER + rows + final.replace('NewScope', 'GPUTime'),
               HEADER + '20,18,4,2,5,7,8\n' + final,
               HEADER + rows]
        for capture in bad:
            with self.subTest(capture=capture), self.assertRaises(ValueError):
                parse_capture(io.StringIO(capture + '[HasHeaderRowAtEnd],1\n'))

    def test_same_row_scopes_and_inactive_rows(self):
        scopes = WATER_SCOPES + PUBLISH_SCOPES + SMOOTHING_SCOPES + BREAKING_SCOPES + FOAM_SCOPES + GROUND_SCOPES + RELIEF_SCOPES
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
        self.assertNotIn(BREAKING_SCOPES[0], summarize(legacy, 0, 0))  # Historical capture lacks the new scope.
        self.assertNotIn(FOAM_SCOPES[0], summarize(legacy, 0, 0))
        self.assertNotIn(GROUND_SCOPES[0], summarize(legacy, 0, 0))
        self.assertNotIn(RELIEF_SCOPES[0], summarize(legacy, 0, 0))
        self.assertNotIn("RaftSimCrests/GameThread/Normals", summarize(legacy, 0, 0))
        self.assertNotIn("RaftSimShoreline/GameThread/RenderPacket", summarize(legacy, 0, 0))
        for name in ('CrestSourceGather', 'OutputStorage', 'BoundsAndNotify'):
            self.assertNotIn(f'RaftSimShoreline/GameThread/{name}', summarize(legacy, 0, 0))

    def test_render_packet_timing_is_optional_and_not_added_to_frame_time(self):
        name = "RaftSimShoreline/GameThread/RenderPacket"
        header = HEADER.rstrip() + ',' + name + '\n'
        text = header + '20,18,4,2,5,1.5\n30,28,4,2,5,0.5\n' + header + '[HasHeaderRowAtEnd],1\n'
        samples, _ = parse_capture(io.StringIO(text))
        result = summarize(samples, 0, 1)
        self.assertEqual(result[name]['mean_ms'], 1)
        self.assertEqual(result['FrameTime']['mean_ms'], 25)
        self.assertEqual(result['elapsed_frame_fps'], 40)

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
        self.assertTrue(stats["frame_p95_within_target_budget"])
        self.assertEqual(stats["target_fps"], 30)
        self.assertAlmostEqual(stats["frame_budget_ms"], 1000 / 30)
        self.assertFalse(summarize(samples, 1, 2, 60)["frame_p95_within_target_budget"])
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

    def test_target_budget_boundary_and_invalid_targets(self):
        samples, _ = parse_capture(io.StringIO(HEADER + "33.333333333333336,20,10,2,12\n" + FOOTER))
        self.assertTrue(summarize(samples, 0, 0)["frame_p95_within_target_budget"])
        samples[0]["FrameTime"] += .001
        self.assertFalse(summarize(samples, 0, 0)["frame_p95_within_target_budget"])
        for target in (0, -30, float("nan"), float("inf")):
            with self.subTest(target=target), self.assertRaises(ValueError):
                summarize(samples, 0, 0, target)


class WaterWorkloadPhaseTest(unittest.TestCase):
    def samples(self):
        # Slow logical frames have refresh AND selection; FrameTime is emitted
        # in the next row. Deliberately anti-correlated same-row timings.
        return [dict(FrameTime=t, GameThreadTime=9., RenderThreadTime=5., RHIThreadTime=2., GPUTime=4.,
                     **{WATER_SCOPES[1]: r, WATER_SCOPES[6]: s})
                for t, r, s in ((10., 20., 5.), (50., 0., 0.), (10., 20., 5.), (50., 0., 0.))]

    def test_explicit_phase_changes_association_not_gate_or_elapsed_samples(self):
        samples = self.samples()
        before = [dict(row) for row in samples]
        shifted = summarize_water_workload(samples, 1, 3, 1)
        legacy = summarize_water_workload(samples, 1, 3, 0)
        self.assertEqual(shifted['groups'][3]['frame_time_sample_indices'], [1, 3])
        self.assertEqual(shifted['groups'][3]['water_scope_sample_indices'], [0, 2])
        self.assertEqual(shifted['groups'][3]['mean_frame_ms'], 50.)
        self.assertEqual(shifted['groups'][3]['scope_mean_ms'][WATER_SCOPES[1]], 20.)
        self.assertEqual(legacy['groups'][3]['frame_time_sample_indices'], [2])
        self.assertEqual(legacy['groups'][3]['mean_frame_ms'], 10.)
        for result in (shifted, legacy):
            self.assertEqual(sorted(i for g in result['groups'] for i in g['frame_time_sample_indices']), [1, 2, 3])
            self.assertEqual(sum(g['count'] for g in result['groups']), 3)
            self.assertEqual(sum(g['frames_over_budget'] for g in result['groups']), 2)
            self.assertFalse(result['frame_p95_within_target_budget'])
            self.assertIsNone(result['groups'][1]['mean_frame_ms'])
            self.assertIsNone(result['groups'][1]['scope_mean_ms'][WATER_SCOPES[1]])
            self.assertNotIn(FOAM_SCOPES[0], result['groups'][0]['scope_mean_ms'])
        self.assertEqual(samples, before)

    def test_nearest_rank_budget_boundary_and_empty_groups(self):
        samples = self.samples()
        for row in samples:
            row['FrameTime'] = 1000/30
        result = summarize_water_workload(samples, 1, 3, 1)
        self.assertTrue(result['frame_p95_within_target_budget'])
        self.assertEqual(result['groups'][3]['p95_frame_ms_nearest_rank'], 1000/30)
        self.assertEqual(sum(g['frames_over_budget'] for g in result['groups']), 0)

    def test_missing_predecessor_and_invalid_offset_are_not_silently_trimmed(self):
        with self.assertRaises(ValueError):
            summarize_water_workload(self.samples(), 0, 3, 1)
        for offset in (None, -1, 2, True, 1., '1'):
            with self.subTest(offset=offset), self.assertRaises(ValueError):
                summarize_water_workload(self.samples(), 1, 3, offset)

    def test_associated_scopes_must_exist_and_be_finite_in_predecessor_too(self):
        for name in (WATER_SCOPES[1], WATER_SCOPES[6]):
            for bad in (None, -1., float('nan'), float('inf')):
                samples = self.samples()
                if bad is None:
                    del samples[0][name]
                else:
                    samples[0][name] = bad
                with self.subTest(name=name, bad=bad), self.assertRaises(ValueError):
                    summarize_water_workload(samples, 1, 3, 1)
        samples = self.samples()
        samples[1][FOAM_SCOPES[0]] = .5
        with self.assertRaises(ValueError):
            summarize_water_workload(samples, 1, 3, 1)


if __name__ == "__main__":
    unittest.main()
