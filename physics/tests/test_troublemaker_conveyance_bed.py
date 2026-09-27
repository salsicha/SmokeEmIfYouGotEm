"""Source-preservation tests, not hydraulic/visual qualification."""
import unittest
import numpy as np
from prepare_troublemaker_conveyance_bed import revise


class ConveyanceBedTest(unittest.TestCase):
    def setUp(self):
        x,y=np.meshgrid(np.linspace(-40,40,9),np.linspace(40,-40,9))
        self.mesh=dict(east_m=x,north_m=y,z_m=np.full(x.shape,8.,dtype=np.float32),
            source_surface_m=np.full(x.shape,10.,dtype=np.float32),
            authority=np.full(x.shape,2,dtype=np.uint8),triangles=np.array([[0,1,9]]))
        self.station=np.zeros(x.shape)
        self.clearance=np.full(x.shape,6.)
        self.design=dict(station_center_m=[-100,100],normal_depth_m=[.5,.5],
            pool_weight=[0.,0.],bank_shape_length_m=[3.,3.],
            centerline_depth_m=[.25,.25])  # Must not import fitted depth.

    def test_unbiased_depth_and_original_unchanged(self):
        out,_,_=revise(self.mesh,self.station,self.clearance,self.design)
        self.assertEqual(out['z_m'][4,4],9.5)
        self.assertTrue(np.all(self.mesh['z_m']==8.))
        for k in self.mesh:
            if k!='z_m': np.testing.assert_array_equal(out[k],self.mesh[k])

    def test_all_non_bed_authorities_unchanged(self):
        for a in (1,3,4,5):
            self.mesh['authority'][4,4]=a
            out,_,_=revise(self.mesh,self.station,self.clearance,self.design)
            self.assertEqual(out['z_m'][4,4],8.)

    def test_boundary_exact_and_smooth_taper(self):
        out,w,_=revise(self.mesh,self.station,self.clearance,self.design)
        edge=np.zeros(w.shape,bool);edge[[0,-1],:]=True;edge[:,[0,-1]]=True
        np.testing.assert_array_equal(out['z_m'][edge],self.mesh['z_m'][edge])
        self.assertEqual(w[4,4],1.)
        self.assertAlmostEqual(w[1,4],7/27)
        self.assertTrue(np.all((out['z_m']>=8)&(out['z_m']<=9.5)))

    def test_pool_and_bank_shape(self):
        self.design['pool_weight']=[1.,1.]
        self.clearance[:]=1.5
        out,_,depth=revise(self.mesh,self.station,self.clearance,self.design)
        self.assertAlmostEqual(depth[4,4],1.1)
        self.assertAlmostEqual(float(out['z_m'][4,4]),8.9,places=5)

    def test_fail_closed_inputs(self):
        for value in (float('nan'),-1.):
            bad=self.clearance.copy();bad[4,4]=value
            with self.assertRaises(ValueError): revise(self.mesh,self.station,bad,self.design)
        for field,value in [('normal_depth_m',[-1.,1.]),('pool_weight',[0.,2.]),
                            ('station_center_m',[1.,0.]),('bank_shape_length_m',[0.,1.])]:
            with self.assertRaises(ValueError):
                revise(self.mesh,self.station,self.clearance,dict(self.design,**{field:value}))
        self.mesh['authority'][4,4]=0
        with self.assertRaises(ValueError): revise(self.mesh,self.station,self.clearance,self.design)

    def test_no_extrapolation_or_above_surface_bed(self):
        self.station[4,4]=101
        with self.assertRaises(ValueError): revise(self.mesh,self.station,self.clearance,self.design)
        self.station[4,4]=0; self.mesh['z_m'][4,4]=11
        with self.assertRaises(ValueError): revise(self.mesh,self.station,self.clearance,self.design)


if __name__=='__main__': unittest.main()
