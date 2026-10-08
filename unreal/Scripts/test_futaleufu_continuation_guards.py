import json
from pathlib import Path
from tempfile import TemporaryDirectory
import subprocess
import unittest
from unittest.mock import Mock, patch

import continue_futaleufu_native_flow as flow


GIB = 1024**3
HEALTHY = dict(available_physical_bytes=12*GIB, available_commit_bytes=12*GIB,
               free_disk_bytes=48*GIB)
SOLVER_SHA = 'fb2624bb8cb210142ae17741c5358c86a48d6f42c60eedab64715def53c6e558'
OTHER = dict(ProcessId=700, Name='UnrealEditor-Cmd.exe', PrivatePageCount=4*GIB)


class ContinuationGuardTests(unittest.TestCase):
    def test_prelaunch_preserves_existing_floors(self):
        flow.require_launch_headroom(HEALTHY, [])
        for key, floor in (('available_physical_bytes', 6*GIB),
                           ('available_commit_bytes', 6*GIB), ('free_disk_bytes', 43*GIB)):
            with self.subTest(key=key):
                flow.require_launch_headroom({**HEALTHY, key: floor}, [])
                with self.assertRaises(ValueError):
                    flow.require_launch_headroom({**HEALTHY, key: floor-1}, [])
        with self.assertRaisesRegex(ValueError, 'do not overlap'):
            flow.require_launch_headroom(HEALTHY, [OTHER])

    def test_running_floors_and_new_work_fail_closed(self):
        self.assertIsNone(flow.runtime_guard_failure(HEALTHY, [], 3599))
        self.assertIn('only owned', flow.runtime_guard_failure(HEALTHY, [OTHER], 1))
        for key, floor in (('available_physical_bytes', 3*GIB),
                           ('available_commit_bytes', 3*GIB), ('free_disk_bytes', 40*GIB)):
            self.assertIsNotNone(flow.runtime_guard_failure({**HEALTHY, key: floor-1}, [], 1))
            self.assertIsNone(flow.runtime_guard_failure({**HEALTHY, key: floor}, [], 1))
        self.assertIn('one-hour', flow.runtime_guard_failure(HEALTHY, [], 3601))

    def test_process_observation_excludes_only_owned_pid(self):
        owned = dict(ProcessId=600, Name='raftsim_cartesian_cook.exe', PrivatePageCount=GIB)
        with patch.object(flow.subprocess, 'run', return_value=Mock(stdout=json.dumps([owned, OTHER]))) as query:
            self.assertEqual(flow.shared_native_work(600), [OTHER])
            self.assertIn('AutomationTool', query.call_args.args[0][-1])
        with patch.object(flow.subprocess, 'run', return_value=Mock(stdout=json.dumps(OTHER))):
            self.assertEqual(flow.shared_native_work(), [OTHER])
        with patch.object(flow.subprocess, 'run', side_effect=OSError('observation failed')):
            with self.assertRaises(OSError): flow.shared_native_work()

    def test_engine_started_during_checkpoint_preparation_prevents_launch(self):
        self.assert_prelaunch_refusal([OTHER], HEALTHY, 'do not overlap')

    def test_memory_used_during_checkpoint_preparation_prevents_launch(self):
        self.assert_prelaunch_refusal([], {**HEALTHY, 'available_commit_bytes': 5*GIB}, 'allowance')

    def assert_prelaunch_refusal(self, busy, final_resources, message):
        with TemporaryDirectory(dir=flow.ROOT/'tmp') as directory:
            output = Path(directory)/'run'
            with patch.object(flow, 'sha', return_value=SOLVER_SHA), \
                 patch.object(flow, 'prepare', return_value=dict(sources_sha256={}, inputs=[], initial_time_seconds=2)), \
                 patch.object(flow, 'resources', side_effect=[HEALTHY, final_resources]), \
                 patch.object(flow, 'shared_native_work', side_effect=[[], busy]) as probe, \
                 patch.object(flow.subprocess, 'Popen') as launch:
                with self.assertRaisesRegex(ValueError, message):
                    flow.run(flow.ROOT/'tmp/prior', flow.ROOT/'tmp/solver.exe', output)
                launch.assert_not_called()
                self.assertEqual(probe.call_count, 2)
            failure = json.loads((output/'failure.json').read_text())
            self.assertEqual(failure['stage'], 'prelaunch')
            self.assertFalse(failure['native_process_started'])
            self.assertEqual(json.loads((output/'prelaunch.json').read_text())['resources'], final_resources)

    def test_new_shared_work_stops_only_owned_child_and_records_it(self):
        child = Mock(pid=600, returncode=1)
        child.poll.return_value = None
        child.wait.side_effect = [subprocess.TimeoutExpired('solver', 5), 1]
        with TemporaryDirectory(dir=flow.ROOT/'tmp') as directory:
            output = Path(directory)/'run'
            with patch.object(flow, 'sha', return_value=SOLVER_SHA), \
                 patch.object(flow, 'prepare', return_value=dict(sources_sha256={}, inputs=[], initial_time_seconds=2)), \
                 patch.object(flow, 'resources', return_value=HEALTHY), \
                 patch.object(flow, 'shared_native_work', side_effect=[[], [], [OTHER]]) as probe, \
                 patch.object(flow.subprocess, 'Popen', return_value=child):
                with self.assertRaisesRegex(RuntimeError, 'only owned'):
                    flow.run(flow.ROOT/'tmp/prior', flow.ROOT/'tmp/solver.exe', output)
                child.terminate.assert_called_once_with()
                self.assertEqual(probe.call_args.args, (600,))
            sample = json.loads((output/'resources.jsonl').read_text())
            self.assertEqual(sample['shared_work'], [OTHER])
            self.assertFalse((output/'completed.json').exists())


if __name__ == '__main__':
    unittest.main()
