import unittest
import numpy as np
from triangle_cell_storage import cell_triangles, TriangleCellStorage
from triangle_face_section import TriangleFaceSection
from south_fork_registered_mesh import RegisteredMeshSampler


def sampler(height):
    x, y = np.meshgrid(np.arange(-2., 2.01, .5), np.arange(2., -2.01, -.5))
    rows, cols = x.shape
    root = (np.arange(rows*cols).reshape(rows, cols)[:-1, :-1]).ravel()
    return RegisteredMeshSampler(dict(east_m=x, north_m=y, z_m=height(x, y),
        nominal_east_axis_m=x[0], nominal_north_axis_m=y[:, 0],
        triangles=np.concatenate((np.stack((root, root+1, root+cols), 1),
                                  np.stack((root+1, root+cols+1, root+cols), 1)))))


def faces(triangles):
    return [TriangleFaceSection.from_cell(triangles, axis, sign*.5, [-.5, .5])
            for axis in (0, 1) for sign in (-1, 1)]


class TriangleFaceSectionTest(unittest.TestCase):
    def test_exact_ramp_face_moments(self):
        section = TriangleFaceSection([[[0, 0], [1, 2]]], [0, 1])
        for eta in (0., 1e-12, .2, .9, 1.7, 2.):
            actual = section.moments(eta)
            np.testing.assert_allclose(actual, [eta*eta/4, eta**3/6, eta/2], atol=0, rtol=2e-15)
        np.testing.assert_allclose(section.moments(3), [2, 13/3, 1], atol=1e-14)
        flat = TriangleFaceSection([[[0, 2], [1, 2]]], [0, 1])
        self.assertEqual(flat.moments(2), (0., 0., 0.))
        np.testing.assert_allclose(flat.moments(2.2), [.2, .04, 1], atol=1e-15)

    def test_moments_against_split_gauss_integration(self):
        rng = np.random.default_rng(938)
        nodes, weights = np.polynomial.legendre.leggauss(3)
        for _ in range(50):
            z = rng.normal(size=6)
            segments = [[[i*.2, z[i]], [(i+1)*.2, z[i+1]]] for i in range(5)]
            section = TriangleFaceSection(segments, [0, 1])
            for eta in np.linspace(min(z)-.1, max(z)+.1, 7):
                expected = np.zeros(3)
                for (x0, z0), (x1, z1) in segments:
                    points = [x0, x1]
                    if min(z0, z1) < eta < max(z0, z1):
                        points.append(x0+(x1-x0)*(eta-z0)/(z1-z0))
                    points.sort()
                    for a, b in zip(points, points[1:]):
                        x = (a+b)/2+(b-a)*nodes/2
                        depth = np.maximum(eta-(z0+(z1-z0)*(x-x0)/(x1-x0)), 0)
                        expected += (b-a)/2*np.array([weights@depth, weights@(depth*depth), weights@(depth > 0)])
                np.testing.assert_allclose(section.moments(eta), expected, atol=5e-14, rtol=2e-13)

    def test_independent_bed_force_cancels_face_pressure_at_rest(self):
        for height in (lambda x, y: 2*x+y+3, lambda x, y: .2+x*x+2*y*y,
                       lambda x, y: .3+np.sin(2*x)*np.cos(3*y)):
            terrain = sampler(height)
            for center in ([0., 0.], [.137, -.219]):
                triangles = cell_triangles(terrain, center, [1, 1])
                storage, boundary = TriangleCellStorage(triangles), faces(triangles)
                for eta in (0., .2, .6, 1., 2., 5.):
                    force = storage.hydrostatic_bed_force(eta)
                    pressure = np.array([.5*9.81*face.moments(eta)[1] for face in boundary])
                    outward = np.array([pressure[1]-pressure[0], pressure[3]-pressure[2]])
                    np.testing.assert_allclose(force, outward, atol=2e-12, rtol=2e-13)

    def test_adjacent_cells_have_the_same_face_not_just_mean_bed(self):
        terrain = sampler(lambda x, y: np.sin(x*3)*np.cos(y*2)+2.)
        for axis in (0, 1):
            first, second = np.array([-.31, -.23]), np.array([-.31, -.23])
            second[axis] += 1
            a = faces(cell_triangles(terrain, first, [1, 1]))[axis*2+1]
            b = faces(cell_triangles(terrain, second, [1, 1]))[axis*2]
            a.verify_shared(b)
            for eta in (.1, 1.2, 2., 3.2):
                np.testing.assert_allclose(a.moments(eta), b.moments(eta), atol=2e-14)

    def test_flat_face_reproduces_pointwise_rusanov(self):
        section = TriangleFaceSection([[[0, .3], [2, .3]]], [0, 2])
        left, right = np.array([1.2, -.4]), np.array([-.2, .7])
        for axis in (0, 1):
            actual, speed = section.flux(1.3, left, 2.3, right, axis)
            hl, hr = 1., 2.
            expected = .5*(np.r_[hl*left[axis], hl*left[axis]*left]
                           +np.r_[hr*right[axis], hr*right[axis]*right])
            expected[axis+1] += .25*9.81*(hl*hl+hr*hr)
            expected -= .5*speed*(np.r_[hr, hr*right]-np.r_[hl, hl*left])
            np.testing.assert_allclose(actual, 2*expected, atol=1e-14)

    def test_rest_dry_and_flow_reversal(self):
        section = TriangleFaceSection([[[-.5, 2], [0, 0]], [[0, 0], [.5, 1]]], [-.5, .5])
        for eta in (-1., 0., .5, 2.):
            actual, _ = section.flux(eta, [0, 0], eta, [0, 0], 0)
            self.assertEqual(actual[0], 0)
            np.testing.assert_allclose(actual[1:], [.5*9.81*section.moments(eta)[1], 0], atol=0)
        a, _ = section.flux(.7, [1, .2], 1.5, [-.3, -.4], 0)
        b, _ = section.flux(1.5, [.3, .4], .7, [-1, -.2], 0)
        np.testing.assert_allclose(a, b*[-1, 1, 1], atol=1e-14)
        dry, _ = section.flux(0., [0, 0], 1.5, [-.3, -.4], 0)
        self.assertLessEqual(dry[0], 0)  # Exactly dry left cell cannot donate.

    def test_missing_overlap_and_unshared_geometry_fail(self):
        for segments in ([[[0, 0], [.4, 0]], [[.5, 0], [1, 0]]],
                         [[[0, 0], [.7, 0]], [[.5, 0], [1, 0]]],
                         [[[0, 0], [.5, 0]], [[.5, .1], [1, 0]]]):
            with self.assertRaises(ValueError):
                TriangleFaceSection(segments, [0, 1])
        a = TriangleFaceSection([[[0, 0], [1, 0]]], [0, 1])
        b = TriangleFaceSection([[[0, .1], [1, .1]]], [0, 1])
        with self.assertRaises(ValueError):
            a.verify_shared(b)
        for x in (-.1, 1.1, np.nan):
            with self.assertRaises(ValueError):
                a.bed_at(x)

    def test_base_flux_has_nonpositive_mechanical_entropy_production(self):
        rng = np.random.default_rng(748)
        section = TriangleFaceSection([[[-.5, 2], [0, 0]], [[0, 0], [.5, 1]]], [-.5, .5])
        maximum = -np.inf
        for _ in range(500):
            el, er = rng.uniform(-.1, 3., 2)
            ul, ur = rng.normal(size=(2, 2))*2
            if el <= 0: ul[:] = 0
            if er <= 0: ur[:] = 0
            for axis in (0, 1):
                flux, _ = section.flux(el, ul, er, ur, axis)
                vl, vr = np.r_[9.81*el-.5*(ul@ul), ul], np.r_[9.81*er-.5*(ur@ur), ur]
                pl, pr = .5*9.81*section.moments(el)[1], .5*9.81*section.moments(er)[1]
                rate = (vr-vl)@flux-(ur[axis]*pr-ul[axis]*pl)
                maximum = max(maximum, rate)
                self.assertLessEqual(rate, 2e-12)
        self.assertLess(maximum, 0.)


if __name__ == '__main__':
    unittest.main()
