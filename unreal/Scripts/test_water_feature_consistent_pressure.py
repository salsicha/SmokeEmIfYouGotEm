import unittest
import numpy as np
from water_feature_consistent_pressure import PressureBoundary, flux_divergence


def fixture():
    flags = np.full((7, 6, 6), 2, np.int32); flags[1:-1, 1:-1, 1:4] = 1; flags[1:-1, 1:-1, 4] = 4
    phi = np.full(flags.shape, 1.); phi[flags == 1] = -.25
    f = np.zeros((*flags.shape, 3))
    for axis in range(3):
        sl = [slice(None)]*3; lo = list(sl); sl[axis] = slice(1, None); lo[axis] = slice(None, -1)
        both = (((flags[tuple(lo)] & 1) != 0) & ((flags[tuple(sl)] & (1|4)) != 0)) | (((flags[tuple(sl)] & 1) != 0) & ((flags[tuple(lo)] & (1|4)) != 0))
        f[tuple(sl)+(axis,)] = both*.375
    return flags, phi, f


class ConsistentPressureTests(unittest.TestCase):
    def test_symmetric_positive_operator(self):
        flags, phi, f = fixture(); model = PressureBoundary(flags, phi, f); rng = np.random.default_rng(812)
        a = rng.normal(size=flags.shape)*model.fluid; b = rng.normal(size=flags.shape)*model.fluid
        self.assertAlmostEqual(float(np.sum(a*model.apply(b))), float(np.sum(b*model.apply(a))), places=12)
        self.assertGreater(float(np.sum(a*model.apply(a))), 0.)

    def test_gradient_flux_matrix_identity(self):
        flags, phi, f = fixture(); model = PressureBoundary(flags, phi, f); rng = np.random.default_rng(132)
        p = rng.normal(size=flags.shape)*model.fluid; v = rng.normal(size=f.shape)
        actual = flux_divergence(model.correct(v, p), f)-flux_divergence(v, f)
        np.testing.assert_allclose(actual[model.fluid], model.apply(p)[model.fluid], atol=2e-14, rtol=1e-14)

    def test_manufactured_solution(self):
        flags, phi, f = fixture(); model = PressureBoundary(flags, phi, f)
        p = np.random.default_rng(21).normal(size=flags.shape)*model.fluid
        recovered, proof = model.solve(model.apply(p), tolerance=1e-10)
        np.testing.assert_allclose(recovered, p, atol=1e-9, rtol=0)
        self.assertLessEqual(proof['maximum_fresh_residual'], 1e-10)

    def test_projected_divergence(self):
        flags, phi, f = fixture(); model = PressureBoundary(flags, phi, f)
        v = np.random.default_rng(93).normal(size=f.shape); after, _, proof = model.project(v, tolerance=1e-10)
        self.assertLess(np.max(np.abs(flux_divergence(after, f)[model.fluid])), 2e-10)

    def test_area_weights_liquid_interface_diagonal(self):
        flags, phi, f = fixture(); model = PressureBoundary(flags, phi, f)
        # theta=.2, so one top interface contributes .375/.2, not
        # .375+(1/.2-1) as an unweighted ghost-fluid diagonal would.
        self.assertAlmostEqual(model.diagonal[3, 2, 3], 5*.375+.375/.2)

    def test_outflow_velocity_frozen_on_both_orientations(self):
        for side in (1, 5):
            flags, phi, f = fixture(); flags[side, 1:-1, 1:4] = 4|16; phi[side, 1:-1, 1:4] = 1.
            model = PressureBoundary(flags, phi, f); p = np.ones(flags.shape)*model.fluid
            v = np.random.default_rng(6).normal(size=f.shape); after = model.correct(v, p)
            index = 2 if side == 1 else 5
            np.testing.assert_array_equal(v[index, 1:-1, 1:4, 0], after[index, 1:-1, 1:4, 0])

    def test_uncoupled_and_wrong_sign_rejected(self):
        flags, phi, f = fixture()
        with self.assertRaises(ValueError):
            PressureBoundary(flags, phi, f*0)
        phi[flags == 4] = -.1
        with self.assertRaises(ValueError):
            PressureBoundary(flags, phi, f)

    def test_actual_pressure_support_required(self):
        flags, phi, f = fixture(); model = PressureBoundary(flags, phi, f)
        with self.assertRaises(ValueError):
            model.apply(np.ones(flags.shape))


if __name__ == '__main__':
    unittest.main()
