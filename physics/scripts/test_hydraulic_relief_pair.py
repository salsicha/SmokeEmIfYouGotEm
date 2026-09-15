import copy
import unittest
from audit_hydraulic_relief_pair import summarize


def fixture():
    return dict(schema='raftsim.cartesian_hydraulic_relief_pair.v1', release_accepted=False,
        rows=[dict(world_seconds=10+i*.1, parallel_first=bool(i%2), vertices=100,
                   nonzero_relief_vertices=32, different_float_bits=0, serial_ms=2., parallel_ms=1.) for i in range(64)])


class ReliefPairTest(unittest.TestCase):
    def test_exact_pair_scope_and_both_orders(self):
        result = summarize(fixture())
        self.assertTrue(result['exact_float_comparison_passed'])
        self.assertTrue(result['measured_both_orders_faster'])
        self.assertEqual(result['compared_vertices'], 6400)
        self.assertEqual(result['groups']['parallel_first']['pairs'], 32)
        self.assertFalse(result['release_accepted'])

    def test_mismatch_and_order_regression_are_not_hidden_by_total_means(self):
        value = fixture()
        value['rows'][0]['different_float_bits'] = 1
        self.assertFalse(summarize(value)['exact_float_comparison_passed'])
        for row in value['rows'][1::2]:
            row['parallel_ms'] = 2.1
        self.assertFalse(summarize(value)['measured_both_orders_faster'])

    def test_missing_duplicate_empty_nonfinite_or_inconsistent_evidence_rejects(self):
        good = fixture()
        cases = []
        for key, replacement in [('vertices', -1), ('vertices', 1.5), ('vertices', True),
                                 ('nonzero_relief_vertices', 0), ('nonzero_relief_vertices', 101),
                                 ('different_float_bits', 101), ('serial_ms', 0),
                                 ('parallel_ms', float('nan')), ('world_seconds', 9),
                                 ('world_seconds', 10), ('parallel_first', False)]:
            value = copy.deepcopy(good)
            value['rows'][1][key] = replacement
            cases.append(value)
        value = copy.deepcopy(good); value['rows'].pop(); cases.append(value)
        value = copy.deepcopy(good); value['release_accepted'] = True; cases.append(value)
        for value in cases:
            with self.subTest(value=value['rows'][1]), self.assertRaises(ValueError):
                summarize(value)


if __name__ == '__main__':
    unittest.main()
