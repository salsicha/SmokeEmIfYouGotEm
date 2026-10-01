import unittest
import numpy as np
from water_feature_geometry import world_coordinates


class GeometryTests(unittest.TestCase):
    def test_translation_preserves_distinct_native_float32_endpoints(self):
        native = np.array([[-2.25, 0., -.9750000238418579],
                           [-2.25, 0., -.9749999642372131]], np.float32)
        matrix = np.eye(4)
        matrix[2, 3] = 3.
        before = native.copy()
        result = world_coordinates(native, matrix)
        self.assertNotEqual(result[0, 2], result[1, 2])
        self.assertEqual(result[1, 2]-result[0, 2], float(native[1, 2])-float(native[0, 2]))
        self.assertEqual(np.float32(result[0, 2]), np.float32(result[1, 2]))
        np.testing.assert_array_equal(native, before)

    def test_rotation_scale_translation(self):
        matrix = np.array([[0, -2, 0, 3], [1, 0, 0, 4], [0, 0, .5, 5], [0, 0, 0, 1]], float)
        np.testing.assert_array_equal(world_coordinates([[1, 2, 3]], matrix), [[-1, 5, 6.5]])

    def test_invalid_affine_or_nonfinite_input_rejected(self):
        for points, matrix in [([[float('nan'), 0, 0]], np.eye(4)),
                               ([[0, 0]], np.eye(4)), ([[0, 0, 0]], np.eye(3)),
                               ([[0, 0, 0]], np.zeros((4, 4)))]:
            with self.assertRaises(ValueError):
                world_coordinates(points, matrix)


if __name__ == '__main__':
    unittest.main()
