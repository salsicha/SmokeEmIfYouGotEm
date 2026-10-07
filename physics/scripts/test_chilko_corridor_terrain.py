import unittest
import numpy as np

from assemble_chilko_corridor_terrain import fill_missing,route_tree,missing_near_route


class CorridorTerrainTests(unittest.TestCase):
    def test_fallback_never_modifies_native_pixels(self):
        native=np.array([[1,np.nan],[3,np.nan]],np.float32)
        owner=np.array([[1,0],[2,0]],np.uint16)
        coarse=np.array([[101,2],[103,4]],np.float32)
        height,kind=fill_missing(native,owner,coarse,np.array([[1,1],[1,0]],np.uint8))
        np.testing.assert_array_equal(height,[[1,2],[3,np.nan]])
        np.testing.assert_array_equal(kind,[[1,2],[1,0]])
        np.testing.assert_array_equal(native,[[1,np.nan],[3,np.nan]])
        np.testing.assert_array_equal(owner,[[1,0],[2,0]])

    def test_unavailable_coarse_stays_missing(self):
        height,kind=fill_missing(np.array([[np.nan]],np.float32),np.array([[0]],np.uint16),
            np.array([[np.nan]],np.float32),np.array([[1]],np.uint8))
        self.assertTrue(np.isnan(height[0,0]));self.assertEqual(kind[0,0],0)

    def test_unknown_source_or_inconsistent_owner_is_refused(self):
        for owner,classes in (([[0]],[[1]]),([[1]],[[9]])):
            with self.assertRaises(ValueError):
                fill_missing(np.array([[1]],np.float32),np.array(owner,np.uint16),
                    np.array([[2]],np.float32),np.array(classes,np.uint8))
        with self.assertRaises(ValueError):
            fill_missing(np.array([[np.inf]],np.float32),np.array([[1]],np.uint16),
                np.array([[2]],np.float32),np.array([[1]],np.uint8))

    def test_missing_cell_between_route_vertices_is_detected(self):
        tree=route_tree([[0,5],[10,5]])
        height=np.ones((10,10),np.float32);height[4,5]=np.nan
        self.assertEqual(missing_near_route(height,[0,0,10,10],tree,0),1)
        height[4,5]=1;height[0,5]=np.nan
        self.assertEqual(missing_near_route(height,[0,0,10,10],tree,0),0)

    def test_endpoint_and_pixel_extent_are_included(self):
        tree=route_tree([[0,0],[1,0]])
        height=np.array([[np.nan]],np.float32)
        self.assertEqual(missing_near_route(height,[1,0,2,1],tree,0),1)
        with self.assertRaises(ValueError):route_tree([[0,0],[0,0]])
        with self.assertRaises(ValueError):route_tree([[0,0],[1,0]],step=0)


if __name__=='__main__':unittest.main()
