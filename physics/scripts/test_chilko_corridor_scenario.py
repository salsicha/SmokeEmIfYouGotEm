import unittest
import tempfile
import json
import io
from contextlib import redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np
from shapely.geometry import LineString, box
from shapely.ops import unary_union

from build_chilko_corridor_scenario import build, full_route_frame, initialize, validate_chart_footprint, validate_branch_coverage
from chilko_corridor_chart import directions_at_source_points


class CorridorScenarioTests(unittest.TestCase):
    def test_written_inputs_keep_nondefault_flow_and_native_friction(self):
        # Small straight-channel fixture exercises real chart coverage,
        # initialization and serialization, with synthetic terrain explicitly
        # confined to the unit test. No native river validation is claimed.
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);profile=root/'profile';profile.mkdir()
            canonical=root/'canonical';canonical.mkdir()
            station=np.arange(0.,1001.,4.)
            np.savez(profile/'profile.npz',station_m=station,xy_m=np.c_[station,np.zeros(len(station))],
                normal_xy=np.tile([0.,1.],(len(station),1)),right_bank_m=np.full(len(station),-20.),
                left_bank_m=np.full(len(station),20.))
            receipt=dict(profile_manifest_sha256='p',profile_sha256='z',terrain_manifest_sha256='t',
                route_sha256='r',planform_sha256='w',ownership_policy='fixture',discharge_m3s=33.5,manning_n=.06)
            manifest=dict(evidence_source=receipt,river_id='chilko_river_bc',horizontal_crs='EPSG:3157',
                vertical_reference='CGVD2013 (EPSG:6647)',world_y_sign=-1,horizontal_origin_m=[0.,0.],vertical_datum_m=100.)
            (canonical/'manifest.json').write_text(json.dumps(manifest))
            def sample(xy):
                wet=abs(xy[...,1])<20.
                ground=np.where(wet,99.,101.)
                return dict(source_height_m=ground,mapped_water=wet,ownership_reference_m=np.full(wet.shape,100.),
                    reference_m=np.full(wet.shape,100.),source_kind=np.ones(wet.shape,np.uint8))
            model=SimpleNamespace(receipt=receipt,line=LineString([(0,0),(1000,0)]),
                polygon=box(0,-20,1000,20),station=station,surface=np.full(len(station),100.),sample=sample)
            triangles=SimpleNamespace(manifest=manifest,folder=canonical,sample=lambda xy:sample(xy)['source_height_m'])
            with patch('build_chilko_corridor_scenario.LandscapeTriangles',return_value=triangles), \
                    patch('build_chilko_corridor_scenario.CorridorBed',return_value=model), redirect_stdout(io.StringIO()):
                report=build('terrain',profile,canonical,root/'inputs')
            sc=json.loads((root/'inputs/scenario/scenario.json').read_text())
            self.assertEqual(sc['metadata']['flow_band'],'inferred_33.5m3s')
            self.assertEqual(sc['metadata']['provenance']['flow_source'],
                '33.5 m3/s construction assumption, not a measured concurrent discharge')
            self.assertAlmostEqual(sc['roughness'],9.81*.06**2)
            self.assertEqual(sc['boundaries'][0]['metadata']['target_discharge_m3s'],33.5)
            self.assertLess(report['initial_discharge_max_error_m3s'],1e-10)
            with np.load(root/'inputs/scenario/initial_state.npz') as state:
                np.testing.assert_allclose(state['hu'].sum(axis=0)*2.,33.5,atol=1e-10)

    def test_canonical_flow_and_roughness_are_used_without_default_substitution(self):
        # Stop before geometry sampling: source validation must use the exact
        # construction assumptions that generated the canonical terrain.
        for discharge,roughness,depth in [(45.,.045,None),(33.5,.06,{'manifest':'depth/manifest.json'})]:
            manifest={'evidence_source':dict(discharge_m3s=discharge,manning_n=roughness,
                                             available_channel_depth=depth)}
            with tempfile.TemporaryDirectory() as tmp, \
                    patch('build_chilko_corridor_scenario.LandscapeTriangles',
                          return_value=SimpleNamespace(manifest=manifest)), \
                    patch('build_chilko_corridor_scenario.CorridorBed',side_effect=RuntimeError('stop before sampling')) as model:
                out=Path(tmp)/'fresh'
                with self.assertRaisesRegex(RuntimeError,'stop before sampling'):
                    build('terrain','profile','canonical',out)
                model.assert_called_once_with('terrain','profile',discharge,roughness,
                    depth_profile=Path('depth') if depth else None)
                self.assertFalse(out.exists())

    def test_parent_numerical_chart_keeps_cells_but_reprojects_geographic_station(self):
        parent=LineString([(0,0),(200,0),(250,50),(300,0),(500,0)])
        corrected=LineString([(0,0),(500,0)])
        old=full_route_frame(parent,smoothing_m=320,end_extension_m=64)
        result=full_route_frame(corrected,smoothing_m=320,end_extension_m=64,chart_line=parent)
        for key in ('xy','normal','station','curvature'):
            np.testing.assert_array_equal(result[key],old[key])
        np.testing.assert_allclose(result['source_station'],np.clip(result['xy'][:,0],0,500))
        self.assertTrue((np.diff(result['source_station'])>=0).all())
        self.assertFalse(np.array_equal(old['source_station'],result['source_station']))

    def test_sampling_directions_preserve_geographic_anchors_and_orientation(self):
        line=LineString([(0,0),(500,0)])
        points=np.array([[0.,0.],[100.,0.],[500.,0.]])
        before=points.copy();normal=directions_at_source_points(line,points)
        np.testing.assert_array_equal(points,before)
        np.testing.assert_allclose(normal,np.tile([0.,1.],(3,1)),atol=1e-12)
        with self.assertRaisesRegex(ValueError,'exact geographic route'):
            directions_at_source_points(line,[[100,10]])
        with self.assertRaises(ValueError):directions_at_source_points(line,[[np.nan,0]])

    def test_sampling_directions_are_smooth_at_short_transverse_source_edge(self):
        line=LineString([(0,0),(240,0),(240,20),(260,20),(500,0)])
        points=np.array([[240.,0.],[240.,10.],[240.,20.]])
        normals=directions_at_source_points(line,points)
        self.assertTrue((normals[:,1]>.99).all())
        np.testing.assert_allclose(np.linalg.norm(normals,axis=1),1.,atol=1e-12)

    def test_endpoint_extension_preserves_two_metre_grid_and_unique_physical_cells(self):
        line=LineString([(0,0),(500,0)])
        frame=full_route_frame(line,smoothing_m=320,end_extension_m=64)
        np.testing.assert_allclose(np.diff(frame['station']),2.,atol=1e-9)
        self.assertTrue((np.diff(frame['source_station'])>=0).all())
        self.assertTrue((np.diff(frame['source_station'])==0).any())
        self.assertTrue((np.linalg.norm(np.diff(frame['xy'],axis=0),axis=1)>1.99).all())
        self.assertTrue(validate_branch_coverage(frame,256,box(0,-40,500,40),line)['all_mapped_branches_covered'])
        for invalid in (-2,3,130):
            with self.assertRaises(ValueError):full_route_frame(line,end_extension_m=invalid)

    def test_main_route_coverage_does_not_hide_a_clipped_mapped_branch(self):
        line=LineString([(0,0),(500,0)]);frame=full_route_frame(line)
        main=box(0,-20,500,20)
        self.assertTrue(validate_branch_coverage(frame,100,main,line)['all_mapped_branches_covered'])
        branch=box(200,90,300,130)
        with self.assertRaisesRegex(ValueError,'clips mapped river branches'):
            validate_branch_coverage(frame,100,unary_union([main,branch]),line)
        self.assertTrue(validate_branch_coverage(frame,140,unary_union([main,branch]),line)['all_mapped_branches_covered'])

    def test_geographic_stages_are_not_flattened_across_curved_chart_row(self):
        bed=np.array([[103.,100.,100.5,103.],[102.,99.,99.5,102.]])
        stage=np.array([[np.nan,101.,101.5,np.nan],[np.nan,100.,100.5,np.nan]])
        channel=np.array([[False,True,True,False]]*2)
        h,u=initialize(bed,stage,channel,np.ones_like(bed),4.)
        np.testing.assert_array_equal(h,[[0.,1.,1.,0.]]*2)
        np.testing.assert_allclose((h*u).sum(axis=1)*2.,4.)
        stage[0,1]=np.nan
        with self.assertRaisesRegex(ValueError,'geographic stage'):
            initialize(bed,stage,channel,np.ones_like(bed),4.)

    def test_complete_strip_covers_source_banks_without_folding(self):
        line=LineString([(0,0),(500,0)])
        f=full_route_frame(line)
        s=np.arange(0,501,4.)
        p=dict(station_m=s,xy_m=np.c_[s,np.zeros(len(s))],
               normal_xy=np.tile([0.,1.],(len(s),1)),right_bank_m=np.full(len(s),-20.),
               left_bank_m=np.full(len(s),20.))
        result=validate_chart_footprint(f,100.,p,500.)
        self.assertTrue(result['full_strip_valid'])
        with self.assertRaisesRegex(ValueError,'clips'):validate_chart_footprint(f,10.,p,500.)
        f['curvature'][20]=.02
        with self.assertRaisesRegex(ValueError,'folds'):validate_chart_footprint(f,100.,p,500.)

    def test_full_frame_has_one_geographic_origin_and_monotonic_source_progression(self):
        line = LineString([(0, 0), (100, 0), (200, 30), (350, 40)])
        f = full_route_frame(line)
        np.testing.assert_allclose(np.diff(f['station']), 2., atol=1e-12)
        self.assertTrue((np.diff(f['source_station']) > 0).all())
        np.testing.assert_allclose(np.linalg.norm(f['normal'], axis=1), 1., atol=1e-12)
        self.assertLess(f['source_station'][0], 2.)
        self.assertLess(line.length-f['source_station'][-1], 4.)
        # A source window slices the common chart, never independently smooths it.
        a = (f['source_station'] >= 70) & (f['source_station'] <= 210)
        b = (f['source_station'] >= 170) & (f['source_station'] <= 280)
        for index in np.flatnonzero(a & b):
            np.testing.assert_array_equal(f['xy'][a][np.flatnonzero(a).tolist().index(index)],
                                          f['xy'][b][np.flatnonzero(b).tolist().index(index)])

    def test_exact_bed_is_not_altered_to_meet_initial_discharge(self):
        bed = np.array([[101., 99., 98., 99., 101.], [101., 98., 97., 98., 101.]])
        stage = np.array([100., 99.]); channel = np.tile([False, True, True, True, False], (2, 1))
        original = bed.copy()
        h, u = initialize(bed, stage, channel, np.ones_like(bed), 45.)
        np.testing.assert_array_equal(bed, original)
        np.testing.assert_array_equal(h, [[0., 1., 2., 1., 0.]]*2)
        np.testing.assert_allclose((h*u).sum(axis=1)*2., 45., atol=1e-12)

    def test_folded_dry_classified_channel_is_also_rejected(self):
        bed = np.array([[101., 99., 101., 101.]])
        channel = np.array([[False, True, True, False]])
        metric = np.array([[1., 1., .05, 1.]])
        with self.assertRaisesRegex(ValueError, 'folds'): initialize(bed, [100.], channel, metric, 45.)

    def test_dry_cross_section_and_clipped_channel_rejected(self):
        for bed, channel, error in [([[101., 101., 101.]], [[False, True, False]], 'Dry hydraulic'),
                                   ([[99., 99., 99.]], [[True, True, False]], 'clipped')]:
            with self.assertRaisesRegex(ValueError, error):
                initialize(bed, [100.], channel, np.ones((1, 3)), 45.)

    def test_self_intersecting_source_and_invalid_spacing_rejected(self):
        with self.assertRaises(ValueError):
            full_route_frame(LineString([(0, 0), (100, 100), (0, 100), (100, 0)]))
        with self.assertRaises(ValueError): full_route_frame(LineString([(0, 0), (300, 0)]), step=0.)


if __name__ == '__main__': unittest.main()
