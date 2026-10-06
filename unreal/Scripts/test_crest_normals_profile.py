import unittest
from audit_crest_normals_profile import analyze


def row(frame):
    return f'CrestNormalsAudit exact frame={frame} vertices=10 triangles=8 rebuilt={frame%2} serial_ms=2 parallel_ms=1 parallel_first={frame%2}'


class CrestNormalsProfileTest(unittest.TestCase):
    def test_keeps_repeated_calls_and_both_orders(self):
        result = analyze(row(120)+'\n'+row(120)+'\n'+row(121), 120, 121)
        self.assertEqual(result['paired_calls'], 3)
        self.assertEqual(result['vertex_attribute_comparisons'], 30)
        self.assertEqual(result['repeated_frame_calls'], {'120': 2})
        self.assertEqual(result['all_calls']['serial_minus_parallel_ms']['mean'], 1)
        self.assertFalse(result['scene_or_fps_accepted'])

    def test_missing_frame_fails(self):
        with self.assertRaisesRegex(ValueError, 'Missing'):
            analyze(row(120), 120, 121)

    def test_mismatch_outside_window_fails(self):
        with self.assertRaisesRegex(ValueError, 'mismatch'):
            analyze(row(120)+'\nCrestNormalsAudit mismatch frame=300', 120, 120)

    def test_malformed_record_fails(self):
        for old, new in [('parallel_first=0', 'parallel_first=1'), ('serial_ms=2', 'serial_ms=0'),
                         ('vertices=10', 'vertices=10.5'), ('parallel_ms=1', 'parallel_ms=nan')]:
            with self.subTest(new=new), self.assertRaises(ValueError):
                analyze(row(120).replace(old, new), 120, 120)


if __name__ == '__main__':
    unittest.main()
