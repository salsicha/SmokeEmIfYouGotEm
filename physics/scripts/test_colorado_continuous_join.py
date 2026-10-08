import copy
import unittest
import tempfile
from unittest.mock import patch
from pathlib import Path

import numpy as np

from join_colorado_continuous_scenarios import merge_registered, write_native_arrays,initial_conveyance_velocity,validate_reinitialization_contract,sample_owned_classification,sample_grid,registered_query_blocks,sample_registered_terrain,sample_registered_classification
from join_colorado_continuous_scenarios import iter_join_items, load_join_item


class ContinuousJoin(unittest.TestCase):
    def test_classification_in_outer_half_pixel_uses_existing_pixel_only(self):
        source=dict(grid=dict(classified_water_mask=np.array([[1,0],[0,1]],bool),
                              corner_east_north_m=np.array([100.,202.])))
        points=np.array([[100.,202.],[100.1,201.9],[101.9,201.9],[102.,202.],
                         [100.,200.],[100.1,200.1],[101.9,200.1],[102.,200.]])
        actual=sample_owned_classification([source],points,np.zeros(len(points),np.int32))
        np.testing.assert_array_equal(actual,[1,1,0,0,0,0,1,1])
        for point in ([99.999,201.],[102.001,201.],[101.,202.001],[101.,199.999]):
            with self.subTest(point=point),self.assertRaisesRegex(ValueError,'outside source pixel'):
                sample_owned_classification([source],np.array([point]),np.zeros(1,np.int32))

    def test_inplace_conveyance_preserves_full_array_calculation(self):
        rng=np.random.default_rng(192)
        for depth in (rng.uniform(.01,20,(17,31)),np.asfortranarray(rng.uniform(.01,20,(17,31)))):
            depth[0,::3]=0
            old=np.where(depth>0,23.*depth**(2/3)/((depth**(5/3)).sum(axis=0)*2.)[None,:],0.)
            actual=initial_conveyance_velocity(depth,2.,23.)
            np.testing.assert_array_equal(actual,old)

    def test_lazy_packages_preserve_merge_and_cropped_registration(self):
        with tempfile.TemporaryDirectory(prefix='raftsim-lazy-join-') as temporary:
            descriptors=[]
            for i,item in enumerate(self.initial_items()):
                folder=Path(temporary)/str(i);pkg=folder/'scenario';pkg.mkdir(parents=True)
                write_native_arrays(pkg,item['bed'],item['depth'],item['u'],item['v'])
                np.savez_compressed(folder/'reference.npz',classified_water=item['classified_water'],
                                    reference_surface=item['reference_surface'])
                descriptors.append(dict(folder=folder,grid=item['grid']))
            station=100.+np.arange(7)*2.
            with patch('join_colorado_continuous_scenarios.load_join_item',wraps=load_join_item) as loader:
                iterator=iter_join_items(descriptors,station,2.)
                self.assertEqual(loader.call_count,0)
                first=next(iterator);self.assertEqual(loader.call_count,1)
                np.testing.assert_array_equal(first['bed'],self.items[0]['bed'])
            expected=merge_registered(self.initial_items(),self.bed,self.grid,self.padding,initial_discharge=10.)
            actual=merge_registered(iter_join_items(descriptors,station,2.),self.bed,self.grid,self.padding,initial_discharge=10.)
            for key in expected[0]:np.testing.assert_array_equal(actual[0][key],expected[0][key])
            for a,b in zip(actual[1:],expected[1:]):np.testing.assert_array_equal(a,b)
            cropped=list(iter_join_items(descriptors,station[1:-1],2.))
            self.assertEqual(cropped[0]['grid']['origin_x'],102.)
            self.assertEqual(cropped[0]['grid']['nx'],3)
            self.assertEqual(cropped[1]['grid']['nx'],3)
            for key in ('bed','depth','u','v','classified_water'):
                np.testing.assert_array_equal(cropped[0][key],self.initial_items()[0][key][:,1:])

    def test_single_pass_merge_checks_later_source(self):
        items=self.initial_items();items[1]['u'][1,1]+=.01
        with self.assertRaisesRegex(ValueError,'un-cooked'):
            merge_registered(iter(items),self.bed,self.grid,self.padding,initial_discharge=10.)

    def test_incremental_npz_preserves_all_saved_arrays_exactly(self):
        rng=np.random.default_rng(17)
        with tempfile.TemporaryDirectory(prefix='raftsim-npz-join-') as temporary:
            pkg=Path(temporary)
            for transposed in (False,True):
                bed,h,u,v=[rng.uniform(.1,30,(9,13)) for _ in range(4)]
                if transposed:bed,h,u,v=(a.T for a in (bed,h,u,v))
                expected=dict(depth=h,eta=bed+h,u=u,v=v,hu=h*u,hv=h*v,wet=h>1e-6)
                write_native_arrays(pkg,bed,h,u,v)
                self.assertFalse((pkg/'initial_state.npz.partial').exists())
                with np.load(pkg/'initial_state.npz',allow_pickle=False) as saved:
                    self.assertEqual(saved.files,list(expected))
                    for key,value in expected.items():
                        np.testing.assert_array_equal(saved[key],value)
                        self.assertTrue(saved[key].flags.c_contiguous)

    def test_bounded_queries_preserve_every_coordinate_and_terrain_sample(self):
        xy=np.array([[float(i),float(i*i)] for i in range(7)])
        angle=np.arange(7)*.1
        normal=np.column_stack((np.cos(angle),np.sin(angle)))
        lateral=np.arange(-4.,6.,2.)
        expected=xy[:,None,:]+normal[:,None,:]*lateral[None,:,None]
        blocks=list(registered_query_blocks(xy,normal,lateral,max_points=12))
        np.testing.assert_array_equal(np.concatenate([q for _,q in blocks]),expected)
        self.assertTrue(all(q.shape[0]*q.shape[1]<=12 for _,q in blocks))
        class Triangles:
            def sample(self,q):return q[...,0]+3*q[...,1]
        actual=sample_registered_terrain(Triangles(),xy,normal,lateral,max_points=12)
        np.testing.assert_array_equal(actual,(expected[...,0]+3*expected[...,1]).T)

    def test_bounded_queries_reject_invalid_grid_and_budget(self):
        xy=np.array([[0.,0.],[2.,0.]]);normal=np.array([[0.,1.],[0.,1.]])
        for lateral,budget in (([-2.,0.,2.],2),([0.,0.],4),([0.,float('nan')],4),([-2.,2.],2.5)):
            with self.assertRaisesRegex(ValueError,'registered query'):
                list(registered_query_blocks(xy,normal,lateral,budget))
        with self.assertRaisesRegex(ValueError,'registered query'):
            list(registered_query_blocks(xy,normal[:1],[-2.,2.]))

    def test_bounded_classification_preserves_values_and_missing_source_refusal(self):
        sources,queries,owner=self.classification_fixture()
        class Mosaic:
            def __init__(self):self.sources=sources;self.missing=False;self.counts=[]
            def sample(self,east,north):
                self.counts.append(east.size)
                found=(east>=2).astype(np.int32)
                if self.missing:found[0,0]=-1
                return np.zeros_like(east),found
        # Source queries are (station,column) here: one station per east value.
        xy=np.column_stack((queries[0,:,0],np.ones(4)))
        normal=np.tile([0.,1.],(4,1));lateral=np.array([-.5,.5])
        full=xy[:,None,:]+normal[:,None,:]*lateral[None,:,None]
        expected=sample_owned_classification(sources,full,(full[...,0]>=2).astype(np.int32)).T
        mosaic=Mosaic()
        actual=sample_registered_classification(mosaic,xy,normal,lateral,max_points=4)
        np.testing.assert_array_equal(actual,expected)
        self.assertEqual(mosaic.counts,[4,4])
        mosaic.missing=True
        with self.assertRaisesRegex(ValueError,'Missing classified'):
            sample_registered_classification(mosaic,xy,normal,lateral,max_points=4)

    def classification_fixture(self):
        sources=[dict(grid=dict(classified_water_mask=np.array([[1,0],[0,1]],bool),
                               corner_east_north_m=[x,2.])) for x in (0.,2.)]
        east,north=np.meshgrid([.5,1.5,2.5,3.5],[1.5,.5])
        queries=np.stack((east,north),axis=-1)
        owner=np.array([[0,0,1,1],[0,0,1,1]],dtype=np.int32)
        return sources,queries,owner

    def test_owned_classification_matches_full_sampling_with_one_query_per_cell(self):
        sources,queries,owner=self.classification_fixture()
        expected=np.zeros(owner.shape,bool)
        for i,source in enumerate(sources):
            g=source['grid']
            values=sample_grid(g['classified_water_mask'],queries,g['corner_east_north_m'],True)
            expected[owner==i]=values[owner==i]>.5
        with patch('join_colorado_continuous_scenarios.sample_grid',wraps=sample_grid) as sampler:
            actual=sample_owned_classification(sources,queries,owner)
        np.testing.assert_array_equal(actual,expected)
        self.assertEqual(sum(call.args[1].shape[0] for call in sampler.call_args_list),owner.size)
        self.assertEqual([call.args[1].shape for call in sampler.call_args_list],[(4,2),(4,2)])

    def test_owned_classification_does_not_hide_missing_or_invalid_coverage(self):
        sources,queries,owner=self.classification_fixture()
        for bad in (-1,2):
            changed=owner.copy();changed[0,0]=bad
            with self.assertRaisesRegex(ValueError,'ownership'):
                sample_owned_classification(sources,queries,changed)
        with self.assertRaisesRegex(ValueError,'ownership'):
            sample_owned_classification(sources,queries,owner.astype(float))
        with self.assertRaisesRegex(ValueError,'ownership'):
            sample_owned_classification(sources,queries[:-1],owner)
        changed=owner.copy();changed[0,0]=1
        with self.assertRaisesRegex(ValueError,'Unclassified'):
            sample_owned_classification(sources,queries,changed)
        queries[0,0,0]=np.nan
        with self.assertRaisesRegex(ValueError,'ownership'):
            sample_owned_classification(sources,queries,owner)

    def test_owned_classification_skips_unreferenced_sources(self):
        sources,queries,owner=self.classification_fixture()
        sources.append(dict(grid=None))
        self.assertEqual(sample_owned_classification(sources,queries,owner).sum(),4)

    def test_transposed_terrain_serializes_row_major_without_moving_values(self):
        bed = np.arange(35., dtype=float).reshape(7, 5).T
        self.assertTrue(bed.flags.f_contiguous)
        h, u, v = bed*.01+1., bed*.02, bed*0.
        with tempfile.TemporaryDirectory() as folder:
            pkg = Path(folder)
            write_native_arrays(pkg, bed, h, u, v)
            actual = np.load(pkg/'bed.npy')
            self.assertTrue(actual.flags.c_contiguous)
            np.testing.assert_array_equal(actual, bed)
            with np.load(pkg/'initial_state.npz') as state:
                for key in state.files:
                    self.assertTrue(state[key].flags.c_contiguous, key)
                np.testing.assert_allclose(state['eta']-actual, h, atol=1e-14, rtol=0)

    def setUp(self):
        self.grid = dict(nx=7, ny=5, dx=2., dy=2., origin_x=100., origin_y=-4.)
        self.bed = np.ones((5, 7))*20.
        self.padding = np.zeros((5, 7), bool)
        self.items = []
        for start, ny in ((100., 5), (106., 3)):
            self.items.append(dict(grid=dict(nx=4, ny=ny, dx=2., dy=2., origin_x=start,
                                            origin_y=-(ny-1)),
                bed=np.ones((ny, 4))*20., depth=np.ones((ny, 4))*2.,
                u=np.ones((ny, 4))*.5, v=np.zeros((ny, 4)),
                classified_water=np.ones((ny, 4), bool), reference_surface=np.ones(4)*22.))

    def run_merge(self, items=None):
        return merge_registered(self.items if items is None else items, self.bed, self.grid, self.padding)

    def test_exact_overlap_and_explicit_dry_padding(self):
        state, mask, surface, covered = self.run_merge()
        self.assertEqual(int((~covered).sum()), 6)
        self.assertTrue(np.array_equal(mask, covered))
        self.assertTrue((surface == 22).all())
        self.assertTrue((state['depth'][~covered] == 0).all())
        self.assertTrue((state['depth'][covered] == 2).all())

    def test_conflicting_state_is_not_blended(self):
        for key in ('depth', 'u', 'v'):
            items = copy.deepcopy(self.items)
            items[1][key][1, 0] += .001
            with self.assertRaisesRegex(ValueError, 'states disagree'):
                self.run_merge(items)

    def test_terrain_mismatch_refused(self):
        self.items[1]['bed'][1, 0] += .01
        with self.assertRaisesRegex(ValueError, 'rendered triangles'):
            self.run_merge()

    def test_missing_wet_padding_refused(self):
        self.padding[0, -1] = True
        with self.assertRaisesRegex(ValueError, 'classified water'):
            self.run_merge()

    def test_fractional_lattice_refused(self):
        self.items[1]['grid']['origin_x'] += .2
        with self.assertRaisesRegex(ValueError, 'exact cell lattice'):
            self.run_merge()

    def test_stage_or_classification_conflict_refused(self):
        items = copy.deepcopy(self.items)
        items[1]['reference_surface'][0] += .01
        with self.assertRaisesRegex(ValueError, 'stage references'):
            self.run_merge(items)
        self.items[1]['classified_water'][1, 0] = False
        with self.assertRaisesRegex(ValueError, 'classifications disagree'):
            self.run_merge()

    def initial_items(self):
        items=copy.deepcopy(self.items)
        for item in items:item['u']=initial_conveyance_velocity(item['depth'],item['grid']['dy'],10.)
        return items

    def test_side_channel_initial_discharge_rebuilt_not_averaged(self):
        items=self.initial_items();old=copy.deepcopy(items)
        with self.assertRaisesRegex(ValueError,'states disagree'):self.run_merge(items)
        state,mask,surface,covered=merge_registered(items,self.bed,self.grid,self.padding,initial_discharge=10.)
        np.testing.assert_allclose((state['depth']*state['u']).sum(axis=0)*2.,10.,atol=1e-12,rtol=0)
        self.assertAlmostEqual(state['u'][2,3],.5)
        self.assertAlmostEqual(state['u'][2,-1],5/6)
        for a,b in zip(items,old):
            for key in ('bed','depth','u','v','classified_water','reference_surface'):np.testing.assert_array_equal(a[key],b[key])

    def test_reconstruction_cannot_consume_cooked_or_modified_states(self):
        for key in ('u','v','depth'):
            items=self.initial_items();items[1][key][1,0]+=.001
            with self.subTest(key=key),self.assertRaises(ValueError):
                merge_registered(items,self.bed,self.grid,self.padding,initial_discharge=10.)
        items=self.initial_items();self.padding[0,-1]=True
        with self.assertRaisesRegex(ValueError,'classified water'):
            merge_registered(items,self.bed,self.grid,self.padding,initial_discharge=10.)

    def test_only_explicit_uncooked_source_receipts_are_eligible(self):
        report=dict(solved=False,accepted=False)
        scenario=dict(metadata=dict(generator='build_colorado_catalog_scenario.py'),feature_count=0,probe_count=0)
        validate_reinitialization_contract(report,scenario)
        for changed in ({},dict(solved=True,accepted=False),dict(solved=False,accepted=True)):
            with self.assertRaisesRegex(ValueError,'un-cooked'):validate_reinitialization_contract(changed,scenario)
        scenario['metadata']['generator']='native_cook'
        with self.assertRaises(ValueError):validate_reinitialization_contract(report,scenario)

    def test_invalid_initial_discharge_and_dry_section_rejected(self):
        for q in (0,-1,float('nan')):
            with self.assertRaises(ValueError):initial_conveyance_velocity(np.ones((3,2)),2,q)
        with self.assertRaisesRegex(ValueError,'Dry'):initial_conveyance_velocity(np.zeros((3,2)),2,10)


if __name__ == '__main__':
    unittest.main()
