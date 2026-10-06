import unittest
from audit_crest_batch_profile import analyze, SIZES


def group(frame):
    return '\n'.join(f'CrestBatchAudit exact frame={frame} batch={size} order={(i+5-frame%5)%5} '
                     f'total_ms={10-i} selection_ms={8-i} vertices=100 triangles=90 memo_bytes=4096'
                     for i, size in enumerate(SIZES))


class BatchProfileTests(unittest.TestCase):
    def test_repeated_group_retained(self):
        report = analyze(group(120)+'\n'+group(120)+'\n'+group(121),120,121)
        self.assertEqual(report['input_groups'],3)
        self.assertEqual(report['expanded_vertex_visits'],300)
        self.assertEqual(report['repeated_frame_groups'],{'120':2})
        self.assertEqual(report['variants']['512']['baseline_minus_variant_ms']['mean'],4)
        self.assertIsNone(report['variants']['128']['difference_by_variant_order']['1'])

    def test_incomplete_group_rejected(self):
        with self.assertRaisesRegex(ValueError,'Incomplete'):
            analyze('\n'.join(group(120).splitlines()[:-1]),120,120)

    def test_wrong_order_rejected(self):
        with self.assertRaisesRegex(ValueError,'order'):
            analyze(group(120).replace('order=0','order=1'),120,120)

    def test_missing_frame_rejected(self):
        with self.assertRaisesRegex(ValueError,'Missing'):
            analyze(group(120),120,121)

    def test_explicit_unchanged_frame_accepted_without_inventing_build(self):
        report=analyze(group(120)+'\nCrestBatchAudit unchanged frame=121',120,121)
        self.assertEqual(report['frames'],2)
        self.assertEqual(report['input_groups'],1)
        self.assertEqual(report['unchanged_geometry_calls'],{'121':1})

    def test_only_unchanged_is_not_timing_evidence(self):
        with self.assertRaisesRegex(ValueError,'No actual'):
            analyze('CrestBatchAudit unchanged frame=120',120,120)

    def test_mismatch_anywhere_rejected(self):
        with self.assertRaisesRegex(ValueError,'mismatch'):
            analyze(group(120)+'\nCrestBatchAudit mismatch frame=300',120,120)

    def test_different_input_rejected(self):
        with self.assertRaisesRegex(ValueError,'input'):
            analyze(group(120).replace('vertices=100','vertices=101',1),120,120)


if __name__ == '__main__':
    unittest.main()
