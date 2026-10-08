import unittest
import numpy as np
from warm_start_colorado_bank_cook import bank_state


class BankWarmStartTests(unittest.TestCase):
    def setUp(self):
        self.bed=np.full((2,3),900.)
        h=np.array([[0.,.2,2.],[1e-7,1.,.5]])
        u=np.array([[0.,2.,3.],[.1,-1.,2.]])
        v=u*.2
        self.frame=dict(h=h,eta=self.bed+h,u=u,v=v,hu=h*u,hv=h*v,wet=(h>1e-6).astype(float))
        self.grid=dict(nx=3,ny=2,dx=2.,dy=2.)

    def test_only_changed_cells_are_rederived_and_no_water_is_added(self):
        bed=self.bed.copy();bed[0,1]+=.5;bed[0,2]+=.5
        result,stats=bank_state(self.frame,self.bed,bed,self.grid)
        self.assertEqual(result['depth'][0,1],0.)
        self.assertEqual(result['u'][0,1],0.)
        self.assertEqual(result['depth'][0,2],1.5)
        self.assertEqual(result['u'][0,2],3.)
        self.assertEqual(result['hu'][0,2],4.5)
        unchanged=bed==self.bed
        for k,a in result.items():
            np.testing.assert_array_equal(a[unchanged],self.frame['h' if k=='depth' else k][unchanged])
        self.assertTrue((result['depth']<=self.frame['h']).all())
        self.assertAlmostEqual(stats['removed_water_volume_m3'],2.8)
        self.assertEqual(stats['newly_dry_cells'],1)
        np.testing.assert_allclose(result['eta']-result['depth'],bed,atol=1e-10,rtol=0)

    def test_dry_source_cannot_create_water(self):
        bed=self.bed+.1
        result,_=bank_state(self.frame,self.bed,bed,self.grid)
        self.assertEqual(result['depth'][0,0],0.)
        self.assertFalse(result['wet'][1,0])

    def test_lowered_nonfinite_or_unbounded_bed_refused(self):
        for change in (-.01,1.02,float('nan')):
            bed=self.bed.copy();bed[0,0]+=change
            with self.subTest(change=change),self.assertRaises(ValueError):bank_state(self.frame,self.bed,bed,self.grid)

    def test_unchanged_candidate_uses_exact_continuation(self):
        with self.assertRaisesRegex(ValueError,'exact continuation'):
            bank_state(self.frame,self.bed,self.bed,self.grid)

    def test_wrong_previous_bed_or_shape_refused(self):
        with self.assertRaisesRegex(ValueError,'bed changed'):
            bank_state(self.frame,self.bed+.1,self.bed+.5,self.grid)
        with self.assertRaisesRegex(ValueError,'Aligned'):
            bank_state(self.frame,self.bed,self.bed[:1],self.grid)


if __name__=='__main__':unittest.main()
