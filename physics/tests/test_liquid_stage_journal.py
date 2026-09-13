import copy
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from liquid_stage_journal import stage_groups


class StageJournalTest(unittest.TestCase):
    def report(self):
        entry=dict(owner=0,name='Spawn',stage=0,iteration=0,iterations=1,loop=0,loops=1,
                   first=True,last=False,reset=False,native_rate_spawns=17,native_event_spawns=0)
        template=dict(simulation_generation='generation',complete=True,aligned=True,entries=[entry])
        return dict(groups=[],simulation_generation='generation',records_truncated=False,
                    complete_aligned_groups=3,incomplete_groups=0,misaligned_groups=0,
                    stage_journal=dict(schema='raftsim.liquid_stage_journal.v1',failed=False,record_count=3,
                                       template_chars=512,templates=[template],records=[[1,4,0],[1,5,0],[2,0,0]]))

    def test_lossless_repetition_and_legacy(self):
        r=self.report();groups=list(stage_groups(r))
        self.assertEqual([(g['render_frame'],g['graph_group']) for g in groups],[(1,4),(1,5),(2,0)])
        self.assertEqual([g['entries'][0]['native_rate_spawns'] for g in groups],[17]*3)
        self.assertEqual(groups,list(stage_groups(dict(groups=groups))))

    def test_omission_overflow_and_ambiguous_storage_rejected(self):
        for edit in (lambda r:r['stage_journal']['records'].pop(),
                     lambda r:r['stage_journal'].update(failed=True),
                     lambda r:r.update(records_truncated=True),
                     lambda r:r.update(groups=[{}]),
                     lambda r:r.update(complete_aligned_groups=2),
                     lambda r:r['stage_journal'].update(template_chars=8*1024*1024+1)):
            r=self.report();edit(r)
            with self.assertRaises(ValueError):list(stage_groups(r))

    def test_bad_addresses_and_stale_templates_rejected(self):
        for row in ([1,4,1],[1,4,-1],[1,4,True],[1,4],[1,4,0,0],[2**32,0,0]):
            r=self.report();r['stage_journal']['records'][0]=row
            with self.assertRaises(ValueError):list(stage_groups(r))
        r=self.report();r['stage_journal']['templates'][0]['simulation_generation']='old'
        with self.assertRaisesRegex(ValueError,'stale'):list(stage_groups(r))

    def test_distinct_births_iteration_reset_and_misalignment_retained(self):
        r=self.report();t=copy.deepcopy(r['stage_journal']['templates'][0]);t['aligned']=False
        t['entries'][0].update(native_rate_spawns=99,iteration=2,reset=True)
        r['stage_journal']['templates'].append(t);r['stage_journal']['records'][1][2]=1
        r.update(complete_aligned_groups=2,misaligned_groups=1)
        g=list(stage_groups(r))[1]
        self.assertFalse(g['aligned']);self.assertTrue(g['entries'][0]['reset'])
        self.assertEqual(g['entries'][0]['native_rate_spawns'],99)
        self.assertEqual(g['entries'][0]['iteration'],2)

    def test_invalid_entry_or_false_alignment_rejected(self):
        for field,value in [('owner',12),('native_rate_spawns',-1),('reset',1),('loop',2.5)]:
            r=self.report();r['stage_journal']['templates'][0]['entries'][0][field]=value
            with self.assertRaises(ValueError):list(stage_groups(r))
        r=self.report();r['stage_journal']['templates'][0]['complete']=False
        with self.assertRaises(ValueError):list(stage_groups(r))


if __name__=='__main__':unittest.main()
