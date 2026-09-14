import unittest
import numpy as np
from triangle_cell_storage import TriangleCellStorage, cell_triangles
from triangle_face_section import TriangleFaceSection
from subcell_drain_event import LowestWetDrain
from test_triangle_face_section import sampler, faces


class SubcellDrainEventTest(unittest.TestCase):
    def test_sloping_strip_exact_finite_extinction_and_semigroup(self):
        triangles = cell_triangles(sampler(lambda x, y: x+2), [-1.5, 0], [1, 1])
        storage = TriangleCellStorage(triangles)
        drain = LowestWetDrain(storage, [(2., faces(triangles)[0])])
        for depth in (1e-12, 1e-6, .1):
            np.testing.assert_allclose(drain.moments(depth), [depth*depth/2, depth, 2*depth], rtol=2e-15, atol=0)
            self.assertAlmostEqual(drain.extinction_time(depth), depth/2)
            remaining, sent = drain.drain(depth, depth/8)
            np.testing.assert_allclose(remaining, .5*(.75*depth)**2, rtol=1e-14, atol=0)
            rest, sent2 = drain.drain(.75*depth, depth/8)
            np.testing.assert_allclose(rest, drain.drain(depth, depth/4)[0], rtol=1e-14, atol=0)
            self.assertEqual(drain.drain(depth, depth)[0], 0.)
            self.assertEqual(drain.drain(depth, depth)[1], depth*depth/2)
            self.assertEqual(drain.drain(depth, 0), (depth*depth/2, 0.))
            np.testing.assert_allclose(rest+sent+sent2, depth*depth/2, rtol=1e-14, atol=0)

    def test_corner_wetting_and_mixed_face_polynomial(self):
        triangle = np.array([[[0., 0., 0.], [1., 0., 1.], [0., 1., 2.]]])
        storage = TriangleCellStorage(triangle)
        ramp = TriangleFaceSection([[[0., 0.], [1., 1.]]], [0, 1])
        drain = LowestWetDrain(storage, [(3., ramp)])
        # V=d^3/12, wet area=d^2/4, Q=3*d^2/2 => time=d/6.
        for d in (1e-9, .1, .5):
            np.testing.assert_allclose(drain.moments(d), [d**3/12, d*d/4, 1.5*d*d], rtol=2e-15)
            np.testing.assert_allclose(drain.extinction_time(d), d/6, rtol=2e-15)
        flat = TriangleFaceSection([[[0., 0.], [1., 0.]]], [0, 1])
        mixed = LowestWetDrain(storage, [(1., flat), (3., ramp)])
        nodes, weights = np.polynomial.legendre.leggauss(48)
        for d in (1e-12, 1e-6, .1, .5):
            x = .5*d*(nodes+1)
            expected = .5*d*np.sum(weights*(x/4)/(1+1.5*x))
            np.testing.assert_allclose(mixed.extinction_time(d), expected, rtol=2e-13, atol=0)

    def test_flat_cell_and_trapped_pool_do_not_invent_extinction(self):
        triangles = cell_triangles(sampler(lambda x, y: x*0), [0, 0], [1, 1])
        storage = TriangleCellStorage(triangles)
        flat = LowestWetDrain(storage, [(1., faces(triangles)[0])])
        self.assertTrue(np.isinf(flat.extinction_time(.1)))
        with self.assertRaisesRegex(ValueError, 'No finite'):
            flat.drain(.1, 1000.)
        raised = TriangleFaceSection([[[0., 1.], [1., 1.]]], [0, 1])
        trapped = LowestWetDrain(storage, [(1., raised)])
        self.assertEqual(trapped.moments(.5)[2], 0.)
        self.assertTrue(np.isinf(trapped.extinction_time(.5)))

    def test_interval_and_coefficient_guards(self):
        storage = TriangleCellStorage(np.array([[[0., 0., 0.], [1., 0., 1.], [0., 1., 2.]]]))
        face = TriangleFaceSection([[[0., 0.], [1., 1.]]], [0, 1])
        drain = LowestWetDrain(storage, [(1., face)])
        for d in (-1., 1.1, np.nan):
            with self.assertRaises(ValueError):
                drain.extinction_time(d)
        for weight in (-1., np.inf, np.nan):
            with self.assertRaises(ValueError):
                LowestWetDrain(storage, [(weight, face)])

    def test_exact_source_polynomial_matches_direct_integrals(self):
        nodes, weights = np.polynomial.legendre.leggauss(64)
        for height in (lambda x, y: x+2, lambda x, y: x+y+4,
                       lambda x, y: .2+x*x+y*y,
                       lambda x, y: 2+np.sin(2*x)*np.cos(3*y)):
            terrain = sampler(height)
            for center in ([0., 0.], [.137, -.219]):
                triangles = cell_triangles(terrain, center, [1, 1])
                storage = TriangleCellStorage(triangles)
                sections = list(zip((.2, .7, 1.1, .4), faces(triangles)))
                drain = LowestWetDrain(storage, sections)
                for fraction in (.1, .4, .9):
                    d = drain.ceiling*fraction
                    eta = drain.datum+d
                    direct = (*storage.volume_and_wet_area(eta),
                              sum(k*s.moments(eta)[0] for k, s in sections))
                    np.testing.assert_allclose(drain.moments(d), direct, rtol=2e-11, atol=1e-16)
                    time = drain.extinction_time(d)
                    if np.isfinite(time):
                        x = .5*d*(nodes+1)
                        integrand = []
                        for distance in x:
                            stage = drain.datum+distance
                            wet = storage.volume_and_wet_area(stage)[1]
                            flow = sum(k*s.moments(stage)[0] for k, s in sections)
                            integrand.append(wet/flow)
                        expected = .5*d*(weights@np.array(integrand))
                        np.testing.assert_allclose(time, expected, rtol=2e-10, atol=1e-14)


if __name__ == '__main__':
    unittest.main()
