import unittest
import tempfile,json
from pathlib import Path
from unittest.mock import patch
from types import SimpleNamespace
import numpy as np
import shapely
from shapely.geometry import LineString,box
from chilko_encoded_capacity import triangle_stencil,EncodedSections,inference_threshold,capacity_grid,validate_capacity_grid,geographic_query_slopes
from chilko_triangle_ownership import preserve_triangle_support
from export_colorado_catalog_runtime import landscape_sample
from export_colorado_continuous_terrain import HEIGHT_BASE,HEIGHT_RANGE
from chilko_corridor_bed import carve_mapped_water


def model():
    m=SimpleNamespace(polygon=box(0,-5,1000,5),line=LineString([(0,0),(1000,0)]),
        station=np.array([0.,1000.]),width=np.array([10.,10.]),depth=np.array([2.,2.]),slope=np.array([.01,.01]))
    def sample(xy):
        xy=np.asarray(xy);mapped=shapely.contains_xy(m.polygon,xy[...,0],xy[...,1])
        ground=np.full(mapped.shape,1000.);stage=np.where(mapped,1000.,np.nan)
        d=shapely.distance(shapely.points(xy.reshape(-1,2)),m.polygon.boundary).reshape(mapped.shape)
        amplitude=np.interp(xy[...,0],m.station,m.depth)
        bed,inferred=carve_mapped_water(ground,np.ones(mapped.shape),mapped,stage,d,np.full(mapped.shape,10.),amplitude,stage)
        return dict(source_height_m=ground,height_m=bed,inferred_bed=inferred,mapped_water=mapped,
                    reference_m=stage,ownership_reference_m=stage)
    m.sample=sample;return m


