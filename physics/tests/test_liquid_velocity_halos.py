import unittest
import numpy as np
from audit_liquid_velocity_halos import compare
from audit_liquid_native_interface import exchange_scalars


class VelocityHaloTest(unittest.TestCase):
    def fields(self):
        a = np.zeros((8, 8, 8, 4))
        b = np.ones((8, 8, 8, 4))*17
        return [a, b], [(0, 1, 2, 2, 0, 2), (1, 0, 5, 3, 7, 3)]

    def test_original_seam_fails(self):
        fields, columns = self.fields()
        self.assertFalse(compare(fields, columns)['exact_owner_halos'])
        self.assertEqual(compare(fields, columns)['max_velocity_error_cm_s'], 17)

    def test_copy_preserves_owners_and_exteriors(self):
        fields, columns = self.fields()
        copied = exchange_scalars(fields, columns)
        self.assertTrue(compare(copied, columns)['exact_owner_halos'])
        for before, after in zip(fields, copied):
            np.testing.assert_array_equal(before[:, 2:-2, 2:-2], after[:, 2:-2, 2:-2])
            np.testing.assert_array_equal(before[:, 0], after[:, 0])

    def test_no_tolerance_for_missing_copy(self):
        fields, columns = self.fields()
        copied = exchange_scalars(fields, columns)
        copied[1][3, 2, 0, 0] = np.nextafter(0., 1.)
        self.assertFalse(compare(copied, columns)['exact_owner_halos'])

    def test_auxiliary_and_nonfinite(self):
        fields, columns = self.fields()
        copied = exchange_scalars(fields, columns)
        copied[1][3, 2, 0, 3] = 1
        self.assertFalse(compare(copied, columns)['exact_owner_halos'])
        copied[1][3, 2, 0, 0] = np.nan
        with self.assertRaises(ValueError):
            compare(copied, columns)

    def test_invalid_map(self):
        fields, columns = self.fields()
        with self.assertRaises(ValueError):
            compare(fields, columns+columns)


if __name__ == '__main__':
    unittest.main()
