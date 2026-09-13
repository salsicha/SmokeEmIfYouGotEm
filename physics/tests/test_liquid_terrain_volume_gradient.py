import sys
from pathlib import Path
import unittest
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from liquid_terrain_volume_gradient import evaluate_bed_columns


class TerrainVolumeGradientTest(unittest.TestCase):
    def fixture(self):
        # One XY column [.5,1.5]^2, phi=z-y. Fixed bed=.87.
        h=np.ones(3);z=np.arange(4)+.5
        c=np.stack((z-.5,z-.5,z-1.5,z-1.5),axis=-1)[None,...]
        def bed_segments(start,end):
            n=len(start)
            return np.arange(n),np.zeros(n),np.ones(n),np.full(n,.87),np.full(n,.87)
        return c,np.array([[0,0]]),np.array([[1.,1.]]),np.array([[.5,.5]]),h,bed_segments

    def test_clipped_surface_volume_and_gradient_low_order(self):
        args=self.fixture();v,g,r=evaluate_bed_columns(*args,2)
        self.assertAlmostEqual(v[0,0],.5*(1.5-.87)**2,places=13)
        self.assertAlmostEqual(g.sum(),-(1.5-.87),places=13)
        self.assertEqual(r['zero_crossing_on_bed_rays'],0)

    def test_all_nodal_derivatives_against_perturbed_volume(self):
        args=self.fixture();v,g,_=evaluate_bed_columns(*args,12)
        direction=np.random.default_rng(23).normal(size=args[0].shape);eps=1e-5
        a=evaluate_bed_columns(args[0]+eps*direction,*args[1:],12)[0]
        b=evaluate_bed_columns(args[0]-eps*direction,*args[1:],12)[0]
        self.assertAlmostEqual(float(np.sum(g*direction)),float((a[0,0]-b[0,0])/(2*eps)),places=7)

    def test_missing_or_overlapping_bed_partition_rejected(self):
        args=list(self.fixture())
        for start,end in ((.1,1.),(0.,.8)):
            def invalid(a,b):
                n=len(a)
                return np.arange(n),np.full(n,start),np.full(n,end),np.zeros(n),np.zeros(n)
            args[-1]=invalid
            with self.assertRaisesRegex(ValueError,'partition'):evaluate_bed_columns(*args,2)


if __name__=='__main__':unittest.main()
