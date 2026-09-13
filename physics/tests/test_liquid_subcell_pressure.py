import sys
import unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from liquid_compatible_projection import surface_gradient_weights,gradient,divergence,constrain_velocity,project
from diagnose_liquid_hydrostatic_balance import lake


class SubcellPressureTest(unittest.TestCase):
    def test_interface_fraction_uses_two_cell_sample_span(self):
        b=np.zeros((4,4,5,4));b[...,3]=2
        phi=np.broadcast_to(np.arange(5)-1.25,(4,4,5)).copy();b[phi<0,3]=0
        w=surface_gradient_weights(b,phi)
        self.assertAlmostEqual(w[2,2,1,0],2/1.25)
        self.assertAlmostEqual(w[2,2,2,0],2/.25)

    def test_weighted_operator_is_symmetric_positive(self):
        _,b,phi,_=lake();_,m,fluid=constrain_velocity(np.zeros((*phi.shape,3)),b)
        w=m*surface_gradient_weights(b,phi);rng=np.random.default_rng(7729)
        p=np.where(fluid,rng.normal(size=phi.shape),0);q=np.where(fluid,rng.normal(size=phi.shape),0)
        a=lambda f:-divergence(w*gradient(f,(50,50,800/24)),(50,50,800/24))
        self.assertAlmostEqual(float(np.sum(p*a(q))),float(np.sum(q*a(p))),places=12)
        self.assertGreater(float(np.sum(p*a(p))),0)

    def test_still_water_has_no_artificial_current_at_fractional_levels(self):
        for stage in (201.,225.,249.):
            v,b,phi,known=lake(stage)
            updated,p,r=project(v,b,spacing=(50,50,800/24),boundary_pressure=known,
                free_surface_phi=phi,tolerance=1e-11,max_iterations=1800)
            self.assertTrue(r['converged'])
            fluid=b[...,3]==0
            self.assertLess(float(abs(updated[fluid]).max()),1e-7)
            self.assertLess(float(abs(p-980*np.maximum(-phi,0))[fluid].max()),1e-4)

    def test_phase_disagreement_is_not_silently_reclassified(self):
        _,b,phi,_=lake();phi[:]=-1
        with self.assertRaises(ValueError):surface_gradient_weights(b,phi)

    def test_nonfinite_boundary_rejected_before_integer_conversion(self):
        import warnings
        _,b,phi,_=lake();b[0,0,0,3]=np.nan
        with warnings.catch_warnings():
            warnings.simplefilter('error')
            with self.assertRaises(ValueError):surface_gradient_weights(b,phi)

    def test_external_air_cannot_supply_nonzero_pressure(self):
        v,b,phi,known=lake();known[(b[...,3]==3)&(phi>=0)]=1
        with self.assertRaises(ValueError):project(v,b,boundary_pressure=known,free_surface_phi=phi)

    def test_default_operator_remains_unchanged_when_no_interface_is_supplied(self):
        v,b,phi,known=lake()
        a,p,r=project(v,b,spacing=(50,50,800/24),boundary_pressure=known)
        self.assertFalse(r['current_interface_supplied'])
        self.assertEqual(r['maximum_free_surface_gradient_weight'],1)
        self.assertGreater(float(abs(a[...,0]).max()),.1)


if __name__=='__main__':unittest.main()
