"""Resolution diagnostics must preserve area and reject changed forcing."""
from pathlib import Path
import sys
import unittest
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tmp/south-fork-geospatial-deps'))
sys.path.insert(0, str(ROOT / 'physics/scripts'))
import numpy as np
from compare_south_fork_resolution import comparable, differences, restrict, temporal_envelope_gap
from raftsim.scenario2_5d import GridSpec2_5D


class ResolutionTests(unittest.TestCase):
    def test_temporal_envelope_distinguishes_phase_from_persistent_offset(self):
        mask = np.ones((1, 1), dtype=bool)
        c = np.array([[[1.]], [[1.2]]])
        overlap = temporal_envelope_gap(c, c[::-1], mask)
        self.assertEqual(overlap['gap_p50_p95_max_m'], [0., 0., 0.])
        lower = temporal_envelope_gap(c, c - .5, mask)
        self.assertEqual(lower['fraction_fine_entirely_lower_by_more_than_1cm'], 1.)
        np.testing.assert_allclose(lower['gap_p50_p95_max_m'], [.3, .3, .3])
        with self.assertRaises(ValueError): temporal_envelope_gap(c, c, ~mask)
        with self.assertRaises(ValueError): temporal_envelope_gap(c, np.full_like(c, np.nan), mask)

    def test_area_restriction_preserves_integral_and_spatial_axes(self):
        field = np.arange(24.).reshape(4, 6)
        coarse = restrict(field, 2)
        np.testing.assert_array_equal(coarse, [[3.5, 5.5, 7.5], [15.5, 17.5, 19.5]])
        self.assertEqual(coarse.sum(), field.sum() * .25)

    def test_restriction_rejects_invalid_shape_ratio_and_nonfinite(self):
        for field, ratio in ((np.ones((3, 4)), 2), (np.ones(4), 2),
                             (np.ones((4, 4)), 1), (np.ones((4, 4)), 2.5),
                             (np.full((4, 4), np.nan), 2)):
            with self.subTest(ratio=ratio, shape=field.shape):
                with self.assertRaises(ValueError): restrict(field, ratio)

    def test_mixed_wet_cells_are_not_full_wet(self):
        np.testing.assert_array_equal(restrict(np.array([[1., 0.], [1., 1.]]), 2) == 1, [[False]])

    def test_comparison_rejects_forcing_and_domain_changes(self):
        coarse = SimpleNamespace(grid=GridSpec2_5D(nx=2, ny=2, dx=1., dy=1., origin_x=0., origin_y=0.),
                                 fixed_dt=.1, roughness=.035, boundaries=())
        fine = SimpleNamespace(grid=GridSpec2_5D(nx=4, ny=4, dx=.5, dy=.5, origin_x=-.25, origin_y=-.25),
                               fixed_dt=.1, roughness=.035, boundaries=())
        registration = dict(geometry_sha256='g', solver_binary_sha256='s', boundary_mode='m', cfl=.2,
            target_discharge_m3s=45., origin_utm_m=[1., 2.], downstream_unit=[1., 0.], left_unit=[0., 1.],
            vertical_origin_navd88_m=220., inlet_stage_navd88_m=229., outlet_stage_navd88_m=226.)
        self.assertEqual(comparable(coarse, fine, registration, registration), 2)
        with self.assertRaises(ValueError):
            comparable(coarse,fine,registration,{**registration,'bed_sampling':'render_triangles'})
        for key in registration:
            with self.subTest(key=key):
                with self.assertRaises(ValueError):
                    comparable(coarse, fine, registration, {**registration, key: None})
        fine.grid = GridSpec2_5D(nx=4, ny=4, dx=.5, dy=.5, origin_x=0., origin_y=-.25)
        with self.assertRaises(ValueError): comparable(coarse, fine, registration, registration)

    def test_empty_and_nonfinite_metrics_fail_closed(self):
        for values in ([], [np.nan], [np.inf]):
            with self.assertRaises(ValueError): differences(values)


if __name__ == '__main__': unittest.main()
