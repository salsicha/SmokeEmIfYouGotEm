import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from audit_futaleufu_saved_continuation import schedule, require_complete_snapshots


class NativeScheduleTests(unittest.TestCase):
    def request(self, steps=30000, interval=3000):
        return dict(command=['solver', 'manifest', 'native', str(steps), str(interval), '4'],
                    steps=steps, dt_seconds=.01, source_time_seconds=32.)

    def test_all_long_run_snapshots_are_audited(self):
        r = self.request()
        r.update(snapshot_interval_steps=3000, target_time_seconds=332.)
        self.assertEqual(schedule(r, dict(dt_seconds=.01, initial_time_seconds=32.)),
                         list(range(0, 30001, 3000)))

    def test_historical_schedule_is_read_from_actual_command(self):
        self.assertEqual(schedule(self.request(3000, 300), dict(dt_seconds=.01, initial_time_seconds=32.)),
                         list(range(0, 3001, 300)))

    def test_conflicting_or_unreviewed_schedule_refuses(self):
        for change in (dict(steps=3000), dict(steps=True), dict(snapshot_interval_steps=300),
                       dict(dt_seconds=.02), dict(source_time_seconds=2.), dict(target_time_seconds=333.),
                       dict(command=['solver', 'manifest', 'native', '30000', '300', '4']),
                       dict(command=['solver', 'manifest', 'native', '30000', '3000', '8'])):
            with self.subTest(change=change), self.assertRaises(ValueError):
                schedule({**self.request(), **change}, dict(dt_seconds=.01, initial_time_seconds=32.))

    def test_partial_and_extra_snapshots_refuse(self):
        with TemporaryDirectory() as directory:
            native = Path(directory)
            for step in (0, 3000):
                folder = native/('frame_%06d'%step)
                folder.mkdir()
                (folder/'complete.json').write_text('{}')
            with self.assertRaises(ValueError):
                require_complete_snapshots(native, [0, 3000, 6000])
            require_complete_snapshots(native, [0, 3000])
            with self.assertRaises(ValueError):
                require_complete_snapshots(native, [0])
            (native/'frame_003000'/'complete.json').unlink()
            with self.assertRaises(ValueError):
                require_complete_snapshots(native, [0, 3000])

    def test_invalid_native_clock_refuses(self):
        for value in (-1., float('nan'), float('inf'), None):
            with self.subTest(value=value), self.assertRaises(ValueError):
                schedule(self.request(), dict(dt_seconds=.01, initial_time_seconds=value))


if __name__ == '__main__':
    unittest.main()
