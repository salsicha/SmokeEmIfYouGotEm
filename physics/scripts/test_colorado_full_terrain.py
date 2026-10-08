import copy
import unittest
import numpy as np

from assemble_colorado_full_terrain import validate_selection, validate_seam, wet_coverage, route_end_caps


class FullTerrain(unittest.TestCase):
    def index(self):
        return dict(schema='raftsim.colorado_continuous_source_index.v1', route_length_m=2500.,
            windows=[dict(tile_id=f'colorado_continuous_{i:04d}', name=f'Colorado continuous {i:04d}',
                          source_core_interval_m=[lo, hi])
                     for i, (lo, hi) in enumerate(((0., 1200.), (1200., 2400.), (2400., 2500.)))])

    def test_full_route_cannot_skip_duplicate_or_drop_partial_terminal_core(self):
        rows = [dict(core=i, evidence=f'tile{i}') for i in range(3)]
        validate_selection(self.index(), rows)
        for bad in (rows[:-1], rows[1:], rows[::-1], [rows[0], rows[0], rows[2]],
                    [rows[0], dict(core=1, evidence='tile0'), rows[2]],
                    [dict(core=False, evidence='tile0'), *rows[1:]]):
            with self.assertRaises(ValueError): validate_selection(self.index(), bad)

    def test_seams_bound_to_exact_sources_origins_and_current_screen(self):
        sources = [dict(directory='a', manifest_sha256='ma', grid_sha256='ga'),
                   dict(directory='b', manifest_sha256='mb', grid_sha256='gb')]
        receipt = dict(schema='raftsim.colorado_continuous_bed_seam.v1', sources=sources,
            source_global_origins_m=[0., 900.], seam_global_station_m=1200., half_width_m=100.,
            bed_screen_passed=True, statistics=dict(shared_wet_cells=20,
                shoreline_disagreement_cells=0, bed_difference=dict(maximum_m=.01),
                reference_surface_difference=dict(maximum_m=.02)))
        validate_seam(receipt, *sources, [0., 900.], 1200.)
        mutations = [('half_width_m', 1.), ('source_global_origins_m', [0., 901.]),
                     ('seam_global_station_m', 1201.), ('bed_screen_passed', False),
                     ('sources', list(reversed(sources)))]
        for key, value in mutations:
            bad = copy.deepcopy(receipt); bad[key] = value
            with self.assertRaises(ValueError): validate_seam(bad, *sources, [0., 900.], 1200.)
        bad = copy.deepcopy(receipt)
        bad['statistics']['reference_surface_difference']['maximum_m'] = .11
        with self.assertRaises(ValueError): validate_seam(bad, *sources, [0., 900.], 1200.)

    def grid(self):
        return dict(classified_water_mask=np.array([[True, True, False], [True, True, True]]),
            station_m=np.array([[0., 1., 2.], [0., 1., 2.]]),
            bed_ellipsoid_m=np.full((2, 3), 300.), cell_m=np.array([1., 1.]),
            corner_east_north_m=np.array([100., 200.]))

    def test_actual_wet_cells_not_centreline_and_bounded_batches(self):
        class Terrain:
            def __init__(self): self.queries = []
            def sample(self, xy):
                self.queries.extend(xy.tolist())
                result = np.full(len(xy), 300.02)
                result[(xy[:, 0] == 101.5) & (xy[:, 1] == 198.5)] = np.nan
                return result
        terrain = Terrain()
        result = wet_coverage(self.grid(), dict(source_halo_interval_m=[100., 103.],
            source_core_interval_m=[100., 101.]), terrain, batch_size=2)
        self.assertEqual(result['classified_core_cells'], 4)
        self.assertEqual(result['missing_terrain_cells'], 1)
        self.assertEqual(result['missing_examples_epsg6404_m'], [[101.5, 198.5]])
        self.assertFalse(result['coverage_passed'])
        self.assertEqual(terrain.queries, [[100.5,199.5], [101.5,199.5], [100.5,198.5], [101.5,198.5]])

    def test_invalid_or_empty_water_coverage_cannot_pass(self):
        profile = dict(source_halo_interval_m=[0.,3.], source_core_interval_m=[0.,2.])
        for key, value in (('classified_water_mask', np.zeros((2,3), dtype=bool)),
                           ('station_m', np.full((2,3), np.nan)),
                           ('cell_m', [2.,2.]), ('corner_east_north_m', [np.inf,0.])):
            grid = self.grid(); grid[key] = value
            with self.assertRaises(ValueError): wet_coverage(grid, profile, None)

    def test_float32_terminal_station_does_not_create_outside_route_gaps(self):
        class Terrain:
            def sample(self, xy):
                return np.where(xy[:,0]>102.,np.nan,300.)
        halo=452097.91174945974
        end=453334.02824855957
        local=end-halo
        grid=self.grid(); grid['classified_water_mask'][:]=True
        grid['station_m']=np.array([[local-2,local-1,local]]*2,dtype=np.float32)
        before=grid['station_m'].copy()
        caps=route_end_caps(dict(horizontal_origin_epsg6404_m=[100.,198.],
            points=[[halo,0,0,0,1],[end,2,0,0,1]]))
        profile=dict(source_halo_interval_m=[halo,end],source_core_interval_m=[halo,end])
        result=wet_coverage(grid,profile,Terrain(),end_caps=caps)
        self.assertEqual(result['outside_route_endpoint_cells'],2)
        self.assertEqual(result['classified_core_cells'],4)
        self.assertTrue(result['coverage_passed'])
        np.testing.assert_array_equal(grid['station_m'],before)
        # A genuine later bend across the end plane must remain a missing cell.
        grid['station_m'][1,2]=local-1
        result=wet_coverage(grid,profile,Terrain(),end_caps=caps)
        self.assertEqual(result['outside_route_endpoint_cells'],1)
        self.assertEqual(result['classified_core_cells'],5)
        self.assertEqual(result['missing_terrain_cells'],1)
        self.assertFalse(result['coverage_passed'])

    def test_rounded_up_endpoint_keeps_cells_inside_geographic_boundary(self):
        class Terrain:
            def sample(self, xy): return np.full(len(xy),300.)
        halo=452097.91174945974;end=453334.02817
        local=end-halo
        self.assertGreater(float(np.float32(local)),local)
        grid=self.grid();grid['classified_water_mask'][:]=True
        grid['station_m']=np.full((2,3),local,dtype=np.float32)
        caps=route_end_caps(dict(horizontal_origin_epsg6404_m=[100.,198.],
            points=[[halo,0,0,0,1],[end,3,0,0,1]]))
        result=wet_coverage(grid,dict(source_halo_interval_m=[halo,end],
            source_core_interval_m=[halo,end]),Terrain(),end_caps=caps)
        self.assertEqual(result['outside_route_endpoint_cells'],0)
        self.assertEqual(result['classified_core_cells'],6)
        self.assertTrue(result['coverage_passed'])

    def test_endpoint_clamping_excludes_only_cells_beyond_run(self):
        class Terrain:
            def sample(self, xy): return np.full(len(xy), 300.)
        grid = self.grid()
        grid['station_m'] = np.array([[0.,0.,2.], [0.,1.,2.]])
        grid['classified_water_mask'][:] = True
        caps = route_end_caps(dict(horizontal_origin_epsg6404_m=[100.,198.],
            points=[[0,1,0,0,1], [2,2,0,0,1]]))
        result = wet_coverage(grid, dict(source_halo_interval_m=[0.,2.],
            source_core_interval_m=[0.,2.]), Terrain(), end_caps=caps)
        self.assertEqual(result['outside_route_endpoint_cells'], 4)
        self.assertEqual(result['classified_core_cells'], 2)
        self.assertTrue(result['coverage_passed'])
        # A later meander behind the start plane is not outside the run.
        grid['station_m'][1,0] = 1.
        result = wet_coverage(grid, dict(source_halo_interval_m=[0.,2.],
            source_core_interval_m=[0.,2.]), Terrain(), end_caps=caps)
        self.assertEqual(result['outside_route_endpoint_cells'], 3)
        self.assertEqual(result['classified_core_cells'], 3)


if __name__ == '__main__': unittest.main()
