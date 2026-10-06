"""Run with Blender --background --python-exit-code 1 --python this_file."""
import math
from pathlib import Path
import sys
import unittest

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from audit_water_feature_pathlines import advance


class Field:
    def __init__(self, function):
        self.function = function

    def sample(self, position):
        return self.function(position)


class PathlineTests(unittest.TestCase):
    bounds = np.array([[2.45, .05, -.2], [3., .95, 1.1]])

    def track(self, point):
        return dict(positions_m=[point], stopped=None)

    def test_constant_velocity(self):
        field = Field(lambda p: np.array([.2, 0., 0.]))
        track = self.track([4., .2, .2])
        for frame in range(24):
            advance(track, field, field, frame, 24, 4, self.bounds)
        np.testing.assert_allclose(track['positions_m'][-1], [4.2, .2, .2], atol=1e-12)
        self.assertIsNone(track['stopped'])

    def test_linear_time_interpolation(self):
        track = self.track([4., .2, .2])
        advance(track, Field(lambda p: np.zeros(3)),
                Field(lambda p: np.array([.2, 0., 0.])), 0, 24, 4, self.bounds)
        np.testing.assert_allclose(track['positions_m'][-1], [4.+.1/24, .2, .2], atol=1e-12)

    def test_rotation_and_step_halving(self):
        field = Field(lambda p: np.array([-(p[1]-.2), p[0]-4., 0.]))
        errors = []
        exact = np.array([4.+.15*math.cos(1), .2+.15*math.sin(1), .2])
        for substeps in (4, 8):
            track = self.track([4.15, .2, .2])
            for frame in range(24):
                advance(track, field, field, frame, 24, substeps, self.bounds)
            self.assertIsNone(track['stopped'])
            errors.append(np.linalg.norm(np.array(track['positions_m'][-1])-exact))
        self.assertLess(errors[0], 3e-6)
        self.assertLess(errors[1], errors[0]/3.9)

    def test_missing_support_stops_without_projection(self):
        track = self.track([4., .2, .2])
        field = Field(lambda p: None)
        advance(track, field, field, 10, 24, 4, self.bounds)
        self.assertIn('support', track['stopped'])
        self.assertEqual(track['positions_m'], [[4., .2, .2]])

    def test_solid_entry_stops(self):
        track = self.track([3.01, .2, .2])
        field = Field(lambda p: np.array([-2., 0., 0.]))
        advance(track, field, field, 10, 24, 4, self.bounds)
        self.assertEqual(track['stopped'], 'entered authored solid')
        self.assertEqual(len(track['positions_m']), 1)


if __name__ == '__main__':
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(PathlineTests))
    if not result.wasSuccessful():
        raise RuntimeError('Pathline integrator tests failed')