class EncodedCapacityTests(unittest.TestCase):
    def test_normal_builder_uses_encoded_fit_and_records_grid(self):
        from build_chilko_corridor_depth import build
        m=model();m.surface=np.array([1000.,1000.]);m.terrain=SimpleNamespace(folder=Path('terrain'))
        m.receipt={key:'fixture' for key in ('profile_manifest_sha256','profile_sha256','terrain_manifest_sha256',
            'route_sha256','planform_sha256','ownership_policy')}
        frame=dict(station=np.array([100.,102.]),source_station=np.array([100.,102.]),
            xy=np.array([[100.,0.],[102.,0.]]),normal=np.array([[0.,1.],[0.,1.]]))
        with tempfile.TemporaryDirectory() as tmp, \
                patch('build_chilko_corridor_depth.CorridorBed',return_value=m), \
                patch('build_chilko_corridor_depth.hydraulic_frame',return_value=(frame,{})), \
                patch('build_chilko_corridor_depth.validate_branch_coverage',return_value={}), \
                patch('build_chilko_corridor_depth.sha',return_value='fixture'),patch('builtins.print'):
            out=Path(tmp)/'depth'
            receipt=build('terrain','profile',out,origin=[0.,0.])
            self.assertEqual(receipt['capacity_grid'],capacity_grid([0.,0.]))
            self.assertFalse(receipt['hydraulic_solution'])
            self.assertIn('wet query',receipt['capacity_slope_policy'])
            with np.load(out/'depth.npz') as z:
                self.assertTrue((z['inferred_capacity_m3s']>=45.).all())
                self.assertTrue((z['depth_amplitude_m']>=m.depth).all())
            self.assertEqual(json.loads((out/'manifest.json').read_text()),receipt)

    def test_export_refuses_incompatible_grid_before_creating_output(self):
        from export_chilko_corridor_terrain import export
        m=model();m.receipt=dict(available_channel_depth=dict(capacity_grid=capacity_grid([0.,0.])))
        with tempfile.TemporaryDirectory() as tmp,patch('export_chilko_corridor_terrain.CorridorBed',return_value=m):
            out=Path(tmp)/'terrain'
            with self.assertRaisesRegex(ValueError,'identical canonical'):
                export('terrain','profile',out,[1.,0.],900.,depth_profile='depth')
            self.assertFalse(out.exists())

    def test_default_capacity_uses_each_wet_query_geographic_slope(self):
        m=model();m.slope=np.array([.001,.1])
        # An oblique numerical row crosses multiple geographic stations. The
        # dry query has no source projection and contributes no capacity.
        xy=np.array([[[100.,-2.],[104.,0.],[108.,2.],[200.,8.]]])
        sections=EncodedSections(m,xy,[0,0])
        expected_slope=np.array([[.0109,.011296,.011692,0.]])
        np.testing.assert_allclose(sections.slope,expected_slope)
        bed=np.sum(sections.vertex_heights([2.])*sections.weights,axis=-1)
        depth=np.where(sections.query_owned,np.maximum(sections.query_stage-bed,0),0)
        expected=np.sum(depth**(5/3)*np.sqrt(expected_slope),axis=1)/.045
        np.testing.assert_allclose(sections.capacity([2.],.045),expected)

    def test_dry_chart_centre_projection_does_not_change_production_capacity(self):
        from build_chilko_corridor_depth import build
        m=model();m.surface=np.array([1000.,1000.]);m.terrain=SimpleNamespace(folder=Path('terrain'))
        m.slope=np.array([.001,.1])
        m.receipt={key:'fixture' for key in ('profile_manifest_sha256','profile_sha256','terrain_manifest_sha256',
            'route_sha256','planform_sha256','ownership_policy')}
        capacities=[]
        with tempfile.TemporaryDirectory() as tmp:
            for i,projection in enumerate(([100.,102.],[800.,800.])):
                frame=dict(station=np.array([100.,102.]),source_station=np.array(projection),
                    xy=np.array([[100.,20.],[102.,20.]]),normal=np.array([[0.,1.],[0.,1.]]))
                with patch('build_chilko_corridor_depth.CorridorBed',return_value=m), \
                        patch('build_chilko_corridor_depth.hydraulic_frame',return_value=(frame,{})), \
                        patch('build_chilko_corridor_depth.validate_branch_coverage',return_value={}), \
                        patch('build_chilko_corridor_depth.sha',return_value='fixture'),patch('builtins.print'):
                    out=Path(tmp)/str(i);build('terrain','profile',out,origin=[0.,0.])
                    with np.load(out/'depth.npz') as z:
                        capacities.append((z['minimum_amplitude_capacity_m3s'].copy(),z['depth_amplitude_m'].copy()))
        for left,right in zip(*capacities):np.testing.assert_array_equal(left,right)

    def test_geographic_slopes_refuse_invalid_wet_support(self):
        m=model()
        for station in (-1.,1001.,np.nan):
            with self.assertRaises(ValueError):geographic_query_slopes(m,np.array([[station]]),np.array([[True]]))
        np.testing.assert_array_equal(geographic_query_slopes(m,np.array([[np.nan,100.]]),np.array([[False,True]])),[[0.,.01]])
        m.slope[0]=0
        with self.assertRaises(ValueError):geographic_query_slopes(m,np.array([[100.]]),np.array([[True]]))

    def test_builder_resumes_only_completed_batches_and_matches_fresh_fit(self):
        from build_chilko_corridor_depth import build
        m=model();m.surface=np.array([1000.,1000.]);m.terrain=SimpleNamespace(folder=Path('terrain'))
        m.receipt={key:'fixture' for key in ('profile_manifest_sha256','profile_sha256','terrain_manifest_sha256',
            'route_sha256','planform_sha256','ownership_policy')}
        stations=np.arange(100.,228.,2.)
        frame=dict(station=stations,source_station=stations.copy(),xy=np.c_[stations,np.zeros(64)],
            normal=np.tile([0.,1.],(64,1)))
        original_fit=EncodedSections.fit;calls=[]
        def fail_second_batch(sections,*args):
            calls.append(True)
            if len(calls)==2:raise ValueError('injected unresolved section')
            return original_fit(sections,*args)
        with tempfile.TemporaryDirectory() as tmp, \
                patch('build_chilko_corridor_depth.CorridorBed',return_value=m), \
                patch('build_chilko_corridor_depth.hydraulic_frame',return_value=(frame,{})), \
                patch('build_chilko_corridor_depth.validate_branch_coverage',return_value={}), \
                patch('build_chilko_corridor_depth.sha',return_value='fixture'),patch('builtins.print'):
            out=Path(tmp)/'resumed';checkpoint=Path(tmp)/'checkpoint'
            with patch.object(EncodedSections,'fit',fail_second_batch),self.assertRaisesRegex(ValueError,'unresolved section'):
                build('terrain','profile',out,origin=[0.,0.],checkpoint_dir=checkpoint)
            self.assertFalse(out.exists())
            with np.load(checkpoint/'latest.npz') as z:self.assertEqual(z['completed'].item(),32)
            with patch.object(EncodedSections,'fit',autospec=True,side_effect=original_fit) as fitted:
                build('terrain','profile',out,origin=[0.,0.],checkpoint_dir=checkpoint)
                self.assertEqual(fitted.call_count,1)
            fresh=Path(tmp)/'fresh';build('terrain','profile',fresh,origin=[0.,0.])
            with np.load(out/'depth.npz') as resumed,np.load(fresh/'depth.npz') as full:
                for key in full.files:np.testing.assert_array_equal(resumed[key],full[key])

    def test_capacity_is_bound_to_export_grid_and_guard(self):
        grid=capacity_grid([442000.,5749000.])
        validate_capacity_grid(grid,[442000.,5749000.])
        for wrong in (dict(grid,spacing_m=1.),dict(grid,support_policy='none'),dict(grid,height_range_m=1000.)):
            with self.assertRaises(ValueError):validate_capacity_grid(wrong,[442000.,5749000.])
        with self.assertRaises(ValueError):validate_capacity_grid(grid,[442001.,5749000.])
        for origin in (None,[0],[np.nan,0]):
            with self.assertRaises(ValueError):capacity_grid(origin)

    def test_native_triangle_stencil_both_diagonals(self):
        xy=np.array([[[.2,.4],[1.5,.4],[1.7,1.8],[2.,2.]]])
        # Include the halo beyond the exact grid vertex: its zero-weight
        # neighbours still belong to the stencil and need valid terrain.
        z=np.array([[1003.,1005.,1007.],[1000.,1001.,1006.],[1004.,1002.,1008.]])
        nodes,ids,w=triangle_stencil(xy,[0,0])
        height=landscape_sample(z,2-nodes[:,1]/2,nodes[:,0]/2)
        np.testing.assert_allclose(np.sum(height[ids]*w,axis=-1),landscape_sample(z,2-xy[...,1]/2,xy[...,0]/2))

    def test_encoded_response_matches_actual_guard(self):
        m=model();xy=np.stack(np.meshgrid([100.,102.],np.arange(-8.,9.)),axis=-1).transpose(1,0,2)
        sections=EncodedSections(m,xy,[0,0],np.full(2,.01))
        for amplitude in (.1,1.,3.):
            m.depth[:]=amplitude
            actual=preserve_triangle_support(m,sections.nodes,m.sample(sections.nodes))['height_m']
            encoded=HEIGHT_BASE+np.rint((actual-HEIGHT_BASE)*65535/HEIGHT_RANGE)*HEIGHT_RANGE/65535
            np.testing.assert_array_equal(sections.vertex_heights(np.full(2,amplitude)),encoded[sections.indices])

    def test_fit_and_geographic_probe_envelope(self):
        m=model();xy=np.stack(np.meshgrid([100.,102.],np.arange(-8.,9.)),axis=-1).transpose(1,0,2)
        sections=EncodedSections(m,xy,[0,0],np.full(2,.01));a,_,capacity=sections.fit(20.)
        self.assertTrue((capacity>=20).all())
        m.depth[:]=.05
        sections.apply_geographic_envelope(m,m.depth,a)
        actual=preserve_triangle_support(m,sections.nodes,m.sample(sections.nodes))['height_m']
        actual=HEIGHT_BASE+np.rint((actual-HEIGHT_BASE)*65535/HEIGHT_RANGE)*HEIGHT_RANGE/65535
        self.assertTrue((actual[sections.indices]<=sections.vertex_heights(a)+1e-10).all())

    def test_protected_narrow_channel_refuses_unbounded_depth(self):
        m=model();m.polygon=box(0,-.5,1000,.5);m.width[:]=1.
        xy=np.array([[[100.,0.],[100.,1.]]])
        sections=EncodedSections(m,xy,[0,0],np.array([.001]))
        with self.assertRaisesRegex(ValueError,'10 m'):sections.fit()

    def test_strict_threshold_and_source_eligibility(self):
        t=inference_threshold(np.array([10.,10.,10.,10.]),np.array([10.,11.,11.,11.]),
            np.array([0.,.5,0.,.5]),np.array([True,True,True,False]))
        np.testing.assert_array_equal(t,[-np.inf,2.,np.inf,np.inf])

    def test_rejects_bad_geometry_and_amplitude(self):
        with self.assertRaises(ValueError):triangle_stencil(np.array([[0,0]]),[0,0])
        m=model();sections=EncodedSections(m,np.array([[[100.,0.]]]),[0,0],np.array([.01]))
        for a in ([0.],[11.],[np.nan],[[2.]]):
            with self.assertRaises(ValueError):sections.capacity(a,.045)


if __name__=='__main__':unittest.main()
