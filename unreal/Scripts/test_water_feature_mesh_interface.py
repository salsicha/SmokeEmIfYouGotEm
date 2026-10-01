import unittest
import numpy as np

from water_feature_mesh_interface import MeshInterface, closest_triangle, brute_nearest, RenderMeshMacField
import test_water_feature_surface_mac as surface_mac_tests


def cube():
    vertices = np.array([(x, y, z) for x in (-1., 1.) for y in (-1., 1.) for z in (-1., 1.)])
    faces = []
    for axis in range(3):
        for side in (-1, 1):
            ids = np.flatnonzero(vertices[:, axis] == side)
            # Ordered in the face's remaining coordinate axes, not hand-coded
            # outward triangle signs; correct each triangle by its face center.
            for tri in ((ids[0], ids[1], ids[3]), (ids[0], ids[3], ids[2])):
                tri = list(tri)
                xyz = vertices[tri]
                if np.cross(xyz[1]-xyz[0], xyz[2]-xyz[0]) @ xyz.mean(axis=0) < 0:
                    tri[1], tri[2] = tri[2], tri[1]
                faces.append(tri)
    return vertices, np.array(faces)


def model(vertices, triangles, maximum=2):
    return MeshInterface(vertices, triangles, lambda p: brute_nearest(vertices, triangles, p), maximum_distance=maximum)


