import sys
from pathlib import Path
import unittest
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from liquid_secondary_contact import segment_triangle_contact as hit


class SecondarySweptContactTests(unittest.TestCase):
    ground=np.array([[0,0,0],[100,0,0],[0,100,0]])

    def test_clear_path(self):
        self.assertFalse(hit([10,10,5],[20,20,5],self.ground))

    def test_vertical_crossing(self):
        self.assertTrue(hit([10,10,5],[10,10,-5],self.ground))

    def test_inside_initially(self):
        self.assertTrue(hit([10,10,-5],[10,10,5],self.ground))

    def test_outside_triangle_not_plane_collision(self):
        self.assertFalse(hit([90,90,5],[90,90,-5],self.ground))

    def test_vertex_and_stationary_contact(self):
        self.assertTrue(hit([0,0,3],[0,0,-1],self.ground))
        self.assertTrue(hit([10,10,0],[10,10,0],self.ground))

    def test_narrow_ridge_between_five_point_samples(self):
        ridge=np.array([[11,0,10],[12,0,10],[11,100,10]])
        start=np.array([0,1,5]);end=np.array([100,1,5])
        self.assertTrue(hit(start,end,ridge))
        self.assertFalse(any(hit(start+t*(end-start),start+t*(end-start),ridge) for t in np.linspace(0,1,5)))

    def test_sloping_bed_and_translation(self):
        slope=self.ground.copy();slope[1,2]=100
        a=np.array([5.,10,20]);b=np.array([50.,10,20])
        self.assertTrue(hit(a,b,slope))
        offset=np.array([-321.5,119.3,731.2])
        self.assertTrue(hit(a+offset,b+offset,slope+offset))

    def test_degenerate_and_nonfinite_rejected(self):
        with self.assertRaises(ValueError):hit([0,0,1],[0,0,-1],np.zeros((3,3)))
        with self.assertRaises(ValueError):hit([np.nan,0,1],[0,0,-1],self.ground)


if __name__=='__main__':unittest.main()
