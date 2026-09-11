from pathlib import Path
import sys
import unittest
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from audit_liquid_live_occupancy import compare
from liquid_surface_occupancy import reconcile


class LiveOccupancyAuditTest(unittest.TestCase):
    def fixture(self):
        boundary=np.zeros((11,11,11));boundary[0]=1;boundary[-1]=2;boundary[:,:,0]=3
        boundary[5,5,5]=1
        density=np.full((22,22,22),.1)
        after,confidence,_=reconcile(density,boundary)
        gpu=np.stack((.5-after,confidence),axis=-1)
        return density,boundary,gpu,np.sign(gpu[...,0])

    def test_parity_and_solid_preservation(self):
        result=compare(*self.fixture())
        self.assertTrue(result['gpu_cpu_parity'])
        self.assertGreater(result['air_in_fully_supported_interior_before'],0)
        self.assertEqual(result['air_in_fully_supported_interior_after'],0)
        self.assertEqual(result['newly_wet_in_nonfluid_parent_cells'],0)

    def test_particle_surface_bypass_must_display_original_not_the_floor(self):
        density,boundary,gpu,filled=self.fixture()
        original=np.sign(.5-density)
        self.assertTrue(compare(density,boundary,gpu,original,apply_floor=False)['gpu_cpu_parity'])
        self.assertFalse(compare(density,boundary,gpu,filled,apply_floor=False)['gpu_cpu_parity'])
        self.assertFalse(compare(density,boundary,gpu,original,apply_floor=True)['gpu_cpu_parity'])

    def test_rejects_output_confidence_and_display_corruption(self):
        for channel in (0,1):
            density,boundary,gpu,display=self.fixture();gpu[2,2,2,channel]+=.01
            self.assertFalse(compare(density,boundary,gpu,display)['gpu_cpu_parity'])
        density,boundary,gpu,display=self.fixture();display=-display
        self.assertFalse(compare(density,boundary,gpu,display)['gpu_cpu_parity'])

    def test_rejects_new_water_in_solid_even_if_display_matches(self):
        density,boundary,gpu,display=self.fixture()
        gpu[10,10,10,0]=-1;display[10,10,10]=-1
        result=compare(density,boundary,gpu,display)
        self.assertFalse(result['gpu_cpu_parity'])
        self.assertGreater(result['newly_wet_in_nonfluid_parent_cells'],0)


if __name__=='__main__':unittest.main()
