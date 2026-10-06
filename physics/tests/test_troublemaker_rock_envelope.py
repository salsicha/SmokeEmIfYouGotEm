"""Independent archived-envelope invariants; not visual/hydraulic acceptance.

These tests read the installed candidate and its preserved source. They do not
regenerate geometry, change assets, recook water, or infer survey accuracy.
Run directly with Python + numpy; pytest is not required.
"""
import hashlib
import json
from pathlib import Path
import unittest

import numpy as np


ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'physics/data/real_world/south_fork_american_chili_bar/reconstruction_2026_09/full_reach'
CANDIDATE = BASE / 'rock_envelope_20260926'


class InstalledEnvelopeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.receipt = json.loads((CANDIDATE / 'rock_envelope_build.json').read_text())
        cls.source_path = ROOT / cls.receipt['source_cap']
        cls.envelope_path = CANDIDATE / 'rock_envelope.npz'
        with np.load(cls.source_path, allow_pickle=False) as archive:
            cls.source = {key: archive[key] for key in archive.files}
        with np.load(cls.envelope_path, allow_pickle=False) as archive:
            cls.envelope = {key: archive[key] for key in archive.files}
        cls.n = len(cls.source['vertices_m'])

    def test_source_and_candidate_match_recorded_hashes(self):
        for path, digest in ((self.source_path, self.receipt['source_cap_sha256']),
                             (self.envelope_path, self.receipt['output_sha256'])):
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), digest)
        self.assertIs(self.receipt['faces_measured'], False)
        self.assertIs(self.receipt['captured_returns_modified'], False)

    def test_unchanged_topology_xy_and_internal_floor(self):
        before, after = self.source['solid_vertices_m'], self.envelope['solid_vertices_m']
        self.assertTrue(np.isfinite(after).all())
        np.testing.assert_array_equal(before[:, :2], after[:, :2])
        np.testing.assert_array_equal(before[self.n:], after[self.n:])
        for key in ('solid_triangles', 'solid_face_kind'):
            np.testing.assert_array_equal(self.source[key], self.envelope[key])
        delta = before[:self.n, 2] - after[:self.n, 2]
        self.assertTrue((delta >= -1e-12).all())
        np.testing.assert_allclose(delta, self.envelope['roof_lowered_m'], atol=1e-12, rtol=0)
        np.testing.assert_array_equal(before[:self.n, 2], self.envelope['roof_original_z_m'])
        self.assertEqual(int((delta > 1e-9).sum()), self.receipt['vertices_changed'])

    def test_closed_oriented_nondegenerate_solid(self):
        vertices = self.envelope['solid_vertices_m']
        faces = self.envelope['solid_triangles']
        self.assertTrue(((faces >= 0) & (faces < len(vertices))).all())
        twice_area = np.linalg.norm(np.cross(vertices[faces[:, 1]] - vertices[faces[:, 0]],
                                             vertices[faces[:, 2]] - vertices[faces[:, 0]]), axis=1)
        self.assertTrue((twice_area > 1e-10).all(), 'Degenerate collision triangles')
        edges = np.concatenate((faces[:, [0, 1]], faces[:, [1, 2]], faces[:, [2, 0]]))
        keys, inverse, counts = np.unique(np.sort(edges, axis=1), axis=0, return_inverse=True, return_counts=True)
        self.assertTrue((counts == 2).all(), 'Open or nonmanifold edge')
        balance = np.bincount(inverse, weights=np.where(edges[:, 0] < edges[:, 1], 1, -1), minlength=len(keys))
        self.assertTrue((balance == 0).all(), 'Inconsistent triangle winding')

    def test_changed_vertex_hydraulic_bounds(self):
        data = self.envelope
        changed = data['roof_lowered_m'] > 1e-9
        wet = data['roof_in_wet_cell'].astype(bool)
        z = data['solid_vertices_m'][:self.n, 2]
        bed = data['roof_cell_bed_m']
        self.assertTrue(np.isfinite(bed[changed & wet]).all())
        self.assertTrue((z[changed & wet] >= bed[changed & wet] - 1e-9).all())
        eta = data['roof_max_near_eta_m']
        constrained = changed & ~wet & data['roof_water_within_radius'].astype(bool)
        self.assertTrue(np.isfinite(eta[constrained]).all())
        self.assertTrue((z[constrained] - eta[constrained] >= self.receipt['water_margin_m'] - 1e-9).all())
        # This is only the recorded vertex constraint, not triangle-interior
        # clearance, continuous water-time coverage, or discharge invariance.

    def test_export_and_install_bind_the_same_envelope(self):
        export = json.loads((CANDIDATE / 'rock_envelope_export.json').read_text())
        install = json.loads((CANDIDATE / 'rock_envelope_install.json').read_text())
        digest = self.receipt['output_sha256']
        self.assertEqual(export['envelope_sha256'], digest)
        self.assertEqual(install['envelope_sha256'], digest)
        self.assertEqual(export['triangle_count'], len(self.envelope['solid_triangles']))
        self.assertEqual(install['triangle_count'], export['triangle_count'])
        self.assertIs(install['hydraulic_fields_changed'], False)
        self.assertIs(install['previous_mesh_unchanged'], True)
        self.assertIs(install['material_unchanged'], True)

    def test_current_game_asset_and_actor_match_install_receipt(self):
        install = json.loads((CANDIDATE / 'rock_envelope_install.json').read_text())
        for asset, expected in (
            (install['new_mesh'], install['new_mesh_sha256']),
            (install['previous_mesh'], install['previous_mesh_sha256']),
            (install['actor_package'], install['actor_package_sha256_after']),
        ):
            self.assertTrue(asset.startswith('/Game/'))
            path = ROOT / 'unreal/Content' / (asset.removeprefix('/Game/') + '.uasset')
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), expected,
                             f'Installed asset no longer matches envelope evidence: {asset}')


if __name__ == '__main__':
    unittest.main(verbosity=2)
