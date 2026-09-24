import unittest
from audit_cartesian_tile_flux import face_accounting


class FaceAccountingTest(unittest.TestCase):
    def grids(self):
        return [dict(nx=2, ny=3, dx=2., dy=1., origin_x=x, origin_y=0.) for x in (0., 4.)]

    def test_shared_sign_and_exterior(self):
        result = face_accounting(self.grids(), [[3., -5., 0., 0.], [5., -7., 0., 0.]])
        self.assertEqual(result['shared_face_pairs'], 1)
        self.assertEqual(result['maximum_shared_face_mismatch_m3s'], 0.)
        self.assertEqual(result['exterior_net_inflow_m3s'], -4.)
        self.assertEqual(len(result['exterior_faces']), 6)

    def test_seam_mismatch_not_hidden_in_exterior(self):
        result = face_accounting(self.grids(), [[3., -5., 0., 0.], [4., -7., 0., 0.]])
        self.assertEqual(result['maximum_shared_face_mismatch_m3s'], 1.)
        self.assertEqual(result['shared_face_net_residual_m3s'], -1.)
        self.assertEqual(result['exterior_net_inflow_m3s'], -4.)

    def test_north_south_shared_pair(self):
        grids = self.grids()
        grids[1].update(origin_x=0., origin_y=3.)
        result = face_accounting(grids, [[0., 0., 3., -5.], [0., 0., 5., -7.]])
        self.assertEqual(result['shared_face_pairs'], 1)
        self.assertEqual(result['maximum_shared_face_mismatch_m3s'], 0.)
        self.assertEqual(result['exterior_net_inflow_m3s'], -4.)

    def test_duplicate_and_off_lattice_rejected(self):
        for x in (0., 4.1):
            grids = self.grids()
            grids[1]['origin_x'] = x
            with self.assertRaises(ValueError):
                face_accounting(grids, [[0.]*4]*2)

    def test_nonfinite_rejected(self):
        with self.assertRaises(ValueError):
            face_accounting(self.grids(), [[float('nan')]*4]*2)


if __name__ == '__main__':
    unittest.main()
