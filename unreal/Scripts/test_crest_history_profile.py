import unittest
from audit_crest_history_profile import analyze


class CrestProfileTests(unittest.TestCase):
    def line(self, frame, fast=1., legacy=2.):
        return f'CrestHistoryHashAudit exact frame={frame} vertices=10 dense=0 fast_ms={fast} legacy_ms={legacy} fast_first={frame%2}'

    def test_repeated_calls_preserved_and_summed(self):
        result = analyze('\n'.join([self.line(10),self.line(10,2.,4.),self.line(11)]),10,11,True)
        self.assertEqual(result['total_calls'],3)
        self.assertEqual(result['repeated_call_frames'],{'10':2})
        self.assertEqual(result['per_frame_sum']['fast_ms']['mean'],2.)
        self.assertEqual(result['verified_vertex_visits'],30)

    def test_missing_frame_rejected(self):
        with self.assertRaisesRegex(ValueError,'Missing'):
            analyze(self.line(10),10,11,True)

    def test_any_mismatch_rejected(self):
        with self.assertRaisesRegex(ValueError,'mismatch'):
            analyze(self.line(10)+'\nCrestHistoryHashAudit mismatch frame=99',10,10,True)

    def test_wrong_order_rejected(self):
        with self.assertRaisesRegex(ValueError,'Invalid'):
            analyze(self.line(10).replace('fast_first=0','fast_first=1'),10,10,True)


if __name__ == '__main__': unittest.main()
