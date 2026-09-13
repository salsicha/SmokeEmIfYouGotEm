import sys
from pathlib import Path
import unittest
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from liquid_correction_map import inverse_map,transport_interface,reclassify_interface
from liquid_compatible_advection import sample_compact


class CorrectionMapTest(unittest.TestCase):
    def test_affine_map_inverse_is_not_negative_euler_or_rk2(self):
        z,y,x=np.indices((15,16,17));grid=np.stack((x+.5,y+.5,z+.5),axis=-1)
        a=np.array([[.1,.04,0],[0,-.05,.03],[.01,0,.08]])
        delta=grid@a.T+[.04,-.07,.02]
        p=np.array([[6.3,7.2,8.1],[8.2,5.7,4.9]])
        dest=p+sample_compact(p,delta.transpose(2,1,0,3),np.ones(3))
        back,valid,r=inverse_map(dest,delta,np.ones(3),tolerance=1e-11)
        self.assertTrue(valid.all());np.testing.assert_allclose(back,p,atol=1e-11)
        self.assertFalse(r['global_injectivity_proven'])
        naive=dest-sample_compact(dest,delta.transpose(2,1,0,3),np.ones(3))
        self.assertGreater(abs(naive-p).max(),.01)

    def test_scalar_translation_and_fixed_cells(self):
        z,y,x=np.indices((12,12,12));phi=z+.5-5.2;delta=np.zeros((*phi.shape,3));delta[...,2]=.4
        selected=np.zeros(phi.shape,bool);selected[3:-3,3:-3,3:-3]=True
        result,r=transport_interface(phi,delta,np.ones(3),selected)
        self.assertTrue(r['candidate_valid'])
        np.testing.assert_allclose(result[selected],phi[selected]-.4,atol=1e-12)
        np.testing.assert_array_equal(result[~selected],phi[~selected])

    def test_folded_and_unsupported_maps_are_explicitly_rejected(self):
        z,y,x=np.indices((12,12,12));delta=np.zeros((12,12,12,3));delta[...,0]=-2*(x+.5-6)
        _,valid,r=inverse_map(np.array([[6.1,6.2,6.3],[.1,.2,.3]]),delta,np.ones(3))
        self.assertFalse(valid.any());self.assertEqual(r['nonpositive_sampled_jacobians'],1)
        selected=np.zeros((12,12,12),bool);selected[6,6,6]=True
        result,r=transport_interface(z.astype(float),delta,np.ones(3),selected)
        self.assertFalse(r['candidate_valid']);self.assertTrue(np.isnan(result[selected]).all())

    def test_phase_change_requires_new_pressure_system_and_preserves_solids(self):
        b=np.zeros((2,2,2,4));b[0,...,3]=2;b[:,0,0,3]=1;b[:,1,1,3]=3
        phi=np.ones((2,2,2));phi[0]=-1
        out,r=reclassify_interface(b,phi)
        self.assertFalse(r['pressure_factorization_reusable'])
        self.assertEqual(r['air_to_fluid_cells'],2);self.assertEqual(r['fluid_to_air_cells'],2)
        np.testing.assert_array_equal(out[:,0,0],b[:,0,0]);np.testing.assert_array_equal(out[:,1,1],b[:,1,1])
        phi[0,0,0]=np.nan
        with self.assertRaises(ValueError):reclassify_interface(b,phi)

    def test_empty_selection_and_invalid_arguments(self):
        phi=np.zeros((8,8,8));delta=np.zeros((*phi.shape,3))
        out,r=transport_interface(phi,delta,np.ones(3),np.zeros(phi.shape,bool))
        self.assertTrue(r['candidate_valid']);np.testing.assert_array_equal(out,phi)
        with self.assertRaises(ValueError):inverse_map(np.zeros((1,3)),delta,[0,1,1])


if __name__=='__main__':unittest.main()
