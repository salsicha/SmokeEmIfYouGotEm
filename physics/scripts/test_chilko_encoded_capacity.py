import unittest
from types import SimpleNamespace
import numpy as np
import shapely
from shapely.geometry import LineString,box
from chilko_encoded_capacity import triangle_stencil,EncodedSections,inference_threshold
from chilko_triangle_ownership import preserve_triangle_support
from export_colorado_catalog_runtime import landscape_sample
from export_colorado_continuous_terrain import HEIGHT_BASE,HEIGHT_RANGE
from chilko_corridor_bed import carve_mapped_water


def model():
    m=SimpleNamespace(polygon=box(0,-5,1000,5),line=LineString([(0,0),(1000,0)]),
        station=np.array([0.,1000.]),width=np.array([10.,10.]),depth=np.array([2.,2.]))
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
