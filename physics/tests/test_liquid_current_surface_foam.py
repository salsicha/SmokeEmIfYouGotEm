from pathlib import Path
import sys
import unittest
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from liquid_current_surface_foam import evolve,surface_coverage_statistics,surface_kinematics


class CurrentSurfaceFoamTest(unittest.TestCase):
    def test_rectangular_physical_edges_are_independent(self):
        c,h,v,b=self.fixture();h[...,1]=0
        z,y,x=np.indices(c.shape[:3]);c[...,0]=(z-5)*10
        z,y,x=np.indices(v.shape[:3]);v[...,0]=-2*((x+.5)*20-60);v[...,1]=400;v[...,2]=2*((z+.5)*20-60)
        expected=float(np.float16(.225/.475*(1-np.exp(-.0475))))
        for half,narrow,wide in (([1000,20],(5,8,5),(5,5,8)),([20,1000],(5,5,8),(5,8,5))):
            result,_=evolve(c,h,v,b,[10,.1,0,1],[120]*3,half_width=half,surface_source=True)
            self.assertAlmostEqual(result[5,5,5,1],expected)
            self.assertEqual(result[(*narrow,1)],0)
            self.assertAlmostEqual(result[(*wide,1)],expected)

    def test_surface_compression_is_rotation_invariant(self):
        j=np.diag([-2.,0.,2.])[None]
        n=np.array([[0.,0.,1.]])
        compression,curl=surface_kinematics([j[...,i] for i in range(3)],n)
        np.testing.assert_allclose(compression,2)
        np.testing.assert_allclose(curl,0)
        angle=.73
        r=np.array([[np.cos(angle),0,np.sin(angle)],[0,1,0],[-np.sin(angle),0,np.cos(angle)]])
        rotated=r@j@r.T
        c,w=surface_kinematics([rotated[...,i] for i in range(3)],n@r.T)
        np.testing.assert_allclose(c,compression,atol=1e-12)
        np.testing.assert_allclose(w,curl,atol=1e-12)

    def test_rotation_alone_is_not_foam_source(self):
        j=np.array([[[0.,-3.,0.],[3.,0.,0.],[0.,0.,0.]]])
        c,w=surface_kinematics([j[...,i] for i in range(3)],np.array([[0.,0.,1.]]))
        np.testing.assert_array_equal(c,0)
        np.testing.assert_array_equal(w,0)

    def test_simple_shear_retained_and_degenerate_surface_excluded(self):
        j=np.array([[[0.,0.,0.],[2.,0.,0.],[0.,0.,0.]]])
        c,w=surface_kinematics([j[...,i] for i in range(3)],np.array([[0.,0.,1.]]))
        np.testing.assert_array_equal(c,0)
        np.testing.assert_allclose(w,2)
        c,w=surface_kinematics([j[...,i] for i in range(3)],np.zeros((1,3)))
        np.testing.assert_array_equal(c,0)
        np.testing.assert_array_equal(w,0)

    def test_uniform_flow_has_no_source_on_curved_surface(self):
        c,h,v,b=self.fixture();z,y,x=np.indices(c.shape[:3])
        c[...,0]=(z-5.5)*10+3*np.sin(x*.6);h=c.copy();v[...,0]=200
        out,a=evolve(c,h,v,b,[10,.1,0,1],[120]*3,surface_source=True)
        np.testing.assert_array_equal(a[...,0],0)
        np.testing.assert_array_equal(out[...,1],0)

    def test_surface_statistics_interpolate_zero_not_volume_max(self):
        field=np.zeros((4,2,3,4));field[...,0]=np.array([-2,-1,1,2])[:,None,None]
        field[...,1]=np.array([1,.2,.4,1])[:,None,None]
        stats=surface_coverage_statistics(field)
        self.assertEqual(stats['columns'],6)
        np.testing.assert_allclose(stats['coverage_quantiles'],[.3]*7)
    def fixture(self):
        current=np.zeros((12,12,12,4));current[...,2]=10;current[...,3]=.25
        history=current.copy();history[...,1]=.5
        flow=np.zeros((6,6,6,4));boundary=flow.copy()
        return current,history,flow,boundary

    def test_pause_and_reset_preserve_surface_metadata(self):
        c,h,v,b=self.fixture()
        for clock,expected in (([10,0,0,0],.5),([0,0,1,1],0)):
            out,_=evolve(c,h,v,b,clock,[120]*3)
            np.testing.assert_array_equal(out[...,[0,2,3]],c[...,[0,2,3]])
            self.assertTrue((out[...,1]==expected).all())

    def test_uniform_flow_advects_at_water_speed_without_source(self):
        c,h,v,b=self.fixture();h[...,1]=0;h[:,:,4,1]=1;v[...,0]=50
        out,_=evolve(c,h,v,b,[10,.1,0,1],[120]*3,source_scale=0,decay=0)
        np.testing.assert_allclose(out[5,5,:,1],np.eye(12)[4]*.5+np.eye(12)[5]*.5)

    def test_decay_and_solid_exclusion(self):
        c,h,v,b=self.fixture();b[:,:,0,3]=1
        out,_=evolve(c,h,v,b,[10,.1,0,1],[120]*3,source_scale=0)
        self.assertTrue((out[:,:,:2,1]==0).all())
        self.assertAlmostEqual(out[5,5,5,1],float(np.float16(.5*np.exp(-.025))))

    def test_half_stored_support_boundary_is_excluded(self):
        c,h,v,b=self.fixture();c[...,0]=50
        out,_=evolve(c,h,v,b,[10,.1,0,1],[200]*3)
        self.assertTrue((out[...,1]==0).all())

    def test_rising_surface_keeps_foam_on_surface_not_empty_volume(self):
        c,h,v,b=self.fixture();z=np.arange(12)[:,None,None]*10+5
        c[...,0]=z-65;h[...,0]=z-60;h[...,1]=0;h[5:7,...,1]=1;v[...,2]=50
        out,_=evolve(c,h,v,b,[10,.1,0,1],[120]*3,source_scale=0,decay=0,project_history=True)
        np.testing.assert_array_equal(out[...,1],(abs(c[...,0])<30).astype(float))
        previous,_=evolve(c,h,v,b,[10,.1,0,1],[120]*3,source_scale=0,decay=0,project_history=False)
        self.assertGreater(out[...,1].sum(),previous[...,1].sum())

    def test_current_surface_gates_source_not_inherited_coverage(self):
        c,h,v,b=self.fixture();h[...,1]=0;c[...,1]=1
        v[...,1]=np.arange(6)[None,None,:]*40+200
        out,a=evolve(c,h,v,b,[10,.1,0,1],[120]*3)
        self.assertGreater(a[5,5,5,0],0)
        c[...,0]=1000
        dry,_=evolve(c,h,v,b,[10,.1,0,1],[120]*3)
        self.assertTrue((dry[...,1]==0).all())


if __name__=='__main__':unittest.main()
