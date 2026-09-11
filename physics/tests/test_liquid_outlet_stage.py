import sys
from pathlib import Path
import unittest
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from liquid_outlet_stage import outlet_pressure_grid


class OutletStageTest(unittest.TestCase):
    def profile(self):
        p = np.zeros((260, 3))
        p[2] = [32.8125, 1050, 350]
        p[3] = [800/24, 64, 24]
        p[4:] = [400, 600, 100]
        p[68:132, 2] = -100
        return {'packed_vectors': p}

    def test_only_outgoing_ghosts_above_bed_have_pressure_boundary(self):
        known, pressure = outlet_pressure_grid(self.profile())
        self.assertFalse(known[:, 2:66, 2:66].any())
        self.assertFalse(known[:, :, :2].any())
        self.assertFalse(known[:2].any())
        self.assertTrue(known[2:, 2:66, 66:].all())
        self.assertTrue((pressure[~known] == 0).all())
        self.assertAlmostEqual(pressure[3, 10, 66]-pressure[4, 10, 66], 980*800/24, places=7)
        self.assertTrue((pressure[8:] == 0).all())

    def test_inflow_never_becomes_pressure_outlet(self):
        profile = self.profile()
        profile['packed_vectors'][4:, 2] = 100
        known, pressure = outlet_pressure_grid(profile)
        self.assertFalse(known.any())
        self.assertFalse(pressure.any())

    def test_wrong_fixture_rejected(self):
        profile = self.profile()
        profile['packed_vectors'][2, 0] = 30
        with self.assertRaises(ValueError):
            outlet_pressure_grid(profile)


if __name__ == '__main__':
    unittest.main()
