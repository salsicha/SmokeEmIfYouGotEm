import math
import unittest
from types import SimpleNamespace
import numpy as np
from triangle_cell_storage import TriangleCellStorage
from triangle_face_section import TriangleFaceSection
from subcell_geometry_patch import SubcellGeometryPatch
from subcell_energy_flux import pressure_secant_area, face_flux, rates
from test_triangle_face_section import sampler


class SubcellEnergyFluxTest(unittest.TestCase):
    def test_pressure_secant_matches_independent_segment_quadrature(self):
        section = TriangleFaceSection([[[0., .3], [.4, -.2]], [[.4, -.2], [1., 1.7]]], [0., 1.])
        nodes, weights = np.polynomial.legendre.leggauss(3)
        for low, high in ((-.4, 2.), (.1, .8), (.3, .3), (-1., -1.), (.5, .5+1e-12)):
            expected = 0.
            for (x0, z0), (x1, z1) in section.segments:
                cuts = [x0, x1]
                if z0 != z1:
                    for eta in (low, high):
                        x = x0+(eta-z0)*(x1-x0)/(z1-z0)
                        if x0 < x < x1:
                            cuts.append(x)
                cuts.sort()
                for a, b in zip(cuts, cuts[1:]):
                    x = (a+b)/2+(b-a)/2*nodes
                    bed = z0+(x-x0)*(z1-z0)/(x1-x0)
                    hl, hr = np.maximum(low-bed, 0), np.maximum(high-bed, 0)
                    if high == low:
                        mean = hl
                    else:
                        mean = np.where(hl > 0, .5*(hl+hr), .5*hr*(hr/(high-low)))
                    expected += (b-a)/2*float(weights@mean)
            actual = pressure_secant_area(section, low, high)
            self.assertAlmostEqual(actual, expected, places=13)
            self.assertEqual(actual, pressure_secant_area(section, high, low))

    def test_flat_and_thin_partial_secants_have_no_depth_floor(self):
        flat = TriangleFaceSection([[[0., 8.], [1., 8.]]], [0., 1.])
        slope = TriangleFaceSection([[[0., 8.], [1., 9.]]], [0., 1.])
        for h in (1e-2, 1e-50, 1e-150):
            self.assertEqual(pressure_secant_area(flat, h, h, 8., 8.), h)
            np.testing.assert_allclose(pressure_secant_area(flat, 0., h, 8., 8.), .5*h, atol=0, rtol=1e-14)
            np.testing.assert_allclose(pressure_secant_area(slope, 0., h, 8., 8.), h*(h/6), atol=0, rtol=1e-14)

    def test_exact_face_energy_identity_both_axes_with_and_without_dissipation(self):
        section = TriangleFaceSection([[[0., -.2], [.5, .9]], [[.5, .9], [1., .3]]], [0., 1.])
        rng = np.random.default_rng(9657)
        for axis in (0, 1):
            for stable in (False, True):
                for _ in range(80):
                    el, er = rng.uniform(-.5, 2., 2)
                    ul, ur = rng.normal(size=(2, 2))
                    flux, audit = face_flux(section, el, ul, er, ur, axis, dissipative=stable)
                    chi = 9.81*(er-el)-.5*(ur@ur-ul@ul)
                    actual = chi*flux[0]+(ur-ul)@flux[1:]+ul[axis]*audit['left_pressure']-ur[axis]*audit['right_pressure']
                    self.assertAlmostEqual(actual, audit['expected_energy_work'], places=11)
                    self.assertLessEqual(audit['expected_energy_work'], 0.)

    def test_dissipative_flux_cannot_donate_from_a_dry_face(self):
        section = TriangleFaceSection([[[0., 0.], [1., 1.]]], [0., 1.])
        for axis in (0, 1):
            for speed in (-100., -1., 0., 1., 100.):
                u = np.array([speed, speed])
                f, _ = face_flux(section, 0., u, .2, u, axis, dissipative=True)
                self.assertLessEqual(f[0], 0.)
                f, _ = face_flux(section, .2, u, 0., u, axis, dissipative=True)
                self.assertGreaterEqual(f[0], 0.)

    def test_energy_conservation_alone_does_not_authorize_dry_front_evolution(self):
        section = TriangleFaceSection([[[0., 0.], [1., 1.]]], [0., 1.])
        # An exactly dry cell has zero velocity. The central flux can still
        # send water out of it when the wet-side velocity points downstream.
        # Preserve this obstruction; never advertise energy as positivity.
        central, _ = face_flux(section, 0., [0., 0.], .2, [2., 0.], 0)
        stable, _ = face_flux(section, 0., [0., 0.], .2, [2., 0.], 0, dissipative=True)
        self.assertGreater(central[0], 0.)
        self.assertLessEqual(stable[0], 0.)

    def test_distinct_datums_describe_the_same_physical_face_flux(self):
        section = TriangleFaceSection([[[0., 8.], [1., 9.]]], [0., 1.])
        for stable in (False, True):
            baseline, _ = face_flux(section, 8.25, [.7, -.2], 8.75, [-.3, .1], 1, dissipative=stable)
            relative, _ = face_flux(section, .25, [.7, -.2], .25, [-.3, .1], 1,
                                    left_datum=8., right_datum=8.5, dissipative=stable)
            np.testing.assert_allclose(relative, baseline, atol=0, rtol=1e-14)

    def test_smooth_base_pde_rates_converge_at_second_order(self):
        errors = []
        for n in (16, 32, 64):
            dx = 2*np.pi/n
            # Independent flat rectangular-cell fixture with exact areas and
            # one periodic face per cell; no source interpolation to hide error.
            cell = TriangleCellStorage(np.array([[[0., 0., 0.], [dx, 0., 0.], [0., 1., 0.]],
                                                 [[dx, 0., 0.], [dx, 1., 0.], [0., 1., 0.]]]))
            face = TriangleFaceSection([[[0., 0.], [1., 0.]]], [0., 1.])
            patch = SimpleNamespace(shape=(1, n), cells=[cell]*n,
                faces=[(i, (i+1)%n, 0, face) for i in range(n)])
            x = np.arange(n)*dx
            h, u = 1+.1*np.sin(x), .2+.05*np.cos(x)
            hx, ux = .1*np.cos(x), -.05*np.sin(x)
            volume = (h*dx)[None, :]
            momentum = np.stack((volume*u, np.zeros_like(volume)), axis=-1)
            r = rates(patch, volume, momentum)
            exact_h = -(hx*u+h*ux)
            exact_p = -(hx*u*u+2*h*u*ux+9.81*h*hx)
            errors.append(np.linalg.norm(r['volume_rate'][0]/dx-exact_h)/np.sqrt(n)
                          +np.linalg.norm(r['momentum_rate'][0, :, 0]/dx-exact_p)/np.sqrt(n))
            self.assertLess(abs(r['energy_rate']), 1e-11)
        self.assertGreater(errors[0]/errors[1], 3.8)
        self.assertGreater(errors[1]/errors[2], 3.9)

    def test_periodic_constant_velocity_obstruction_is_removed_in_base_flux(self):
        for axis in (0, 1):
            shape = (1, 3) if axis == 0 else (3, 1)
            origin = [-1., 0.] if axis == 0 else [0., -1.]
            patch = SubcellGeometryPatch(sampler(lambda x, y: x*0), origin, shape, periodic=(True, True))
            for sign in (-1., 1.):
                u = np.zeros((*shape, 2));u[..., axis] = .5*sign
                volume, momentum = patch.state_from_stages(np.array([1., 2., 4.]).reshape(shape), u)
                r = rates(patch, volume, momentum)
                self.assertLess(abs(r['volume_rate'].sum()), 1e-12)
                np.testing.assert_allclose(r['momentum_rate'].sum(axis=(0, 1)), 0., atol=1e-12)
                self.assertLess(abs(r['energy_rate']), 1e-11)
                self.assertFalse(r['time_or_two_pole_or_gameplay_accepted'])

    def test_rough_partial_wet_terrain_balances_energy_and_lake_at_rest(self):
        patch = SubcellGeometryPatch(sampler(lambda x, y: .6+.7*np.cos(x*2)*np.cos(y*2)),
                                    [-1.5, -1.5], (4, 4), relative_stages=True)
        rng = np.random.default_rng(66)
        for stable in (False, True):
            v, p = patch.state_from_stages(.7)
            r = rates(patch, v, p, dissipative=stable)
            np.testing.assert_allclose(r['volume_rate'], 0., atol=1e-13)
            np.testing.assert_allclose(r['momentum_rate'], 0., atol=1e-13)
            v, p = patch.state_from_stages(rng.uniform(.4, 1.8, patch.shape), rng.normal(size=(*patch.shape, 2)))
            r = rates(patch, v, p, dissipative=stable)
            self.assertLess(r['energy_identity_error'], 1e-10)
            self.assertLessEqual(r['energy_rate'], 1e-10)
            self.assertLess(abs(r['volume_rate'].sum()), 1e-12)

    def test_invalid_state_fails_without_mutation(self):
        section = TriangleFaceSection([[[0., 0.], [1., 1.]]], [0., 1.])
        with self.assertRaises(ValueError):
            pressure_secant_area(section, math.nan, 1.)
        with self.assertRaises(ValueError):
            face_flux(section, 1., [0., 0.], 1., [0., 0.], 2)
        patch = SubcellGeometryPatch(sampler(lambda x, y: x*0), [0., 0.], (1, 1))
        v, p = patch.state_from_stages(0.)
        p[0, 0, 0] = 1.
        with self.assertRaises(ValueError):
            rates(patch, v, p)
        self.assertEqual(p[0, 0, 0], 1.)


if __name__ == '__main__':
    unittest.main()
