import sys
import unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from liquid_surface_occupancy import fluid_core,centered_upsample,reconcile
from liquid_anisotropic_surface import upper_surface


class SurfaceOccupancyTest(unittest.TestCase):
    def test_core_requires_all_twenty_seven_neighbors_and_excludes_edges(self):
        types=np.zeros((7,7,7),int)
        types[3,3,3]=2
        core=fluid_core(types)
        self.assertFalse(core[2,2,2])
        self.assertFalse(core[3,3,3])
        self.assertFalse(core[0].any())
        self.assertTrue(core[1,1,1])

    def test_interpolation_uses_cell_centers_and_preserves_affine_fields(self):
        z,y,x=np.indices((4,4,4))+.5
        result=centered_upsample(2*x+3*y+z,(8,8,8))
        zz,yy,xx=(np.indices((8,8,8))+.5)/2
        np.testing.assert_allclose(result[1:-1,1:-1,1:-1],(2*xx+3*yy+zz)[1:-1,1:-1,1:-1])

    def test_interior_hole_filled_without_changing_outer_surface_or_source(self):
        types=np.full((8,8,8),2)
        types[:6]=0
        density=np.ones((16,16,16))
        density[12:]=0
        density[4:8,6:10,6:10]=0
        original=density.copy()
        result,confidence,parents=reconcile(density,types)
        np.testing.assert_allclose(result[4:8,6:10,6:10],1)
        np.testing.assert_array_equal(result[10:],original[10:])
        self.assertFalse(((density<.5)&(result>=.5)&(parents!=0)).any())
        np.testing.assert_array_equal(density,original)

    def test_isolated_fluid_cell_cannot_seed_a_false_body(self):
        types=np.full((5,5,5),2)
        types[2,2,2]=0
        result,_,_=reconcile(np.zeros((10,10,10)),types)
        self.assertFalse(result.any())

    def test_solver_core_can_raise_exposed_surface_to_a_grid_face(self):
        # Regression for the real capture: solver classification is not a
        # license to replace a lower particle-derived surface with a shelf.
        types=np.full((8,8,8),2);types[:6]=0
        z=(np.arange(16)+.5)[:,None,None]
        density=np.broadcast_to(np.clip(.5+.25*(7.3-z),0,1),(16,16,16)).copy()
        result,_,_=reconcile(density,types)
        before=upper_surface(density,(0,0,0),(16,16,16))
        after=upper_surface(result,(0,0,0),(16,16,16))
        self.assertAlmostEqual(before[8,8],7.3)
        self.assertAlmostEqual(after[8,8],10.)
        self.assertGreater(after[8,8]-before[8,8],2.)

    def test_invalid_categorical_and_mismatched_domains_rejected(self):
        for types in (np.zeros((2,2,2)),np.full((4,4,4),.5),np.full((4,4,4),np.nan)):
            with self.assertRaises(ValueError):
                fluid_core(types)
        with self.assertRaises(ValueError):
            reconcile(np.zeros((8,8,6)),np.zeros((4,4,4)))


if __name__=='__main__':
    unittest.main()
