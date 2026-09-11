"""Native face selection must preserve the requested physical coverage."""
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from audit_south_fork_liquid_flux import control_volume_indices


class ControlVolumeTests(unittest.TestCase):
    def setUp(self):
        self.grid=SimpleNamespace(origin_x=-135.,origin_y=-80.,dx=1.,dy=1.,nx=271,ny=161)

    def test_legacy_and_full_rapid_faces(self):
        self.assertEqual(control_volume_indices(self.grid,[[-10.5,-10.5],[10.5,10.5]]),(125,70,146,91))
        self.assertEqual(control_volume_indices(self.grid,[[-112.5,-40.5],[132.5,40.5]]),(23,40,268,121))

    def test_no_clamping_or_rounding_into_a_different_domain(self):
        for bounds in ([[-10,-10],[10,10]],[[-136.5,-40.5],[132.5,40.5]],
                       [[10.5,-1.5],[-10.5,1.5]],[[float('nan'),0],[1,2]]):
            with self.assertRaises(ValueError):control_volume_indices(self.grid,bounds)


if __name__=='__main__':unittest.main()
