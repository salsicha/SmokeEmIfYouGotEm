import sys
import unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from diagnose_liquid_transfer_occupancy import measure


class TransferOccupancyTest(unittest.TestCase):
    def test_halos_are_not_additional_water(self):
        total=np.zeros((3,6,6,4));total[...,3]=100
        total[:,2:-2,2:-2,3]=.25
        result=measure(total,.5)
        self.assertEqual(result['physical_cells'],12)
        self.assertEqual(result['deposited_volume_m3'],3)
        self.assertEqual(result['nonzero_support_cell_volume_m3'],6)

    def test_tiny_support_is_reported_without_being_promoted_to_volume(self):
        total=np.zeros((1,1,6,4));total[...,3]=[0,.001,.05,.25,.5,1.5]
        result=measure(total,1,halo=0)
        self.assertEqual(result['supported_cells'],5)
        self.assertAlmostEqual(result['deposited_volume_m3'],2.301)
        self.assertEqual(sum(b['cells'] for b in result['density_bins']),5)
        self.assertAlmostEqual(sum(b['deposited_volume_m3'] for b in result['density_bins']),2.301)

    def test_invalid_mass_is_rejected(self):
        for value in (-1,float('nan'),float('inf')):
            total=np.zeros((2,5,5,4));total[0,2,2,3]=value
            with self.assertRaises(ValueError):measure(total,1)


if __name__=='__main__':unittest.main()
