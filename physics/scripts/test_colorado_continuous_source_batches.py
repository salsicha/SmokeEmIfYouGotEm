import copy
import unittest
from build_colorado_continuous_source_batches import plan_batches


class SourceBatches(unittest.TestCase):
    def index(self):
        return dict(schema='raftsim.colorado_continuous_source_index.v1',route_length_m=3200.,
                    windows=[dict(tile_id=f'colorado_continuous_{i:04d}',name=f'Colorado continuous {i:04d}',
                                  source_core_interval_m=[lo,hi])
                             for i,(lo,hi) in enumerate(((0.,1200.),(1200.,2400.),(2400.,3200.)))])

    def test_full_tail_includes_partial_terminal_core(self):
        self.assertEqual(plan_batches(self.index(),0,batch_size=2),[[0,1],[2]])
        self.assertEqual(plan_batches(self.index(),1),[[1,2]])
        self.assertEqual(plan_batches(self.index(),1,2),[[1]])

    def test_bad_bounds_and_unbounded_batch_refused(self):
        for start,stop,size in ((-1,None,12),(3,None,12),(0,4,12),(2,1,12),(True,None,12),
                                (0,None,0),(0,None,13),(0,2.5,12)):
            with self.assertRaises(ValueError):plan_batches(self.index(),start,stop,size)

    def test_gap_overlap_identity_or_missing_endpoint_refused(self):
        for lo in (1199.,1201.,float('nan')):
            index=self.index();index['windows'][1]['source_core_interval_m'][0]=lo
            with self.assertRaises(ValueError):plan_batches(index,1)
        for key,value in (('tile_id','../foreign'),('name','Unrelated source')):
            index=self.index();index['windows'][1][key]=value
            with self.assertRaises(ValueError):plan_batches(index,1)
        index=copy.deepcopy(self.index());index['route_length_m']=3300.
        with self.assertRaises(ValueError):plan_batches(index,1)


if __name__=='__main__':unittest.main()
