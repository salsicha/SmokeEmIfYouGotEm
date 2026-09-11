import sys
from pathlib import Path
import unittest
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from analyze_liquid_pool_circulation import analyze


class PoolCirculationTests(unittest.TestCase):
    def fixture(self):
        return {'Velocity':np.zeros((24,68,68,3)),
                'SolidVelocity_Boundary':np.zeros((24,68,68,4))}

    def test_solid_cells_do_not_count_as_return_flow(self):
        f=self.fixture();f['Velocity'][...,0]=-100;f['SolidVelocity_Boundary'][...,3]=1
        r=analyze(f);self.assertEqual(r['pool']['fluid_cells'],0);self.assertIsNone(r['pool']['upstream_fraction'])

    def test_signed_cm_to_m_velocity(self):
        f=self.fixture();f['Velocity'][...]=[-100,20,30]
        r=analyze(f);self.assertEqual(r['pool']['upstream_fraction'],1)
        self.assertEqual(r['pool']['rising_fraction'],1)
        self.assertEqual(r['pool']['velocity_xyz_quantiles_m_s'][2],[-1,.2,.3])
        self.assertAlmostEqual(r['layers'][0]['datum_z_m'],3.5+1/6)

    def test_small_noise_is_not_return_flow(self):
        f=self.fixture();f['Velocity'][...,0]=-1
        self.assertEqual(analyze(f)['pool']['upstream_fraction'],0)


if __name__=='__main__':unittest.main()
