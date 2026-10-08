import copy
import unittest
from types import SimpleNamespace
from unittest.mock import patch
import numpy as np
from review_chilko_continuous_cook import validate_native,validate_frame,wet_chart_metric,validate_source_reference,inlet_outlet_wet_path
from review_colorado_catalog_cook import compare
from chilko_native_friction import friction_contract
from review_chilko_continuous_cook import validate_initial_frame


class ChilkoCookReview(unittest.TestCase):
    def test_diagnostic_flow_cannot_be_exported_even_with_a_passing_screen(self):
        from review_chilko_continuous_cook import checked_cook
        for in_build in (True,False):
            marker={'runtime_promotion_authorized':True}
            build={'fixed_bed_flow_sensitivity':marker} if in_build else {}
            scenario={'metadata':{'provenance':{} if in_build else {'fixed_bed_flow_sensitivity':marker}}}
            with patch('review_chilko_continuous_cook.read_inputs',
                       return_value=(build,scenario,None,None,None,None,{})):
                with self.assertRaisesRegex(ValueError,'not a production runtime source'):
                    checked_cook(None,None,None)

    def test_restart_all_state_fields_are_bound(self):
        initial={k:np.ones((2,3)) for k in ('depth','eta','u','v','hu','hv','wet')}
        frame={('h' if k=='depth' else k):v.copy() for k,v in initial.items()}
        validate_initial_frame(frame,initial)
        for key in frame:
            bad=copy.deepcopy(frame);bad[key][0,0]+=.01
            with self.subTest(key=key),self.assertRaisesRegex(ValueError,'initial inputs'):
                validate_initial_frame(bad,initial)

    def test_restart_refuses_broadcast_shape_and_nonfinite_state(self):
        initial={k:np.ones((2,3)) for k in ('depth','eta','u','v','hu','hv','wet')}
        frame={('h' if k=='depth' else k):v.copy() for k,v in initial.items()}
        for bad_value in (np.ones((1,3)),np.full((2,3),np.nan),np.full((2,3),np.inf)):
            bad=copy.deepcopy(initial);bad['hu']=bad_value
            with self.assertRaisesRegex(ValueError,'initial inputs'):
                validate_initial_frame(frame,bad)

    def test_wet_columns_do_not_hide_disconnected_puddles(self):
        h=np.eye(4)
        self.assertTrue((h>.05).any(axis=0).all())
        self.assertFalse(inlet_outlet_wet_path(dict(h=h)))
        h[1,:]=.06
        self.assertTrue(inlet_outlet_wet_path(dict(h=h)))
        h[:,2]=.05
        self.assertFalse(inlet_outlet_wet_path(dict(h=h)))

    def test_water_path_refuses_missing_or_nonfinite_depth(self):
        for h in (np.array([]),np.zeros((0,2)),np.array([[1.,np.nan]])):
            with self.assertRaises(ValueError):inlet_outlet_wet_path(dict(h=h))

    def test_source_review_batches_adjacent_columns_not_whole_river_lateral_rows(self):
        rows,cols=np.indices((257,600));queries=np.stack((cols,rows),axis=-1).astype(float)
        calls=[]
        def sample(xy):
            calls.append((len(xy),float(np.ptp(xy[:,0]))))
            return dict(mapped_water=np.ones(len(xy),bool),source_height_m=100.+xy[:,0]/100,
                source_kind=np.ones(len(xy),np.uint8),ownership_reference_m=100.+xy[:,0]/100,
                reference_m=101.+xy[:,0]/100)
        source=sample(queries.reshape(-1,2));calls.clear()
        keys=dict(river='mapped_water',dem2021='source_height_m',source_kind='source_kind',
            ownership_reference='ownership_reference_m',ws_reference_grid='reference_m')
        reference={k:source[v].reshape(rows.shape) for k,v in keys.items()}
        reference['channel']=np.ones(rows.shape,bool)
        validate_source_reference(reference,queries,SimpleNamespace(sample=sample))
        self.assertEqual(len(calls),3)
        self.assertTrue(all(count<=65536 and span<=254 for count,span in calls))

    def test_shoreline_review_cannot_change_its_source_mask_or_ownership(self):
        queries=np.array([[[0.,0.],[1.,0.],[2.,0.]]])
        source=dict(mapped_water=np.array([False,True,True]),source_height_m=np.array([102.,100.,101.]),
            source_kind=np.ones(3,dtype=np.uint8),ownership_reference_m=np.array([np.nan,100.,100.]),
            reference_m=np.array([np.nan,100.5,100.5]))
        model=SimpleNamespace(sample=lambda xy:source)
        reference=dict(river=source['mapped_water'][None,:],dem2021=source['source_height_m'][None,:],
            source_kind=source['source_kind'][None,:],ownership_reference=source['ownership_reference_m'][None,:],
            ws_reference_grid=source['reference_m'][None,:],channel=np.array([[False,True,False]]))
        validate_source_reference(reference,queries,model)
        for key in reference:
            bad=copy.deepcopy(reference)
            if bad[key].dtype.kind=='b':bad[key][0,2]=~bad[key][0,2]
            else:bad[key][0,1]+=1
            with self.subTest(key=key),self.assertRaisesRegex(ValueError,'source reference changed'):
                validate_source_reference(bad,queries,model)

    def test_review_compares_cellwise_surface_without_changing_legacy_columns(self):
        wet=np.ones((3,4),bool);surface=np.arange(12.).reshape(3,4)+100.
        frame=dict(h=np.ones((3,4)),eta=surface+.2,u=np.ones((3,4)),v=np.zeros((3,4)))
        ref=dict(classified_water=wet,reference_surface=surface,station=np.arange(4.))
        stats=compare(ref,frame,frame,2.)
        self.assertAlmostEqual(stats['surface_error_abs_p95_m'],.2)
        ref['reference_surface']=np.arange(4.)+100.
        frame['eta']=np.broadcast_to(ref['reference_surface'][None,:],(3,4))+.3
        self.assertAlmostEqual(compare(ref,frame,frame,2.)['surface_error_abs_p95_m'],.3)
        ref['reference_surface']=np.zeros((4,3))
        with self.assertRaises(ValueError):compare(ref,frame,frame,2.)

    def test_newly_wetted_fold_is_not_hidden_by_initial_source_mask(self):
        ref=dict(curvature=np.array([.02,.01]),lateral=np.array([0.,40.,80.]))
        h=np.array([[1.,1.],[0.,0.],[0.,0.]])
        self.assertEqual(wet_chart_metric(dict(h=h),ref),1.)
        h[2,0]=.1
        self.assertAlmostEqual(wet_chart_metric(dict(h=h),ref),-.6)
        with self.assertRaises(ValueError):wet_chart_metric(dict(h=np.zeros((3,2))),ref)

    def setUp(self):
        self.scenario=dict(metadata=dict(scenario_id='chilko_native'))
        self.native=dict(solver_mode='finite_volume',boundary_mode='scenario',flux_scheme='hll',spatial_order=2,
            cfl=.2,feature_strength_scale=0,roughness_scale=1,bed_slope_source_scale=1,
            preserve_initial_mass=False,disable_fixture_calibrations=True,experimental_west_discharge_m3s=-1,
            experimental_west_supercritical_stage=False,scenario_id='chilko_native')
        self.validation=dict(passed=True,finite_state=True,velocity_limit_reached=False)

    def test_only_reviewed_native_configuration_allowed(self):
        validate_native(self.native,self.validation,self.scenario)
        for key,value in [('solver_mode','reference'),('feature_strength_scale',1),
                ('spatial_order',1),('preserve_initial_mass',True),('disable_fixture_calibrations',False),
                ('scenario_id','another'),('bed_slope_source_scale',0),('roughness_scale',2),
                ('experimental_west_discharge_m3s',45),('experimental_west_supercritical_stage',True)]:
            native=dict(self.native);native[key]=value
            with self.subTest(key=key),self.assertRaisesRegex(ValueError,'Unreviewed'):
                validate_native(native,self.validation,self.scenario)

    def test_failed_or_clipped_native_state_refused(self):
        for key,value in [('passed',False),('finite_state',False),('velocity_limit_reached',True)]:
            validation=dict(self.validation);validation[key]=value
            with self.subTest(key=key),self.assertRaisesRegex(ValueError,'validation failed'):
                validate_native(self.native,validation,self.scenario)

    def test_full_corridor_cannot_be_accepted_with_manning_as_native_coefficient(self):
        s=copy.deepcopy(self.scenario)
        s['metadata'].update(generator='build_chilko_corridor_scenario.py',
            provenance=dict(continuous_terrain=dict(manning_n=.045)))
        s['roughness']=.045
        with self.assertRaisesRegex(ValueError,'friction'):validate_native(self.native,self.validation,s)
        c=friction_contract(.045)
        s['metadata']['provenance']['friction']=c
        with self.assertRaisesRegex(ValueError,'friction'):validate_native(self.native,self.validation,s)
        s['roughness']=c['native_roughness_coefficient']
        validate_native(self.native,self.validation,s)

    def test_same_shape_different_bed_or_world_position_is_not_same_cook(self):
        bed=np.full((3,4),950.);r,c=np.indices(bed.shape)
        grid=dict(origin_x=0,origin_y=-2,dx=2,dy=2)
        frame=dict(x=c*2.,y=r*2.-2,h=np.ones(bed.shape),eta=bed+1)
        validate_frame(frame,bed,grid)
        for key in ('x','y','eta','h'):
            bad=copy.deepcopy(frame);bad[key][1,1]+=.01
            with self.subTest(key=key),self.assertRaisesRegex(ValueError,'input grid and bed'):
                validate_frame(bad,bed,grid)


if __name__=='__main__':unittest.main()
