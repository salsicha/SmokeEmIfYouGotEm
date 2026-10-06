import unittest
import numpy as np
from test_water_feature_subcell_geometry import box
from water_feature_box_face_certificate import certified_box_faces


class BoxFaceCertificateTests(unittest.TestCase):
    def test_fully_contained_faces(self):
        v, t = box([0, 0, 0], [2, 2, 2])
        masks = certified_box_faces(v, t, (2, 2, 2), [0, 0, 0], 1.)
        self.assertEqual([a.shape for a in masks], [(3, 2, 2), (2, 3, 2), (2, 2, 3)])
        self.assertTrue(all(a.all() for a in masks))

    def test_no_small_gap_cutoff(self):
        v, t = box([np.nextafter(0., 1.), 0, 0], [2, 2, 2])
        masks = certified_box_faces(v, t, (2, 2, 2), [0, 0, 0], 1.)
        self.assertFalse(masks[0][0].any())
        self.assertFalse(masks[1][0].any())
        self.assertFalse(masks[2][0].any())

    def test_partial_faces_not_certified(self):
        v, t = box([.5, 0, 0], [2, 2, 2]); masks = certified_box_faces(v, t, (2, 2, 2), [0, 0, 0], 1.)
        self.assertTrue(masks[0][1:].all()); self.assertFalse(masks[1][0].any())
        self.assertTrue(masks[1][1].all()); self.assertFalse(masks[2][0].any())

    def test_sheared_or_nonclosed_boxes_rejected(self):
        v, t = box([0, 0, 0], [2, 2, 2]); v[:, 2] += .5*v[:, 0]
        with self.assertRaises(ValueError):
            certified_box_faces(v, t, (2, 2, 2), [0, 0, 0], 1.)
        v, t = box([0, 0, 0], [2, 2, 2]); t[0] = t[1]
        with self.assertRaises(ValueError):
            certified_box_faces(v, t, (2, 2, 2), [0, 0, 0], 1.)


if __name__ == '__main__':
    unittest.main()
