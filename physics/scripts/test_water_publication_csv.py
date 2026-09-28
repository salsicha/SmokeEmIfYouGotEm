import unittest

from audit_unreal_frame_csv import METRICS
from audit_water_publication_csv import COUNTERS, PAIRED, PREFIX, SCOPES, read_capture, summarize


def row(**counts):
    values = {PREFIX+n:float(counts.get(n,0)) for n in COUNTERS}
    values.update({name:0. for name in SCOPES})
    return values


def capture(columns, rows):
    header = ','.join(['EVENTS']+list(METRICS)+columns)
    lines = [header]
    lines.extend(',20,18,4,2,5,'+','.join(map(str,values)) for values in rows)
    return ('\n'.join(lines)+'\n'+header+'\n[HasHeaderRowAtEnd],1\n').encode()


class PublicationCsv(unittest.TestCase):
    def test_reason_partition_and_nested_costs(self):
        a = row(PublishCalls=1, PublishInterpolation=1)
        b = row(PublishCalls=2, PublishInterpolation=1, PublishRecenter=1,
                RecenterWorkCalls=1, CarryRenderedHistoryCalls=1, PlanarGeometryCalls=1)
        a[PREFIX+'GameThread/Tick'] = 10
        b[PREFIX+'GameThread/Tick'] = 80
        b[PREFIX+'GameThread/RecenterPublication'] = 20
        result = summarize([a,b],0,1)
        self.assertEqual(result['aggregate']['counts']['PublishCalls'],3)
        self.assertEqual(result['aggregate']['cpu'][PREFIX+'GameThread/Tick']['total_ms'],90)
        self.assertEqual(len(result['caller_groups']),2)
        self.assertEqual(result['events'][0]['sample_index'],1)
        self.assertEqual(result['events'][0]['counts']['PublishRecenter'],1)

    def test_inactive_missing_scope_is_unavailable_not_zero(self):
        a = row(PublishCalls=1, PublishInterpolation=1)
        del a[PREFIX+'GameThread/CreatePublication']
        result = summarize([a],0,0)
        scope = result['aggregate']['cpu'][PREFIX+'GameThread/CreatePublication']
        self.assertEqual(scope['available_rows'],0)
        self.assertIsNone(scope['total_ms'])
        self.assertIsNone(scope['mean_available_ms'])
        a[PREFIX+'PublishCalls'] = 2
        a[PREFIX+'PublishCreate'] = 1
        with self.assertRaises(ValueError):
            summarize([a],0,0)

    def test_scope_zero_does_not_erase_counted_call(self):
        a = row(PublishCalls=1, PublishHardSwap=1)
        self.assertEqual(summarize([a],0,0)['aggregate']['counts']['PublishHardSwap'],1)

    def test_no_count_inference_from_timing(self):
        a = row()
        a[PREFIX+'GameThread/RecenterWork'] = 4
        self.assertEqual(summarize([a],0,0)['events'],[])
        del a[PREFIX+'PublishCalls']
        with self.assertRaises(ValueError):
            summarize([a],0,0)

    def test_invalid_counts_and_partition_rejected(self):
        for value in (.5,-1,float('inf'),float('nan'),True,None):
            a = row(); a[PREFIX+'PublishCalls'] = value
            with self.subTest(value=value), self.assertRaises(ValueError):
                summarize([a],0,0)
        for a in (row(PublishCalls=1), row(PublishInterpolation=1)):
            with self.assertRaises(ValueError):
                summarize([a],0,0)

    def test_invalid_timings_and_active_missing_pairs_rejected(self):
        for value in (-1,float('inf'),float('nan'),True,None):
            a = row(); a[SCOPES[0]]=value
            with self.assertRaises(ValueError):
                summarize([a],0,0)
        for count,scope in PAIRED.items():
            a = row(**{count:1})
            if count.startswith('Publish'):
                a[PREFIX+'PublishCalls']=1
            del a[PREFIX+'GameThread/'+scope]
            with self.assertRaises(ValueError):
                summarize([a],0,0)

    def test_final_header_counts_and_intervals(self):
        columns = [PREFIX+n for n in COUNTERS]+list(SCOPES)
        a=row(PublishCalls=1, PublishInterpolation=1)
        data=capture(columns,[[a[n] for n in columns]])
        rows,_=read_capture(data)
        self.assertEqual(summarize(rows,0,0)['aggregate']['counts']['PublishCalls'],1)
        for first,last in ((-1,0),(1,0),(0,1)):
            with self.assertRaises(ValueError):
                summarize(rows,first,last)
        with self.assertRaises(ValueError):
            read_capture(data.replace(b'[HasHeaderRowAtEnd],1\n',b''))

    def test_missing_early_counter_and_ambiguous_series_are_not_zero(self):
        columns=[PREFIX+n for n in COUNTERS]
        raw=capture(columns,[[0]*(len(columns)-1)])
        with self.assertRaises(ValueError):
            read_capture(raw)
        columns.append(PREFIX+'PublishCalls')
        raw=capture(columns,[[0]*len(columns)])
        with self.assertRaises(ValueError):
            read_capture(raw, (PREFIX+'PublishCalls',))
        with self.assertRaises(ValueError):
            summarize([{}],0,0)

    def test_appended_scope_retains_unavailable_early_rows(self):
        columns=[PREFIX+n for n in COUNTERS]
        initial=','.join(['EVENTS']+list(METRICS)+columns)
        scope=PREFIX+'GameThread/InterpolationPublication'
        final=initial+','+scope
        a=row(); b=row(PublishCalls=1, PublishInterpolation=1)
        raw=(initial+'\n,20,18,4,2,5,'+','.join(str(a[n]) for n in columns)+
             '\n,20,18,4,2,5,'+','.join(str(b[n]) for n in columns)+',2\n'+
             final+'\n[HasHeaderRowAtEnd],1\n').encode()
        rows,_=read_capture(raw)
        self.assertNotIn(scope,rows[0])
        self.assertEqual(rows[1][scope],2)
        stats=summarize(rows,0,1)['aggregate']['cpu'][scope]
        self.assertEqual(stats['available_rows'],1)
        self.assertEqual(stats['mean_available_ms'],2)


if __name__ == '__main__':
    unittest.main()
