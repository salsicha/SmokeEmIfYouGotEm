"""Independent mathematical checks for centered Niagara P2G tent support."""
import unittest
import numpy as np


def metric_weights(points, center, unit_to_world_rows, cells):
    rows = np.asarray(unit_to_world_rows, dtype=float)
    lengths = np.linalg.norm(rows, axis=1)
    offset = (points-center) @ (rows/lengths[:, None]).T
    offset *= np.asarray(cells)/lengths
    return np.maximum(1-np.abs(offset), 0).prod(axis=-1)


class CenteredTransferTest(unittest.TestCase):
    def setUp(self):
        self.index = np.array([4, 4, 4])
        self.center = self.index+.5
        axis = np.arange(2.125, 7, .25)
        self.points = np.stack(np.meshgrid(axis, axis, axis, indexing='ij'), axis=-1).reshape(-1, 3)

    def test_old_equal_weight_gather_has_half_cell_bias(self):
        bins = np.floor(self.points).astype(int)
        old = ((bins >= self.index-1) & (bins <= self.index)).all(axis=1)
        np.testing.assert_allclose(self.points[old].mean(axis=0)-self.center, [-.5]*3)

    def test_centered_support_needs_positive_neighbor_bins(self):
        weights = metric_weights(self.points, self.center, np.eye(3)*8, [8]*3)
        bins = np.floor(self.points[weights > 0]).astype(int)
        np.testing.assert_array_equal(bins.min(axis=0), self.index-1)
        np.testing.assert_array_equal(bins.max(axis=0), self.index+1)
        np.testing.assert_allclose(np.average(self.points, axis=0, weights=weights), self.center)

    def test_preserves_uniform_and_affine_fields_on_uniform_quadrature(self):
        weights = metric_weights(self.points, self.center, np.eye(3)*8, [8]*3)
        gradient = np.array([[2., -1., .3], [.5, 0., 1.], [-.4, .7, 2.]])
        constant = np.array([138., -27., 0.])
        velocity = self.points @ gradient.T + constant
        np.testing.assert_allclose(np.average(velocity, axis=0, weights=weights), self.center @ gradient.T+constant)
        np.testing.assert_allclose(np.average(np.broadcast_to(constant, velocity.shape), axis=0, weights=weights), constant)

    def test_rotated_anisotropic_grid_uses_local_cell_metric(self):
        angle = np.deg2rad(158.434789)
        rotation = np.array([[np.cos(angle), np.sin(angle), 0.], [-np.sin(angle), np.cos(angle), 0.], [0., 0., 1.]])
        lengths = np.array([22.3125, 22.3125, 8.])
        cells = np.array([68, 68, 24])
        rows = rotation*lengths[:, None]
        spacing = lengths/cells
        origin = np.array([151., -53., 3.5])
        points = (self.points*spacing) @ rotation+origin
        center = (self.center*spacing) @ rotation+origin
        actual = metric_weights(points, center, rows, cells)
        expected = metric_weights(self.points, self.center, np.eye(3)*8, [8]*3)
        np.testing.assert_allclose(actual, expected, atol=1e-12)


if __name__ == '__main__':
    unittest.main()
