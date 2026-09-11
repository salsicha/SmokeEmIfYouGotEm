import copy
import sys
import unittest
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from liquid_region_state import split_state
from liquid_region_geometry import boundaries, contact_page, ownership_table, FACES
from test_liquid_region_state import fixture


def inputs():
    w, s, p, a = fixture()
    regions, manifest = split_state(w, s, p, a, (4, 4))
    nx, ny, nz = s['domain']['physical_cells']
    offsets = [8, 8+ny, 8+2*ny, 8+2*ny+nx]
    n = 2*(nx+ny)
    packed = [[*a[0], 0], [*a[1], 0], [0, 0, 350], [500, 450, 800],
              [50, 75, 100/3], [nx, ny, nz], [nx+4, ny+4, nz], [700, 750, 800]]
    packed += np.arange(2*n*3).reshape(2*n, 3).tolist()
    parent = dict(schema='raftsim.liquid_grid_boundary.v3', domain=s['domain'],
                  packed_vectors=packed, vector_rows_offset=8+n, face_rows_offsets=offsets,
                  face_row_counts=[ny, ny, nx, nx], source_geometry_sha256='captured')
    return parent, manifest, regions


class RegionalGeometryTests(unittest.TestCase):
    def test_exterior_rows_preserved_once_shared_faces_have_no_forcing(self):
        parent, manifest, regions = inputs()
        original = copy.deepcopy((parent, manifest, regions))
        out = boundaries(parent, manifest, regions)
        used = []
        pairs = {}
        for region in out:
            self.assertNotIn('packed_vectors', region)  # Not a legacy tank profile.
            for face in region['faces']:
                if face['kind'] == 'external':
                    used += face['parent_rows']
                    np.testing.assert_array_equal(face['bed_stage_inward_speed_cm'],
                        np.asarray(parent['packed_vectors'])[face['parent_rows']])
                    vo = parent['vector_rows_offset']-8
                    np.testing.assert_array_equal(face['velocity_station_lateral_up_cm_per_s'],
                        np.asarray(parent['packed_vectors'])[np.asarray(face['parent_rows'])+vo])
                else:
                    self.assertNotIn('parent_rows', face)
                    self.assertNotIn('bed_stage_inward_speed_cm', face)
                    self.assertNotIn('velocity_station_lateral_up_cm_per_s', face)
                    pairs.setdefault(face['interface_id'], []).append((region['region_id'], face['neighbor_region']))
        self.assertEqual(sorted(used), list(range(8, parent['vector_rows_offset'])))
        for pair in pairs.values():
            self.assertEqual(len(pair), 2)
            self.assertEqual(pair[0], pair[1][::-1])
        self.assertEqual((parent, manifest, regions), original)

    def test_halos_cover_once_point_to_physical_owner_and_preserve_global_cell(self):
        p, m, regions = inputs(); out = boundaries(p, m, regions)
        by_id = {r['id']: r for r in regions}
        diagonal = 0
        for b in out:
            nx, ny, nz = b['physical_cells']
            expected = {(x, y) for y in range(ny+4) for x in range(nx+4)
                        if not (2 <= x < nx+2 and 2 <= y < ny+2)}
            seen = []
            lo = np.asarray(b['first_parent_cell_xy'])
            for x, y, owner, sx, sy in b['shared_halo_columns']:
                seen.append((x, y))
                source = by_id[owner]
                self.assertNotEqual(owner, b['region_id'])
                self.assertTrue(2 <= sx < source['physical_cells'][0]+2)
                self.assertTrue(2 <= sy < source['physical_cells'][1]+2)
                np.testing.assert_array_equal(lo+[x-2, y-2],
                    np.asarray(source['cell_bounds_xy'][0])+[sx-2, sy-2])
                diagonal += int((x < 2 or x >= nx+2) and (y < 2 or y >= ny+2))
            for x, y, px, py in b['external_halo_columns']:
                seen.append((x, y))
                np.testing.assert_array_equal(lo+[x, y], [px, py])
                parent_nx, parent_ny = m['domain']['physical_cells'][:2]
                self.assertFalse(2 <= px < parent_nx+2 and 2 <= py < parent_ny+2)
            self.assertEqual(len(seen), len(expected))
            self.assertEqual(set(seen), expected)
        self.assertGreater(diagonal, 0)

    def test_rejects_missing_duplicate_and_fake_reservoir_interfaces(self):
        for mutate in (lambda m: m['interfaces'].pop(),
                       lambda m: m['interfaces'].append(copy.deepcopy(m['interfaces'][0])),
                       lambda m: m['interfaces'][0].update(native_source_emission=True),
                       lambda m: m['interfaces'][0].update(parent_face_index=999),
                       lambda m: m['interfaces'][1].update(id=m['interfaces'][0]['id'])):
            p, m, r = inputs(); mutate(m)
            with self.assertRaisesRegex(ValueError, 'interface|reservoir'):
                boundaries(p, m, r)

    def test_rejects_wrong_parent_metrics_frame_and_coverage(self):
        p, m, r = inputs(); p['packed_vectors'][4][0] = 51
        with self.assertRaisesRegex(ValueError, 'metrics'): boundaries(p, m, r)
        p, m, r = inputs(); r[0]['canonical_frame'] = 'legacy-translated'
        with self.assertRaisesRegex(ValueError, 'frame'): boundaries(p, m, r)
        p, m, r = inputs()
        with self.assertRaisesRegex(ValueError, 'Missing'): ownership_table(m['domain'], r[:-1])
        r.append(copy.deepcopy(r[0])); r[-1]['id'] = 99
        with self.assertRaisesRegex(ValueError, 'Duplicate'): ownership_table(m['domain'], r)

    def test_contact_keeps_query_neighbors_and_rejects_missing_support(self):
        p, m, r = inputs()
        nc = nr = 60
        verts = []
        for row in range(nr):
            for col in range(nc):
                z = 100+col+row
                verts.extend([[0,0,z],[50,0,z+1],[0,-50,z+1],
                              [50,0,z+1],[50,-50,z+2],[0,-50,z+1]])
        profile = dict(schema='raftsim.registered_liquid_contact.v2',
            vertex_encoding='nominal-quad-local-xy-and-world-z-centimetres',
            source_geometry_sha256='captured', packed_vectors=[[-1500,1500,50],[50,nc,nr],*verts])
        page = contact_page(profile, r[0], m['domain']['cell_size_m'])
        self.assertTrue(page['prepared_query_bitwise_parity'])
        self.assertFalse(page['runtime_support_verified'])
        self.assertEqual(page['query_candidate_halo_quads'], 1)
        self.assertEqual(page['query_padding_cm'], 50.)
        with self.assertRaises(ValueError): contact_page(profile, r[0], m['domain']['cell_size_m'], 2000.)
        with self.assertRaises(ValueError): contact_page(profile, r[0], m['domain']['cell_size_m'], -1.)


if __name__ == '__main__': unittest.main()
