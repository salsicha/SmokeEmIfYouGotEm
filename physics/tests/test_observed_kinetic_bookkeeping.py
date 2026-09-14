import unittest
import numpy as np
from audit_observed_kinetic_bookkeeping import bookkeeping


class KineticBookkeepingTests(unittest.TestCase):
    def test_chain_rule_and_read_only(self):
        state = np.array([[[2., 6., 8.]]])
        rate = np.array([[[-.25, 1.5, -2.]]])
        pressure = np.array([[[.3, -.4]]])
        before = [a.tobytes() for a in (state, rate, pressure)]
        result = bookkeeping(state, rate, pressure)
        self.assertEqual(result['kinetic'].item(), 25.)
        self.assertAlmostEqual(result['kinetic_rate'].item(), -.375)
        self.assertAlmostEqual(result['pressure_work'].item(), -.7)
        self.assertAlmostEqual(result['nonpressure_rate'].item(), .325)
        self.assertEqual(before, [a.tobytes() for a in (state, rate, pressure)])

    def test_draining_cell_can_accelerate_while_losing_kinetic(self):
        # h_t/h=-2, m_t/m=-1.5: u grows but K_t/K=-1.
        result = bookkeeping(np.array([[[1., 2., 0.]]]),
                             np.array([[[-2., -3., 0.]]]), np.zeros((1, 1, 2)))
        self.assertEqual(result['kinetic_rate'].item(), -2.)

    def test_dry_and_tiny_positive_depth(self):
        state = np.array([[[0., 0., 0.], [1e-200, 3e-200, 4e-200]]])
        result = bookkeeping(state, np.zeros_like(state), np.zeros((1, 2, 2)))
        np.testing.assert_array_equal(result['velocity'][0], [[0., 0.], [3., 4.]])
        self.assertAlmostEqual(result['kinetic'][0, 1]/1e-200, 12.5)
        self.assertTrue(all(np.isfinite(a).all() for a in result.values()))


if __name__ == '__main__':
    unittest.main()
