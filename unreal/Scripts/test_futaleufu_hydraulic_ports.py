import unittest
import numpy as np
import shapely
from prepare_futaleufu_hydraulic_ports import make_port, outside_port, subdivide


class HydraulicPortTests(unittest.TestCase):
    def test_ports_stay_outside_gameplay_and_clear_new_caps(self):
        line=shapely.LineString([(0,0),(2000,0)])
        p=make_port(line,400,np.array([0.,0.]),True,'in')
        self.assertEqual(p['coordinate_m'],56)
        self.assertEqual(p['remaining_buffer_m'],344)
        self.assertEqual(p['retained_sign'],1)
        p=make_port(line,400,np.array([0.,0.]),False,'out')
        self.assertEqual(p['coordinate_m'],1932)
        self.assertEqual(p['retained_sign'],-1)

    def test_returning_interior_is_not_removed_by_a_global_plane(self):
        line=shapely.LineString([(0,0),(1000,0),(1000,100),(-100,100)])
        p=make_port(line,400,np.array([0.,0.]),True,'in')
        q=np.array([[20,0],[80,0],[0,100]])
        np.testing.assert_array_equal(outside_port(q,[line],[p]),[True,False,False])

    def test_retile_copies_every_cell_once_with_northward_negative_indices(self):
        a=np.arange(252*252).reshape(252,252);pieces=dict(subdivide((-2,3),dict(h=a)))
        self.assertEqual(len(pieces),81)
        result=np.empty_like(a)
        for (x,y),v in pieces.items():result[(y-27)*28:(y-26)*28,(x+18)*28:(x+19)*28]=v['h']
        np.testing.assert_array_equal(result,a)

    def test_short_buffer_rejected(self):
        with self.assertRaises(ValueError):make_port(shapely.LineString([(0,0),(1000,0)]),310,np.zeros(2),True,'in')


if __name__=='__main__':unittest.main()
