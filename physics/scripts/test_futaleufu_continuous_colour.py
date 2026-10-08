import unittest
import numpy as np
from build_futaleufu_continuous_colour import registration, display_rgb


class ContinuousColourTests(unittest.TestCase):
    def test_corners_centres_and_world_y_reflection(self):
        g = dict(epsg=32718, shape=[652,844], transform=[10,0,737790,0,-10,5201340,0,0,1])
        o = np.array([739986.,5195961.5]); r = registration(g,o)
        xy = np.array([[737790,5201340],[746230,5194820],[737795,5201335]])
        world = (xy-o)*[100,-100]
        uv = world*r['scale_xy']+r['offset_xy']
        np.testing.assert_allclose(uv,[[0,0],[1,1],[.5/844,.5/652]],atol=1e-15)

    def test_unreviewed_frame_rejected(self):
        for change in (dict(epsg=32618),dict(transform=[10,1,0,0,-10,0]),dict(shape=[1,3])):
            g = dict(epsg=32718,shape=[3,4],transform=[10,0,0,0,-10,0]);g.update(change)
            with self.assertRaises(ValueError):registration(g,[0,0])

    def test_radiometry_and_colour_order(self):
        raw = dict(red=np.array([[4000,1000]]),green=np.array([[1000,4000]]),blue=np.array([[1000,1000]]))
        np.testing.assert_equal(display_rgb(raw,np.ones((1,2),bool)),[[[255,0,0],[0,255,0]]])
        with self.assertRaises(ValueError):display_rgb(raw,np.array([[True,False]]))


if __name__ == '__main__':unittest.main()
