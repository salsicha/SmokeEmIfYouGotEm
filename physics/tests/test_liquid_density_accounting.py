import sys
from pathlib import Path
import unittest
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from liquid_density_projection import density_accounting,density_target


class DensityAccountingTest(unittest.TestCase):
    def test_air_or_solid_clump_cannot_hide_in_fluid_report(self):
        rho=np.ones((3,3,3));solid=np.zeros_like(rho);types=np.zeros_like(rho,int)
        rho[1,1,1]=12;solid[1,1,1]=.4
        for phase in (0,1,2,3):
            types[1,1,1]=phase;b=np.zeros((*rho.shape,4));b[...,3]=types
            _,r=density_target(rho,solid,b)
            g=r['whole_domain']
            self.assertEqual(g['maximum_particle_density'],12)
            self.assertEqual(g['maximum_total_density'],12.4)
            self.assertEqual(g['maximum_total_density_cell_phase'],phase)
            self.assertEqual(g['maximum_total_density_cell_zyx'],[1,1,1])
            self.assertAlmostEqual(g['total_density_excess_sum'],11.4)
            self.assertAlmostEqual(g['total_density_excess_squared_sum'],11.4**2)

    def test_phase_totals_partition_all_kernel_weight_without_mutation(self):
        rng=np.random.default_rng(23);rho=rng.random((4,5,6))*2
        solid=rng.random(rho.shape);types=rng.integers(0,4,rho.shape);before=rho.copy()
        r=density_accounting(rho,solid,types)
        self.assertEqual(sum(p['cells'] for p in r['phases'].values()),rho.size)
        self.assertAlmostEqual(sum(p['particle_density_sum'] for p in r['phases'].values()),rho.sum())
        self.assertAlmostEqual(sum(p['total_density_excess_squared_sum'] for p in r['phases'].values()),r['total_density_excess_squared_sum'])
        np.testing.assert_array_equal(rho,before)

    def test_absent_phase_and_zero_water_have_finite_accounting(self):
        rho=np.zeros((2,2,2));r=density_accounting(rho,np.ones_like(rho),np.ones_like(rho))
        self.assertEqual(r['particle_density_sum'],0)
        self.assertEqual(r['total_density_excess_sum'],0)
        self.assertEqual(r['phases']['fluid']['cells'],0)
        self.assertEqual(r['phases']['fluid']['maximum_total_density'],0)

    def test_invalid_input_is_rejected(self):
        rho=np.ones((2,2,2))
        for types in (np.full_like(rho,.4),np.full_like(rho,4),np.full_like(rho,np.nan)):
            with self.assertRaises(ValueError):density_accounting(rho,np.zeros_like(rho),types)
        with self.assertRaises(ValueError):density_accounting(-rho,rho,np.zeros_like(rho))


if __name__=='__main__':unittest.main()
