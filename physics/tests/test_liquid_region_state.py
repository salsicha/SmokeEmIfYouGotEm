import copy
import sys
import unittest
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from liquid_region_state import partition, owners, split_state


def fixture():
    domain = dict(physical_cells=[10, 6, 24], cell_size_m=[.5, .75, 1/3],
        native_face_bounds_m=[[-2.5, -2.25], [2.5, 2.25]], centre_station_lateral_m=[0, 0],
        physical_extents_m=[5, 4.5, 8], nominal_particle_volume_m3=.5*.75/3/4)
    rotation = np.array([[.8, -.6], [.6, .8]])
    x, y = np.meshgrid(np.arange(10)*.5-2.25, np.arange(6)*.75-1.875)
    points = np.c_[np.c_[x.ravel(), y.ravel()]@rotation.T*100, np.full(60, 500.)]
    source_positions = np.c_[np.array([[-2.49, 0], [2.49, 0]])@rotation.T*100, [150, 150]]
    volume = domain['nominal_particle_volume_m3']
    window = dict(source_geometry_sha256='captured', solid_sha256='solid', local_origin_engine_cm=[0, 0, 350])
    source = dict(schema='raftsim.native_face_liquid_source.v2', domain=domain,
        source_geometry_sha256='captured', solid_sha256='solid',
        nominal_particle_volume_m3=volume, positions_world_offset_cm=source_positions.tolist(),
        velocities_world_cm_per_s=[[80, 60, 0], [-80, -60, 0]], weights_m3_per_s=[2., 3.],
        total_inflow_m3_per_s=5., requested_spawn_particles_per_second=5/volume)
    initial = dict(schema='raftsim.registered_liquid_initial_state.v2', domain=domain,
        source_geometry_sha256='captured', nominal_particle_volume_m3=volume,
        positions_world_cm=points.tolist(), velocities_world_cm_per_s=np.arange(180).reshape(60, 3).tolist(), particle_count=60)
    return window, source, initial, rotation.T.tolist()


class LiquidRegionStateTests(unittest.TestCase):
    def test_exact_identity_position_velocity_and_source_conservation(self):
        w, s, p, a = fixture()
        originals = copy.deepcopy((w, s, p, a))
        bundles, report = split_state(w, s, p, a, (4, 4))
        seed_ids = np.concatenate([b['seed_parent_ids'] for b in bundles])
        source_ids = np.concatenate([b['source_parent_ids'] for b in bundles]).astype(int)
        np.testing.assert_array_equal(np.sort(seed_ids), np.arange(60))
        np.testing.assert_array_equal(np.sort(source_ids), np.arange(2))
        for b in bundles:
            ids = b['seed_parent_ids']
            np.testing.assert_array_equal(b['positions_canonical_cm'], np.asarray(p['positions_world_cm'])[ids])
            np.testing.assert_array_equal(b['velocities_canonical_cm_per_s'], np.asarray(p['velocities_world_cm_per_s'])[ids])
            self.assertFalse(b['internal_source_emission'])
        self.assertAlmostEqual(sum(b['external_inflow_m3_per_s'] for b in bundles), 5.)
        self.assertAlmostEqual(sum(b['external_spawn_particles_per_second'] for b in bundles), s['requested_spawn_particles_per_second'])
        self.assertEqual((w, s, p, a), originals)
        self.assertFalse(report['runtime_coupling_verified'])

    def test_full_rapid_keeps_last_two_cell_group_and_all_coverage(self):
        domain = dict(physical_cells=[490, 162, 24], cell_size_m=[.5, .5, 1/3],
            native_face_bounds_m=[[-112.5, -40.5], [132.5, 40.5]])
        regions, interfaces = partition(domain)
        cover = np.zeros((162, 490), dtype=int)
        for r in regions:
            (x0, y0), (x1, y1) = r['cell_bounds_xy']
            cover[y0:y1, x0:x1] += 1
            self.assertLessEqual(np.prod(r['computational_cells'])*8, 2000000)
        np.testing.assert_array_equal(cover, 1)
        self.assertEqual(len(regions), 12)
        self.assertEqual(regions[-1]['computational_cells'], [110, 38, 24])
        self.assertEqual(len(interfaces), 17)
        self.assertEqual(len({(f['lower_region'], f['upper_region']) for f in interfaces}), 17)
        self.assertTrue(all(not f['native_source_emission'] for f in interfaces))

    def test_half_open_shared_faces_corners_and_outer_faces(self):
        w, s, p, a = fixture()
        regions, _ = partition(s['domain'], (4, 4))
        points = [[-2.5, -2.25], [-.5, 0], [1.5, .75], [2.5, 2.25]]
        np.testing.assert_array_equal(owners(points, regions), [0, 1, 5, 5])
        # A moving identity can cross several regions without being re-seeded;
        # classification concerns its NEW position, not its previous owner.
        np.testing.assert_array_equal(owners([[-2, 0], [2, 0]], regions), [0, 2])
        with self.assertRaisesRegex(ValueError, 'outside'):
            owners([[2.5000001, 0]], regions)
        with self.assertRaisesRegex(ValueError, 'duplicates'):
            owners([[0, 0]], regions+[regions[1]])

    def test_rejects_inconsistent_frame_volume_and_flow(self):
        for mutate in (lambda w, s, p: w.update(local_origin_engine_cm=[100, 0, 350]),
                       lambda w, s, p: p.update(nominal_particle_volume_m3=1.),
                       lambda w, s, p: s.update(total_inflow_m3_per_s=6.),
                       lambda w, s, p: s.update(requested_spawn_particles_per_second=100.),
                       lambda w, s, p: p.update(particle_count=59)):
            w, s, p, a = fixture(); mutate(w, s, p)
            with self.assertRaises(ValueError):
                split_state(w, s, p, a, (4, 4))
        w, s, p, a = fixture()
        with self.assertRaisesRegex(ValueError, 'right-handed'):
            split_state(w, s, p, [[1, 0], [0, -1]])

    def test_capacity_and_odd_x_never_truncate(self):
        w, s, p, a = fixture()
        with self.assertRaisesRegex(ValueError, 'even X'):
            partition(s['domain'], (3, 4))
        huge = dict(physical_cells=[490, 162, 24], cell_size_m=[.5, .5, 1/3],
            native_face_bounds_m=[[-112.5, -40.5], [132.5, 40.5]])
        with self.assertRaisesRegex(ValueError, 'cap'):
            partition(huge, (490, 162))
        p['positions_world_cm'] = [p['positions_world_cm'][0]]*163841
        p['velocities_world_cm_per_s'] = [[0, 0, 0]]*163841
        p['particle_count'] = 163841
        with self.assertRaisesRegex(ValueError, 'burst capacity'):
            split_state(w, s, p, a, (4, 4))

    def test_single_last_y_row_merges_without_loss(self):
        domain = dict(physical_cells=[8, 5, 4], cell_size_m=[1, 1, 1], native_face_bounds_m=[[0, 0], [8, 5]])
        regions, _ = partition(domain, (4, 4))
        self.assertEqual([r['physical_cells'] for r in regions], [[4, 5, 4], [4, 5, 4]])

    def test_consistently_wrong_particle_volume_still_rejected(self):
        w, s, p, a = fixture()
        s['domain']['nominal_particle_volume_m3'] = 1.
        s['nominal_particle_volume_m3'] = p['nominal_particle_volume_m3'] = 1.
        s['requested_spawn_particles_per_second'] = 5.
        with self.assertRaisesRegex(ValueError, 'cell metric'):
            split_state(w, s, p, a)


if __name__ == '__main__':
    unittest.main()
