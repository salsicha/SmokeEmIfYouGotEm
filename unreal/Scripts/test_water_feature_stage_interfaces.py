import unittest
import numpy as np
from water_feature_stage_interfaces import column_interface, stage_displacements


class StageInterfaceTests(unittest.TestCase):
    def fields(self, height=5.3):
        phi = np.broadcast_to(np.arange(12)[None,None,:]+.5-height, (8,9,12)).copy()
        return phi, np.full(phi.shape, 4, np.int32)

    def test_affine_zero_is_invariant_to_phi_scaling(self):
        phi, flags = self.fields()
        for scale in (.3,1.,7.):
            r = column_interface(phi*scale, flags, [3,4], .075)
            self.assertEqual(r['status'], 'supported')
            self.assertAlmostEqual(r['crossings'][0]['relative_height_m'], 5.3*.075, places=14)

    def test_absent_multiple_and_obstacle_roots_not_filled(self):
        phi, flags = self.fields()
        self.assertEqual(column_interface(abs(phi)+1, flags, [3,4], .075)['status'], 'absent')
        flags[3,4,4] = 2
        r = column_interface(phi, flags, [3,4], .075)
        self.assertEqual(r['status'], 'absent')
        self.assertEqual(r['obstacle_crossings'], 1)
        phi, flags = self.fields()
        phi[3,4,7],phi[3,4,8] = -1.,1.
        r = column_interface(phi, flags, [3,4], .075)
        self.assertEqual(r['status'], 'ambiguous')
        self.assertEqual(len(r['crossings']), 2)

    def test_measured_stages_are_not_retimed_or_projected(self):
        rows = [column_interface(*self.fields(h), [3,4], .075) for h in (5.3,5.4,5.5,5.5)]
        r = stage_displacements(rows)
        self.assertAlmostEqual(r['advection_vertical_displacement_m'], .0075)
        self.assertAlmostEqual(r['join_minus_advection_vertical_displacement_m'], .0075)
        self.assertEqual(r['final_minus_join_vertical_displacement_m'], 0.)
        rows[1]['status'] = 'absent'
        self.assertIsNone(stage_displacements(rows))

    def test_bad_geometry_flags_and_columns_fail(self):
        phi, flags = self.fields()
        for column, spacing in (([0,4],.075),([3.2,4],.075),([True,4],.075),([3,4],0)):
            with self.assertRaises(ValueError):
                column_interface(phi, flags, column, spacing)
        with self.assertRaises(ValueError):
            column_interface(phi, flags.astype(float), [3,4], .075)
        phi[0,0,0] = np.nan
        with self.assertRaises(ValueError):
            column_interface(phi, flags, [3,4], .075)


if __name__ == '__main__':
    unittest.main()
