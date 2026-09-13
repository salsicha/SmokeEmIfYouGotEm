import sys
from pathlib import Path
import unittest
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from evaluate_liquid_density_correction import correction_scale,coincidence_counts
from solve_liquid_geometric_density import contact_clearance_targets


class CorrectionScaleTest(unittest.TestCase):
    def test_density_only_uses_common_step(self):
        self.assertEqual(correction_scale({'status':'converged'},2.),.25)
        self.assertEqual(correction_scale({'status':'converged'},0.),1.)

    def test_geometric_field_is_not_rescaled_even_if_failed(self):
        for converged in (False,True):
            self.assertEqual(correction_scale({'status':'geometric-reference',
                'geometric_density_converged':converged},.500001),1.)

    def test_bad_package_or_displacement_rejected(self):
        for value in (-1.,np.nan,np.inf):
            with self.assertRaises(ValueError):correction_scale({'status':'converged'},value)
        with self.assertRaises(ValueError):correction_scale({'status':'unrecognized'},1.)

    def test_contact_preserves_preexisting_skin_without_moving_bed(self):
        required,accepted=contact_clearance_targets([1.985,2.,3.],2.,.001)
        np.testing.assert_array_equal(required,[1.985,2.,2.001])
        np.testing.assert_array_equal(accepted,[1.985,2.,2.])
        with self.assertRaises(ValueError):contact_clearance_targets([-.001],2.,.001)

    def test_coincident_markers_are_counted_not_merged(self):
        p=np.array([[1.,2,3],[1,2,3],[1,2,3.0001],[4,5,6],[4,5,6]])
        old=p.copy();r=coincidence_counts(p)
        self.assertEqual(r,dict(unique_positions=3,exact_duplicate_groups=2,
            particles_in_duplicate_groups=4,maximum_coincident_count=2))
        np.testing.assert_array_equal(p,old)

    def test_empty_or_invalid_marker_sets(self):
        self.assertEqual(coincidence_counts(np.empty((0,3)))['maximum_coincident_count'],0)
        with self.assertRaises(ValueError):coincidence_counts([[0,1,np.nan]])


if __name__=='__main__':unittest.main()
