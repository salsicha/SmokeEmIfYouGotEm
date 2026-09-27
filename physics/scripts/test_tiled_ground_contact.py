import unittest
import hashlib
import json
from pathlib import Path
import tempfile
from unittest.mock import patch
import numpy as np

from audit_tiled_ground_contact import audit, compare, triangle_heights, world_vertices


def probe(ground=0., water=1., wet=True):
    return dict(x_cm=0., y_cm=0., ground_z_cm=ground, water_z_cm=water,
                ground_hit=True, support_available=True, support_wet=wet,
                raw_available=True, raw_wet=True)


class TiledGroundContactTests(unittest.TestCase):
    def test_hashed_manifest_integration_and_corruption(self):
        # Tiny generated fixture, never a production source edit.
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            mesh = root/'tile.npz'
            np.savez(mesh, xyz_local_m=np.array([[0., 0., 0.], [1., 0., 0.], [0., 1., 0.]]),
                     triangles=np.array([[0, 1, 2]]))
            tile = dict(name='tile', path='tile.npz', sha256=hashlib.sha256(mesh.read_bytes()).hexdigest(),
                        actor_translation_cm=[0, 0, 0], actor_scale=[1, -1, 1], origin_utm_m=[0, 0],
                        vertex_count=3, triangle_count=1)
            source = root/'source.json'
            source.write_text(json.dumps(dict(maximum_tile_width_m=1., tiles=[tile])))
            replacement = root/'replacement.json'
            replacement.write_text(json.dumps(dict(source_tile_manifest='source.json',
                source_tile_manifest_sha256=hashlib.sha256(source.read_bytes()).hexdigest(), tiles=[])))
            p = probe(); p['x_cm'], p['y_cm'] = 20., -20.
            capture = root/'capture.json'
            capture.write_text(json.dumps(dict(ground_contact_probes=[p])))
            with patch('audit_tiled_ground_contact.ROOT', root):
                result = audit(capture, [replacement])
                self.assertTrue(result['passed'])
                self.assertEqual(result['rows'][0]['source']['source_face'], 0)
                mesh.write_bytes(b'corrupted fixture')
                with self.assertRaisesRegex(ValueError, 'hash mismatch'):
                    audit(capture, [replacement])

    def test_diagonal_not_bilinear(self):
        vertices = np.array([[0., 0., 0.], [2., 0., 0.], [2., 2., 4.], [0., 2., 0.]])
        triangles = np.array([[0, 1, 2], [0, 2, 3]])
        z, faces = triangle_heights(vertices, triangles, np.array([[1., 1.], [1.5, .5], [.5, 1.5]]))
        np.testing.assert_array_equal(z, [2., 1., 1.])
        self.assertTrue((faces >= 0).all())

    def test_holes_and_outside_not_filled(self):
        v = np.array([[0., 0., 0.], [1., 0., 1.], [0., 1., 2.]])
        z, faces = triangle_heights(v, np.array([[0, 1, 2]]), np.array([[.75, .75], [-.1, .1]]))
        self.assertTrue(np.isnan(z).all())
        np.testing.assert_array_equal(faces, [-1, -1])

    def test_highest_and_reversed_winding(self):
        v = np.array([[0., 0., 0.], [1., 0., 0.], [0., 1., 0.],
                      [0., 0., 3.], [1., 0., 3.], [0., 1., 3.]])
        z, faces = triangle_heights(v, np.array([[0, 1, 2], [5, 4, 3]]), np.array([[.2, .2]]))
        np.testing.assert_array_equal(z, [3.])
        np.testing.assert_array_equal(faces, [1])

    def test_vertical_faces_not_ground(self):
        v = np.array([[0., 0., 0.], [1., 0., 0.], [1., 0., 3.]])
        z, _ = triangle_heights(v, np.array([[0, 1, 2]]), np.array([[.5, 0.]]))
        self.assertTrue(np.isnan(z[0]))

    def test_transform_float_and_reflection(self):
        local = np.array([[1.234567890123, 2.34567890123, -3.456789123]])
        got = world_vertices(local, [-700000.1234, -400000.5678, 0.], [1., -1., 1.])
        expected = (local*100).astype(np.float32).astype(float)*[1, -1, 1] + [-700000.1234, -400000.5678, 0]
        np.testing.assert_array_equal(got, expected)

    def test_invalid_triangles(self):
        v = np.zeros((3, 3))
        for tri in (np.array([[0., 1., 2.]]), np.array([[0, 1, 3]]), np.array([[0, 1, -1]])):
            with self.assertRaises(ValueError):
                triangle_heights(v, tri, np.zeros((1, 2)))

    def test_dry_occlusion_and_wet_clear_pass(self):
        result = compare([probe(), probe(ground=2., wet=False)], [0., 2.])
        self.assertTrue(result['passed'])
        self.assertEqual(result['source_buried'], 1)

    def test_missing_coverage_is_failure_not_survivor_pass(self):
        result = compare([probe(), probe()], [0., np.nan])
        self.assertFalse(result['passed'])
        self.assertEqual(result['uncovered'], 1)

    def test_covered_wrong_height_fails(self):
        self.assertFalse(compare([probe()], [.0021])['passed'])
        self.assertTrue(compare([probe()], [.0019])['passed'])

    def test_classification_near_surface_not_tolerance_relaxed(self):
        # Numerical height agreement does not excuse the wrong wet/dry state.
        self.assertFalse(compare([probe(ground=0., water=.0001)], [.0002])['passed'])
        self.assertFalse(compare([probe(wet=False)], [0.])['passed'])

    def test_invalid_and_missing_observations(self):
        for key, value in [('support_wet', 1), ('ground_z_cm', float('nan')), ('water_z_cm', True)]:
            p = probe(); p[key] = value
            with self.assertRaises(ValueError):
                compare([p], [0.])
        for key in ('ground_hit', 'support_available', 'raw_available', 'raw_wet'):
            p = probe(); p[key] = False
            self.assertFalse(compare([p], [0.])['passed'])


if __name__ == '__main__':
    unittest.main()
