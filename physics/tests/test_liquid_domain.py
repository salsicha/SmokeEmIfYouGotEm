from pathlib import Path
import sys
import unittest
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from liquid_domain import layout
from build_south_fork_liquid_grid_boundary import remap_boundary_flux


class LiquidDomainTests(unittest.TestCase):
    def test_boundary_noise_allowance_never_discards_incoming_water(self):
        np.testing.assert_array_equal(remap_boundary_flux([-2e-9,2.],[0.,1.]),[0.,2.])
        with self.assertRaisesRegex(ValueError,'wet support'):
            remap_boundary_flux([2e-9,2.],[0.,1.])
        with self.assertRaisesRegex(ValueError,'wet support'):
            remap_boundary_flux([-2e-6,2.],[0.,1.])

    def test_legacy_face_extent_and_nominal_volume_are_preserved(self):
        result=layout({'fluid_domain_local_bounds_m':[[-10,-10,0],[10,10,8]]},
                      {'local_station_lateral_face_bounds_m':[[-10.5,-10.5],[10.5,10.5]]})
        self.assertEqual(result['computational_cells'],[68,68,24])
        self.assertEqual(result['nominal_particle_volume_m3'],(21/64)**3/4)
        changed=layout({'fluid_domain_local_bounds_m':[[-10,-10,0],[10,10,8]]},
                       {'local_station_lateral_face_bounds_m':[[-10.5,-10.5],[10.5,10.5]]},[32,32])
        self.assertFalse(changed['legacy_fixture'])
        self.assertEqual(changed['physical_cells'],[32,32,24])

    def test_full_rectangle_keeps_origin_spacing_and_counts_distinct(self):
        result=layout({'fluid_domain_local_bounds_m':[[-122.5,-40.5,0],[122.5,40.5,8]],'centre_station_lateral_m':[10,0]},
                      {'local_station_lateral_face_bounds_m':[[-112.5,-40.5],[132.5,40.5]]},[490,162])
        self.assertEqual(result['computational_cells'],[494,166,24])
        self.assertEqual(result['centre_station_lateral_m'],[10,0])
        np.testing.assert_allclose(result['cell_size_m'],[.5,.5,1/3])
        self.assertAlmostEqual(result['nominal_particle_volume_m3'],1/48)
        self.assertFalse(result['runtime_support_verified'])

    def test_nonlegacy_no_silent_extent_or_resolution_fallback(self):
        window={'fluid_domain_local_bounds_m':[[-20,-10,0],[20,10,8]]}
        audit={'local_station_lateral_face_bounds_m':[[-20,-10],[20,10]]}
        with self.assertRaises(ValueError):layout(window,audit)
        with self.assertRaises(ValueError):layout(window,audit,[64.5,64])
        with self.assertRaises(ValueError):layout(window,{'local_station_lateral_face_bounds_m':[[-10.5,-10.5],[10.5,10.5]]},[64,64])


if __name__=='__main__':unittest.main()
