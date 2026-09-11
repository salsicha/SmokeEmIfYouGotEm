from pathlib import Path
import sys
import unittest
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from liquid_breaking_source import crest_activity


class CrestActivityTest(unittest.TestCase):
    def fixture(self):
        # Deliberately anisotropic metric; a 20 cm sphere at a known pole.
        self.extent=np.array([120.,160.,200.]);self.shape=np.array([80,80,80])
        z,y,x=np.indices(self.shape)
        point=(np.stack((x,y,z),axis=-1)+.5)/self.shape[::-1]*self.extent-self.extent/2
        self.surface=np.zeros((*self.shape,4));self.surface[...,0]=np.linalg.norm(point,axis=-1)-20
        self.flow=np.zeros((40,40,40,4))
        return np.array([[.5,.5,.6]])

    def test_convex_sphere_with_outward_flow(self):
        p=self.fixture();self.flow[...,2]=200
        curvature,alignment,rate=crest_activity(self.surface,self.flow,p,self.extent)
        self.assertAlmostEqual(curvature[0],.1,delta=.004)
        self.assertAlmostEqual(alignment[0],1,places=8)
        self.assertAlmostEqual(rate[0],20,delta=.8)

    def test_tangent_inward_stationary_and_concave_do_not_break(self):
        p=self.fixture()
        for flow in ([200,0,0],[0,0,-200],[0,0,0]):
            self.flow[...,:3]=flow
            self.assertEqual(crest_activity(self.surface,self.flow,p,self.extent)[2][0],0)
        self.surface[...,0]*=-1;self.flow[...,2]=-200
        self.assertEqual(crest_activity(self.surface,self.flow,p,self.extent)[2][0],0)

    def test_planar_surface_does_not_break(self):
        p=self.fixture();self.surface[...,0]=(np.arange(80)[:,None,None]+.5)*2.5-120
        self.flow[...,2]=200
        self.assertEqual(crest_activity(self.surface,self.flow,p,self.extent)[2][0],0)


if __name__=='__main__':unittest.main()