class MeshInterfaceTests(unittest.TestCase):
    def test_independent_triangle_closest_regions(self):
        tri = np.array([[0., 0., 0.], [1., 0., 0.], [0., 1., 0.]])
        for p, q in [([.2, .3, .4], [.2, .3, 0]), ([.6, .6, 0], [.5, .5, 0]),
                     ([-.1, -.2, .1], [0, 0, 0]), ([2, -.1, .2], [1, 0, 0])]:
            np.testing.assert_allclose(closest_triangle(p, tri), q, atol=1e-14)

    def test_cube_face_edge_vertex_sign_and_distance(self):
        interface = model(*cube())
        for p, exact in [([.1, .2, 1.2], .2), ([.1, .2, .8], -.2),
                         ([1.1, 1.2, .3], np.hypot(.1, .2)),
                         ([1.1, 1.2, 1.3], np.linalg.norm([.1, .2, .3]))]:
            sample = interface.sample(p)
            self.assertAlmostEqual(sample['phi_m'], exact, places=14)
            self.assertAlmostEqual(np.linalg.norm(sample['gradient']), 1, places=14)

    def test_distance_gradient_by_independent_difference(self):
        interface = model(*cube())
        for point in ([.1, .2, .8], [1.1, 1.2, .3], [1.1, 1.2, 1.3]):
            p = np.array(point)
            numerical = []
            for axis in range(3):
                step = np.eye(3)[axis]*1e-6
                numerical.append((interface.sample(p+step)['phi_m']-interface.sample(p-step)['phi_m'])/2e-6)
            np.testing.assert_allclose(interface.sample(p)['gradient'], numerical, atol=1e-9)

    def test_exact_surface_and_undefined_crease_normal(self):
        interface = model(*cube())
        value, normal = interface.surface([.1, .2, 1])
        self.assertAlmostEqual(value, 0, places=14)
        np.testing.assert_allclose(normal, [0, 0, 1])
        np.testing.assert_allclose(interface.surface([0, 0, 1])[1], [0, 0, 1])
        self.assertEqual(interface.sample([1, 1, .3])['feature'], 'edge')
        self.assertIsNone(interface.surface([1, 1, .3]))
        self.assertIsNone(interface.surface([1, 1, 1]))

    def test_input_geometry_is_not_edited_or_aliased(self):
        vertices, triangles = cube()
        original = vertices.copy()
        interface = model(vertices, triangles)
        np.testing.assert_array_equal(vertices, original)
        self.assertFalse(interface.vertices.flags.writeable)
        self.assertFalse(interface.triangles.flags.writeable)

    def test_open_inverted_and_bowtie_geometry_rejected(self):
        vertices, triangles = cube()
        with self.assertRaises(ValueError):
            model(vertices, triangles[:-1])
        with self.assertRaises(ValueError):
            model(vertices, triangles[:, [0, 2, 1]])
        other = vertices+np.array([2., 2., 2.])
        # Two closed cubes touching only at one shared vertex have disconnected
        # vertex links, although each undirected edge still has two faces.
        merged = np.concatenate((vertices, other[1:]))
        remap = np.array([7]+list(range(8, 15)))
        with self.assertRaisesRegex(ValueError, 'Disconnected vertex'):
            model(merged, np.concatenate((triangles, remap[triangles])))

    def test_bounds_contact_and_invalid_queries_rejected(self):
        vertices, triangles = cube()
        interface = model(vertices, triangles, maximum=.01)
        self.assertIsNone(interface.surface([.1, .2, 1.02]))
        interface.allowed[:] = False
        self.assertIsNone(interface.surface([.1, .2, 1]))
        with self.assertRaises(ValueError):
            interface.surface([np.nan, 0, 0])

    def test_retessellation_preserves_edge_vertex_sign(self):
        vertices, triangles = cube()
        subdivided_vertices, subdivided_triangles = vertices.tolist(), []
        for ids in triangles:
            center = len(subdivided_vertices)
            subdivided_vertices.append(vertices[ids].mean(axis=0).tolist())
            subdivided_triangles.extend([[int(ids[i]), int(ids[(i+1)%3]), center] for i in range(3)])
        a, b = model(vertices, triangles), model(np.array(subdivided_vertices), np.array(subdivided_triangles))
        for point in ([1.1, 1.2, .3], [1.1, 1.2, 1.3], [.1, .2, .8]):
            self.assertAlmostEqual(a.sample(point)['phi_m'], b.sample(point)['phi_m'], places=14)

    def test_concave_prism_nearest_reentrant_edge(self):
        polygon = np.array([[0., 0.], [2., 0.], [2., 1.], [1., 1.], [1., 2.], [0., 2.]])
        vertices = np.concatenate([np.column_stack((polygon, np.full(6, z))) for z in (-1., 1.)])
        caps = np.array([[0, 1, 2], [0, 2, 3], [0, 3, 5], [3, 4, 5]])
        triangles = list(caps[:, [0, 2, 1]])+list(caps+6)
        for i in range(6):
            j = (i+1)%6
            triangles.extend([[i, j, j+6], [i, j+6, i+6]])
        interface = model(vertices, np.array(triangles))
        self.assertAlmostEqual(interface.volume, 6, places=14)
        for point, exact in [([.5, .5, 0], -.5), ([1.2, 1.3, 0], .2),
                             ([.9, .9, 0], -np.sqrt(.02))]:
            self.assertAlmostEqual(interface.sample(point)['phi_m'], exact, places=14)
        self.assertEqual(interface.sample([.9, .9, 0])['feature'], 'edge')

    def test_mesh_mac_uses_distinct_explicit_interface(self):
        field, p, function = surface_mac_tests.SurfaceMacTests().field()
        vertices, triangles = cube()
        vertices = vertices*.08+(p-np.array([0., 0., .07]))
        interface = model(vertices, triangles)
        query = p+np.array([0., 0., .01])
        self.assertIsNone(field.sample(query))
        shared = RenderMeshMacField(field.interior.phi, field.interior.solid, field.interior.velocity,
            field.interior.origin, field.interior.spacing, 2., interface=interface)
        value, report = shared.sample(query)
        np.testing.assert_allclose(value, [function(query, a) for a in range(3)], atol=1e-12)
        self.assertAlmostEqual(report['native_base_phi_m'], .01, places=14)
        self.assertFalse(report['accepted'])
        with self.assertRaises(ValueError):
            shared.manifold_surface([query], .01)


if __name__ == '__main__':
    unittest.main()
