import sys
import unittest
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from review_troublemaker_reference_coverage import metric_points


class ReferenceCoverageTests(unittest.TestCase):
    def test_rotated_metric_frame_and_roundtrip(self):
        origin = np.array([683805.13, 4296673.44])
        down = np.array([-.93, .36756]); down /= np.linalg.norm(down)
        left = np.array([-down[1], down[0]])
        local = np.array([[-10.5,-10.5],[10.5,-10.5],[10.5,10.5],[-10.5,10.5]])
        world = metric_points(local, origin, down, left)
        np.testing.assert_allclose((world-origin) @ np.column_stack([down,left]),local,atol=1e-9)
        np.testing.assert_allclose(world.mean(axis=0),origin,atol=1e-9)
        self.assertAlmostEqual(np.linalg.norm(world[1]-world[0]),21,places=8)

    def test_rebase_does_not_move_physical_footprint(self):
        origin=np.array([100,200]); down=np.array([0,1]); left=np.array([-1,0])
        local=np.array([[1,2],[3,4]]); shift=np.array([10,2])
        shifted_origin=metric_points(shift,origin,down,left)
        np.testing.assert_allclose(metric_points(local,origin,down,left),
                                   metric_points(local-shift,shifted_origin,down,left))

    def test_reject_non_metric_or_reflected_frames(self):
        for down,left in [([2,0],[0,1]),([1,0],[0,-1]),([float('nan'),0],[0,1])]:
            with self.assertRaises(ValueError): metric_points([[0,0]],[0,0],down,left)


if __name__ == '__main__': unittest.main()
