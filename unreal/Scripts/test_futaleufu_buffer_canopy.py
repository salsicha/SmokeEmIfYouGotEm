import unittest
import numpy as np
from qualify_futaleufu_buffer_canopy import eligible


class BufferCanopyTests(unittest.TestCase):
    def test_ground_changes_and_crown_clearance_are_independent(self):
        np.testing.assert_array_equal(eligible([12,12,14,14,20],[3,5,6,6,3],[0,0,0,.01,np.nan]),
                                      [True,False,True,False,False])

    def test_nonfinite_and_invalid_radii_are_rejected(self):
        np.testing.assert_array_equal(eligible([np.nan,np.inf,20,20],[3,3,0,-1],[0,0,0,0]),[False]*4)


if __name__=='__main__':unittest.main()
