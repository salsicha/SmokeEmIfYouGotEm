import unittest
import numpy as np
from reconstructed_pressure_geometry import ReconstructedPressureGeometry
from reconstructed_pressure_rates import PressureGeometryRate, kinematic_forcing
from directional_pressure_geometry import DirectionalPressureGeometry
from difference_scalar_gradient_reference import difference_gradient, difference_scalar_gradients


def geometry(n=16, amplitude=.2):
    x = (np.arange(n)+.5)/n
    bed = np.tile(amplitude*np.sin(2*np.pi*x), (2, 1))
    return ReconstructedPressureGeometry(1-bed, bed, 1/n, periodic=True,
        pressure_trace='integrated_column', bed_quadrature='shared_bottom')


class DifferenceScalarTests(unittest.TestCase):
    def test_constant_and_uniform_advection_exactly_zero(self):
        g = geometry()
        tangent = PressureGeometryRate(g, g.bed, np.zeros_like(g.h))
        u = np.ones((*g.h.shape, 2))
        with difference_scalar_gradients():
            np.testing.assert_array_equal(g.scalar_gradient(np.ones_like(g.h)), 0.)
            np.testing.assert_array_equal(kinematic_forcing(g, tangent, u)[2], 0.)

    def test_matches_row_sum_subtraction_algebra(self):
        g = geometry()
        f = np.random.default_rng(4).normal(size=g.h.shape)
        expected = g.scalar_gradient(f)-f[..., None]*g.scalar_gradient(np.ones_like(f))
        np.testing.assert_allclose(difference_gradient(g, f), expected, rtol=2e-14, atol=2e-14)

    def test_smooth_manufactured_derivative_refines_second_order(self):
        errors = []
        for n in (16, 32, 64):
            g = geometry(n)
            x = (np.arange(n)+.5)/n
            f = np.tile(np.sin(2*np.pi*x), (2, 1))
            expected = np.tile(2*np.pi*np.cos(2*np.pi*x), (2, 1))
            errors.append(float(abs(difference_gradient(g, f)[..., 0]-expected).max()))
        self.assertGreater(errors[0]/errors[1], 3.)
        self.assertGreater(errors[1]/errors[2], 3.)

    def test_pressure_action_and_kinematics_unmodified(self):
        g = geometry()
        random = np.random.default_rng(6)
        p, b = random.normal(size=(2, *g.h.shape))
        u = random.normal(size=(*g.h.shape, 2))
        original = g.gradient_traction(p, b).tobytes(), *(a.tobytes() for a in g.kinematic_components(u))
        with difference_scalar_gradients():
            actual = g.gradient_traction(p, b).tobytes(), *(a.tobytes() for a in g.kinematic_components(u))
        self.assertEqual(original, actual)

    def test_directional_dry_support_retained(self):
        h = np.array([[0., .3, 1., .4], [0., .3, 1., .4]])
        g = ReconstructedPressureGeometry(h, np.zeros_like(h), .5, periodic=True,
            pressure_trace='integrated_column', bed_quadrature='shared_bottom')
        ht = np.zeros_like(h); ht[:, 0] = .1
        entering = DirectionalPressureGeometry(g, ht)
        before = entering.h.tobytes()
        with difference_scalar_gradients():
            np.testing.assert_array_equal(entering.scalar_gradient(np.ones_like(h)), 0.)
        self.assertEqual(before, entering.h.tobytes())
        self.assertTrue(np.all(entering.kinematic_support))

    def test_error_restores_original_method(self):
        original = ReconstructedPressureGeometry.scalar_gradient
        with self.assertRaisesRegex(RuntimeError, 'expected'):
            with difference_scalar_gradients():
                raise RuntimeError('expected')
        self.assertIs(original, ReconstructedPressureGeometry.scalar_gradient)


if __name__ == '__main__':
    unittest.main()
