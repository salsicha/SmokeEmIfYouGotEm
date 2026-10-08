import unittest

import numpy as np

from chilko_corridor_bed import carve_mapped_water, inferred_depth_parameters, source_water_reference


class CorridorBedTests(unittest.TestCase):
    def test_regressed_stage_cannot_reclassify_source_water_or_emergent_bar(self):
        terrain = [100., 100.2, 100.3]
        for stage in (99.5, 100., 100.5):
            bed, inferred = carve_mapped_water(terrain, [1]*3, [True]*3,
                [stage]*3, [5.]*3, [10.]*3, [2.]*3, ownership_reference=[100.]*3)
            np.testing.assert_array_equal(bed, [stage-2., stage-2., 100.3])
            np.testing.assert_array_equal(inferred, [True, True, False])

    def test_local_source_water_reference_keeps_unregressed_features(self):
        raw = np.array([100., 100.2, np.nan, 100.1, 99.9])
        reference, gaps = source_water_reference(np.arange(5)*4., raw)
        np.testing.assert_array_equal(reference[[0, 1, 3, 4]], raw[[0, 1, 3, 4]])
        self.assertAlmostEqual(reference[2], 100.15)
        self.assertEqual(len(gaps), 1)
        self.assertTrue(np.isnan(raw[2]))
        with self.assertRaises(ValueError): source_water_reference([0, 4, 8], [np.nan, 100., 99.])
        with self.assertRaises(ValueError): source_water_reference([0, 24, 48], [100., np.nan, 99.9])

    def test_only_low_mapped_water_is_lowered(self):
        terrain = np.array([100., 100.2, 100.3, 99., 95.])
        bed, inferred = carve_mapped_water(terrain, [1, 1, 1, 2, 3],
            [True, True, True, False, True], [100.] * 5, [5.] * 5, [10.] * 5, [2.] * 5)
        np.testing.assert_array_equal(bed, [98., 98., 100.3, 99., 95.])
        np.testing.assert_array_equal(inferred, [True, True, False, False, False])
        np.testing.assert_array_equal(terrain, [100., 100.2, 100.3, 99., 95.])

    def test_no_reference_needed_on_unmapped_dry_ground(self):
        bed, inferred = carve_mapped_water([100.], [1], [False], [np.nan], [np.nan], [np.nan], [np.nan])
        self.assertEqual(bed[0], 100.); self.assertFalse(inferred[0])

    def test_integer_terrain_does_not_truncate_inferred_depth(self):
        bed, _ = carve_mapped_water([100], [1], [True], [100.], [5.], [10.], [1.25])
        self.assertEqual(bed[0], 98.75)

    def test_missing_source_and_bad_reference_refused(self):
        for terrain, kind, reference, width in [(np.nan, 0, 100., 10.), (100., 0, 100., 10.),
                (100., 1, np.nan, 10.), (100., 1, 100., 0.)]:
            with self.assertRaises(ValueError):
                carve_mapped_water([terrain], [kind], [True], [reference], [2.], [width], [1.])

    def test_same_coordinates_are_order_independent(self):
        terrain = np.array([100., 100.4, 99.]); mapped = np.array([True, True, False])
        whole = carve_mapped_water(terrain, [1, 1, 2], mapped, [100.] * 3, [2.] * 3, [10.] * 3, [1.] * 3)
        reverse = carve_mapped_water(terrain[::-1], [2, 1, 1], mapped[::-1], [100.] * 3, [2.] * 3, [10.] * 3, [1.] * 3)
        for a, b in zip(whole, reverse): np.testing.assert_array_equal(a, b[::-1])

    def test_initial_depth_has_discharge_and_width_sensitivity(self):
        s = np.arange(101) * 4.; z = 100. - .01 * s; width = np.full(101, 30.)
        low, slope = inferred_depth_parameters(s, z, width, 45., .045)
        high, _ = inferred_depth_parameters(s, z, width, 90., .045)
        narrow, _ = inferred_depth_parameters(s, z, width / 2, 45., .045)
        self.assertTrue(np.isfinite(low).all()); self.assertTrue((slope >= .001).all())
        self.assertTrue((high > low).all()); np.testing.assert_allclose(high, narrow)

    def test_bad_hydraulic_assumptions_refused(self):
        for s, z, w, q, n in [([0, 4, 8], [100, 101, 99], [10]*3, 45, .045),
                ([0, 0, 8], [100, 99, 98], [10]*3, 45, .045),
                ([0, 4, 8], [100, 99, 98], [10]*3, -1, .045),
                ([0, 4, 8], [100, 99, 98], [10]*3, 45, 0)]:
            with self.assertRaises(ValueError): inferred_depth_parameters(s, z, w, q, n)


if __name__ == '__main__': unittest.main()
