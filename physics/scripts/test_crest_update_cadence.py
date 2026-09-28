import unittest

from audit_crest_update_cadence import COUNTERS, PREFIX, SCOPES, classify, read_capture, summarize
from audit_unreal_frame_csv import METRICS, WATER_SCOPES


def row(calls=1, changed=None, cost=2.):
    r = {PREFIX + n: 0. for n in COUNTERS}
    r[PREFIX + 'UpdateCalls'] = calls
    if changed:
        r[PREFIX + changed] = 1.
    r.update({SCOPES[0]: cost, SCOPES[1]: cost + 3.})
    return r


class Cadence(unittest.TestCase):
    def test_categories_do_not_conflate_more_calls_and_more_cost(self):
        rows = [row(), row(changed='XYChanged', cost=8.), row(2, cost=10.),
                row(changed='CoarseChanged'), row(0, cost=0.)]
        result = summarize(rows, 0, 4)
        self.assertEqual(result['aggregate']['update_calls'], 5)
        self.assertEqual(result['aggregate']['cpu'][SCOPES[0]]['aggregate_ms_per_crest_call'], 4.4)
        self.assertEqual(len(result['categories']), 5)
        self.assertIsNone(result['categories']['no_counted_update']['cpu'][SCOPES[0]]['aggregate_ms_per_crest_call'])
        self.assertIsNone(result['aggregate']['cpu'][SCOPES[1]]['aggregate_ms_per_crest_call'])

    def test_each_geometry_owner_is_classified(self):
        for n in ('XYChanged', 'IndicesChanged', 'ProfileChanged', 'DetailWindowChanged'):
            self.assertEqual(classify(row(changed=n)), 'single_geometry_changed')
        self.assertEqual(classify(row(changed='DenseHistoryUpdates')), 'single_targets_unchanged')

    def test_invalid_counts_scopes_and_intervals_rejected(self):
        for key, value in ((PREFIX+'UpdateCalls', .5), (PREFIX+'XYChanged', 2),
                           (PREFIX+'ShoreChanged', float('nan')), (SCOPES[0], -1),
                           (SCOPES[0], None), (SCOPES[0], True),
                           (SCOPES[0], float('inf'))):
            r = row(); r[key] = value
            with self.assertRaises(ValueError):
                classify(r)
        r = row(); del r[PREFIX+'UpdateCalls']
        with self.assertRaises(ValueError):
            classify(r)
        with self.assertRaises(ValueError):
            summarize([row()], 0, 1)

    def test_completed_csv_identity_and_missing_counter(self):
        names = list(dict.fromkeys(METRICS + WATER_SCOPES + tuple(PREFIX+n for n in COUNTERS)))
        def data(columns):
            header = ','.join(['EVENTS'] + columns)
            values = ['1' if n == PREFIX+'UpdateCalls' or n in METRICS else '0' for n in columns]
            return (header+'\n,'+','.join(values)+'\n'+header+'\n[HasHeaderRowAtEnd],1\n').encode()
        rows, _ = read_capture(data(names))
        self.assertEqual(len(rows), 1)
        self.assertEqual(classify(rows[0]), 'single_targets_unchanged')
        with self.assertRaises(ValueError):
            read_capture(data([n for n in names if n != PREFIX+'ShoreChanged']))

    def test_unavailable_early_counter_is_not_zero(self):
        names = list(dict.fromkeys(METRICS + WATER_SCOPES + tuple(PREFIX+n for n in COUNTERS)))
        header = ','.join(['EVENTS'] + names)
        raw = (header+'\n,'+','.join('1' for _ in names[:-1])+'\n'+header+
               '\n[HasHeaderRowAtEnd],1\n').encode()
        with self.assertRaises(ValueError):
            read_capture(raw)


if __name__ == '__main__':
    unittest.main()
