"""Synthetic indexing/quadrature checks; not validation of cached CFD."""
import unittest
import numpy as np
from audit_water_feature_jet_flux import plane_flux, inlet_extent


class FluxTests(unittest.TestCase):
    def test_mac_face_and_anisotropic_area(self):
        phi = -np.ones((2, 3, 4))
        solid = np.ones_like(phi)
        velocity = np.zeros((*phi.shape, 3))
        velocity[:, :, 1, 2] = -2
        velocity[:, :, 2, 2] = -99  # Wrong face must not be sampled.
        row = plane_flux(phi, solid, velocity, 1, (.2, .3, .4), .5)
        self.assertAlmostEqual(row['signed_downward_flux_m3s'], .36)
        self.assertEqual(row['occupied_faces'], 6)

    def test_face_occupancy_and_bidirectional_budget(self):
        phi = -np.ones((2, 2, 3))
        solid = np.ones_like(phi)
        phi[0, 0, 0] = 3  # Face average positive despite upper liquid cell.
        solid[0, 1, :2] = -1
        velocity = np.zeros((*phi.shape, 3))
        velocity[1, 0, 1, 2] = -3
        velocity[1, 1, 1, 2] = 1
        row = plane_flux(phi, solid, velocity, 1, (1, 1, 1), 1)
        self.assertEqual(row['occupied_faces'], 2)
        self.assertEqual(row['signed_downward_flux_m3s'], 2)
        self.assertEqual(row['downward_only_flux_m3s'], 3)
        self.assertEqual(row['upward_only_flux_m3s'], 1)

    def test_invalid_layout_and_boundary(self):
        a = np.ones((2, 3, 4))
        v = np.zeros((*a.shape, 3))
        for k in (0, 4):
            with self.assertRaises(ValueError):
                plane_flux(a, a, v, k, (1, 1, 1), 1)
        with self.assertRaises(ValueError):
            plane_flux(a, a, v.transpose(1, 0, 2, 3), 1, (1, 1, 1), 1)

    def test_inlet_extent_mapping_and_empty_field(self):
        a = np.ones((2, 2, 3))
        a[1, 0, 1] = -1
        row = inlet_extent(a, (10, -2, -1), (2, 4, 6), (10, -2), 1, 9)
        self.assertEqual(row['center_bbox_min_m'], [13, 0, 8])
        self.assertEqual(row['negative_centers_below_nozzle'], 1)
        self.assertEqual(row['negative_centers_outside_inner_radius'], 1)
        empty = inlet_extent(np.ones_like(a), (0, 0, 0), (1, 1, 1), (0, 0), 1, 0)
        self.assertEqual(empty['negative_cells'], 0)
        self.assertIsNone(empty['center_bbox_min_m'])


if __name__ == '__main__':
    unittest.main()
