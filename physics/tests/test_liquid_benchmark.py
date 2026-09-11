import copy
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from audit_liquid_benchmark import summarize


class LiquidBenchmarkTest(unittest.TestCase):
    def fixture(self):
        return dict(complete=True,error=None,captures=[dict(frame=230),dict(frame=720)],
                    live_density_requested=False,benchmark=dict(start_frame=240,end_frame=720,
                    intervals_ms=[20.]*480,wall_seconds=9.6,simulation_seconds=8.,
                    blocking_readbacks_during_window=False,image_exports_during_window=False))

    def test_uninterrupted_window_is_not_game_fps(self):
        result=summarize(self.fixture(),'')
        self.assertTrue(result['uninterrupted_window_verified'])
        self.assertFalse(result['packaged_game_fps_measured'])
        self.assertEqual(result['editor_fixture_frame_intervals']['p95_ms'],20.)

    def test_rejects_blocking_capture_missing_interval_and_engine_error(self):
        for mutate in (lambda c:c['captures'].append(dict(frame=500)),
                       lambda c:c['benchmark']['intervals_ms'].pop(),
                       lambda c:c['benchmark'].update(blocking_readbacks_during_window=True)):
            c=self.fixture();mutate(c)
            self.assertFalse(summarize(c,'')['uninterrupted_window_verified'])
        self.assertFalse(summarize(self.fixture(),'LogRenderer: Error: resource conflict')['uninterrupted_window_verified'])

    def test_gpu_order_and_sum_are_independent_checks(self):
        c=self.fixture();c['live_density_requested']=True
        c['live_density_result']=dict(gpu_timing_available=True,gpu_timing_waits_for_results=False,
            diagnostics=[0]*4,error='',gpu_timing_skipped_busy_slots=0,
            gpu_timing_samples=[dict(update=i,ordered=True,pack_density_ms=5.,distance_ms=2.,copy_ms=.1,total_ms=7.1) for i in range(720)])
        self.assertTrue(summarize(c,'')['gpu_timing_verified'])
        bad=copy.deepcopy(c);bad['live_density_result']['gpu_timing_samples'][300]['ordered']=False
        self.assertFalse(summarize(bad,'')['gpu_timing_verified'])
        c['live_density_result']['gpu_timing_samples'][300]['total_ms']=10.
        self.assertFalse(summarize(c,'')['gpu_timing_verified'])


if __name__=='__main__':unittest.main()
