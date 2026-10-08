import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import Mock, patch

import resume_futaleufu_native_checkpoint as flow

GIB=1024**3
HEALTHY=dict(available_physical_bytes=10*GIB, available_commit_bytes=10*GIB, free_disk_bytes=48*GIB)


class LongContinuationGuards(unittest.TestCase):
    def test_changed_input_is_refused_before_process_observation(self):
        with TemporaryDirectory() as directory, patch.object(flow, 'shared_native_work') as observe:
            output=Path(directory)
            with self.assertRaisesRegex(ValueError, 'changed'):
                flow.prelaunch_check(output, Mock(side_effect=ValueError('changed input')))
            observe.assert_not_called()
            self.assertFalse(json.loads((output/'failure.json').read_text())['native_process_started'])

    def test_new_shared_work_after_serialization_refuses_launch(self):
        calls=[]
        with TemporaryDirectory() as directory, patch.object(flow, 'resources', return_value=HEALTHY), \
                patch.object(flow, 'shared_native_work', side_effect=lambda: calls.append('observe') or [dict(ProcessId=8,Name='UnrealEditor.exe')]):
            output=Path(directory)
            with self.assertRaisesRegex(ValueError, 'overlap'):
                flow.prelaunch_check(output, lambda: calls.append('verify'))
            self.assertEqual(calls,['verify','observe'])
            receipt=json.loads((output/'failure.json').read_text())
            self.assertEqual(receipt['stage'],'prelaunch')
            self.assertFalse(receipt['native_process_started'])

    def test_fresh_headroom_is_checked_after_preparation(self):
        with TemporaryDirectory() as directory, patch.object(flow, 'shared_native_work', return_value=[]):
            for key,floor in (('available_physical_bytes',6*GIB),('available_commit_bytes',6*GIB),('free_disk_bytes',43*GIB)):
                with self.subTest(key=key), patch.object(flow, 'resources',return_value={**HEALTHY,key:floor-1}), self.assertRaises(ValueError):
                    flow.prelaunch_check(Path(directory),lambda:None)

    def test_healthy_prelaunch_records_actual_resources(self):
        with TemporaryDirectory() as directory, patch.object(flow, 'resources',return_value=HEALTHY), \
                patch.object(flow, 'shared_native_work',return_value=[]):
            output=Path(directory)
            self.assertEqual(flow.prelaunch_check(output,lambda:None),HEALTHY)
            self.assertEqual(json.loads((output/'prelaunch.json').read_text())['resources'],HEALTHY)
            self.assertFalse((output/'failure.json').exists())

    def test_long_run_keeps_four_hour_bound_and_existing_reserves(self):
        self.assertIsNone(flow.watchdog_failure(HEALTHY,[],4*3600))
        self.assertIn('four-hour',flow.watchdog_failure(HEALTHY,[],4*3600+.01))
        for key,floor in (('available_physical_bytes',3*GIB),('available_commit_bytes',3*GIB),('free_disk_bytes',40*GIB)):
            self.assertIsNone(flow.watchdog_failure({**HEALTHY,key:floor},[],0))
            self.assertIsNotNone(flow.watchdog_failure({**HEALTHY,key:floor-1},[],0))
        self.assertIn('only owned',flow.watchdog_failure(HEALTHY,[dict(ProcessId=8)],0))


if __name__=='__main__':unittest.main()
