import unittest
from expand_futaleufu_hydraulic_halo import expanded_keys


class DrySupportTests(unittest.TestCase):
    def test_exact_chebyshev_layers(self):
        available={(i,j) for i in range(-3,4) for j in range(-3,4)}
        self.assertEqual(expanded_keys({(0,0)},available,set(),2),
            {(i,j) for i in range(-2,3) for j in range(-2,3)})

    def test_port_crop_and_missing_support_are_preserved(self):
        available={(i,j) for i in range(-3,4) for j in range(-3,4)}-{(1,1)}
        excluded={(i,j) for i,j in available if i<0}
        result=expanded_keys({(0,0)},available,excluded,2)
        self.assertFalse(result & excluded)
        self.assertNotIn((1,1),result)
        self.assertIn((0,0),result)
        self.assertIn((2,1),result)
        self.assertNotIn((2,2),result)  # Missing (1,1) blocks the two-step diagonal.

    def test_invalid_support_and_bounds_refuse(self):
        for layers in (0,4,True,1.5):
            with self.assertRaises(ValueError):expanded_keys({(0,0)},{(0,0)},set(),layers)
        with self.assertRaises(ValueError):expanded_keys({(0,0)},set(),set(),1)
        with self.assertRaises(ValueError):expanded_keys({(0,0)},{(0,0)},{(0,0)},1)
