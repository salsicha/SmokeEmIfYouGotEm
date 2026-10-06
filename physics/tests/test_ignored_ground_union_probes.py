import unittest
import numpy as np
from prepare_ignored_ground_union_probes import observation_rows, envelope_union


class ObservationRowsTest(unittest.TestCase):
    def setUp(self):
        self.xyz = np.array([[100.,200.,3.], [102.,203.,4.]])
        self.rows = [dict(original_return_index=i, source_utm_navd88_m=p.tolist()) for i,p in enumerate(self.xyz)]

    def call(self, rows=None, heights=None, classes=None):
        return observation_rows(self.rows if rows is None else rows, self.xyz,
            [20,20] if classes is None else classes, [2.,5.] if heights is None else heights, [90.,190.], 1.)

    def test_signed_residual_and_reflected_engine_frame(self):
        result = self.call()
        self.assertEqual([r['observation_minus_union_m'] for r in result], [1.,-1.])
        self.assertEqual(result[0]['world_position_cm'], [1000.,-1000.,100.])
        np.testing.assert_array_equal(self.xyz, [[100.,200.,3.],[102.,203.,4.]])

    def test_duplicate_or_bad_index(self):
        for ids in ([0,0], [-1,1], [0,2], [0,.5]):
            rows = [dict(r, original_return_index=i) for r,i in zip(self.rows,ids)]
            with self.assertRaises(ValueError): self.call(rows=rows)

    def test_changed_coordinates_or_class(self):
        rows = [dict(self.rows[0], source_utm_navd88_m=[100.,200.,3.01]), self.rows[1]]
        with self.assertRaises(ValueError): self.call(rows=rows)
        with self.assertRaises(ValueError): self.call(classes=[20,2])

    def test_missing_or_nonfinite_height(self):
        for heights in ([2.], [2.,float('nan')], [2.,float('inf')]):
            with self.assertRaises(ValueError): self.call(heights=heights)

    def test_empty_queries_rejected(self):
        with self.assertRaises(ValueError): self.call(rows=[], heights=[])

    def test_envelope_replaces_old_roof_and_preserves_bed_outside(self):
        np.testing.assert_array_equal(envelope_union([2.,3.,4.], [2.5,np.nan,1.]), [2.5,3.,4.])

    def test_invalid_envelope_samples(self):
        for bed, roof in (([2.], [2.,3.]), ([np.nan], [2.]), ([2.], [np.inf])):
            with self.assertRaises(ValueError): envelope_union(bed, roof)
