import unittest
import numpy as np
from review_colorado_catalog_cook import compare,core_reviews,validate_native_frame,validate_native_source


class CookReviewTests(unittest.TestCase):
    def test_native_validation_block_boundaries_preserve_refusals(self):
        bed=np.full((7,11),900.)
        grid=dict(nx=11,ny=7,dx=2.,dy=2.,origin_x=1000.,origin_y=-6.)
        rows,cols=np.indices(bed.shape)
        frame=dict(x=grid['origin_x']+cols*2.,y=rows*2.-6.,h=np.ones(bed.shape),
                   eta=bed+1.,u=np.ones(bed.shape),v=np.zeros(bed.shape),
                   hu=np.ones(bed.shape),hv=np.zeros(bed.shape),wet=np.ones(bed.shape))
        initial={('depth' if k=='h' else k):v.copy() for k,v in frame.items() if k not in ('x','y')}
        for budget in (11,22,77,262144):
            validate_native_frame(frame,bed,grid,initial,max_points=budget)
            for field in frame:
                bad={k:v.copy() for k,v in frame.items()};bad[field][-1,-1]=np.nan
                with self.subTest(budget=budget,field=field),self.assertRaises(ValueError):
                    validate_native_frame(bad,bed,grid,initial,max_points=budget)
            bad_initial={k:v.copy() for k,v in initial.items()};bad_initial['hv'][-1,-1]+=.01
            with self.assertRaisesRegex(ValueError,'saved initial'):
                validate_native_frame(frame,bed,grid,bad_initial,max_points=budget)
        with self.assertRaisesRegex(ValueError,'block budget'):
            validate_native_frame(frame,bed,grid,max_points=10)

    def test_native_first_frame_must_match_bed_grid_and_restart(self):
        bed=np.full((2,3),900.)
        grid=dict(nx=3,ny=2,dx=2.,dy=2.,origin_x=1000000.,origin_y=-2.)
        rows,cols=np.indices(bed.shape)
        frame=dict(x=grid['origin_x']+cols*2,y=rows*2-2.,h=np.ones(bed.shape),
                   eta=bed+1,u=np.ones(bed.shape),v=np.zeros(bed.shape),
                   hu=np.ones(bed.shape),hv=np.zeros(bed.shape),wet=np.ones(bed.shape))
        initial={('depth' if k=='h' else k):v.copy() for k,v in frame.items() if k not in ('x','y')}
        validate_native_frame(frame,bed,grid,initial)
        for key in frame:
            bad={k:v.copy() for k,v in frame.items()};bad[key][0,0]=np.nan
            with self.subTest(nonfinite=key),self.assertRaises(ValueError):
                validate_native_frame(bad,bed,grid,initial)
        for key in ('x','eta','hu'):
            bad={k:v.copy() for k,v in frame.items()};bad[key][0,0]+=.01
            with self.subTest(changed=key),self.assertRaises(ValueError):
                validate_native_frame(bad,bed,grid,initial)

    def test_native_configuration_and_validation_cannot_be_omitted(self):
        native=dict(solver_mode='finite_volume',boundary_mode='scenario',flux_scheme='hll',
            spatial_order=2,cfl=.2,feature_strength_scale=0,roughness_scale=1,
            bed_slope_source_scale=1,preserve_initial_mass=False,disable_fixture_calibrations=True,
            experimental_west_discharge_m3s=-1,experimental_west_supercritical_stage=False,
            scenario_id='test')
        validation=dict(passed=True,finite_state=True,velocity_limit_reached=False)
        scenario=dict(metadata=dict(scenario_id='test'))
        validate_native_source(native,validation,scenario)
        for key in native:
            bad=native.copy();del bad[key]
            with self.subTest(missing=key),self.assertRaises(ValueError):
                validate_native_source(bad,validation,scenario)
        for key in validation:
            bad=validation.copy();bad[key]=not bad[key]
            with self.subTest(validation=key),self.assertRaises(ValueError):
                validate_native_source(native,bad,scenario)

    def test_joined_average_cannot_hide_bad_core(self):
        source=np.zeros((10,101),bool);source[2:8]=True
        wet=source.copy();wet[:,:10]=True
        ref=dict(classified_water=source,reference_surface=np.full(101,100.),
                 station=np.arange(101)*2.,source_station=np.arange(101)*2.)
        f=dict(h=wet.astype(float),eta=np.full(wet.shape,100.),u=wet.astype(float),v=np.zeros(wet.shape))
        self.assertGreater(compare(ref,f,f,2.)['wet_intersection_over_union'],.9)
        cores=core_reviews(ref,f,f,np.full(102,20.),20.,2.,[(0,20),(20,200)])
        self.assertFalse(cores[0]['construction_screen_passed'])
        self.assertTrue(cores[1]['construction_screen_passed'])

    def test_missing_registered_core_refused(self):
        with self.assertRaisesRegex(ValueError,'registered core'):
            core_reviews(dict(source_station=np.arange(10)),{},{},np.ones(11),1.,2.,[(20,30)])

    def test_partial_core_overlap_is_not_full_coverage(self):
        for interval in [(-1,5),(4,12),(-1,12),(5,5),(8,3),(0,np.inf)]:
            with self.subTest(interval=interval), self.assertRaisesRegex(ValueError,'registered core'):
                core_reviews(dict(source_station=np.arange(10)),{},{},np.ones(11),1.,2.,[interval])

    def test_invalid_source_station_axis_refused(self):
        for stations in [[0,1,1,3],[0,2,1,3],[0,np.nan,3],[],[[0,1],[2,3]]]:
            with self.subTest(stations=stations), self.assertRaisesRegex(ValueError,'registered core'):
                core_reviews(dict(source_station=np.array(stations)),{},{},np.ones(5),1.,2.,[(0,3)])

    def test_exact_match_reports_no_error_or_spreading(self):
        source=np.zeros((8,10),bool);source[2:6]=True
        ref=dict(classified_water=source,reference_surface=np.full(10,100.),station=np.arange(10)*2.)
        fields=dict(h=source.astype(float),eta=np.full(source.shape,100.),u=np.zeros(source.shape),v=np.zeros(source.shape))
        result=compare(ref,fields,fields,2.)
        self.assertEqual(result['wet_intersection_over_union'],1.)
        self.assertEqual(result['surface_error_abs_p95_m'],0.)
        self.assertEqual(result['extra_wet_cells_over_4m_from_source'],0)
        self.assertEqual(result['depth_change_max_m'],0.)

    def test_missing_surface_sections_remain_missing(self):
        source=np.ones((2,3),bool)
        h=np.ones((2,3));h[:,1]=0
        ref=dict(classified_water=source,reference_surface=np.full(3,100.),station=np.arange(3)*2.)
        fields=dict(h=h,eta=np.full(h.shape,100.),u=np.zeros(h.shape),v=np.zeros(h.shape))
        result=compare(ref,fields,fields,2.)
        self.assertEqual(result['surface_sections_missing'],1)
        self.assertIsNone(result['surface_error_per_station_m'][1])


if __name__=='__main__':unittest.main()
