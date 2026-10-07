import unittest
import numpy as np

from build_pacuare_evidence_grid import project as reference
from project_nearest_route import project


class NearestRouteProjectionTests(unittest.TestCase):
    def compare(self, px, py, X, Y):
        X,Y,px,py = map(lambda a: np.asarray(a, dtype=float), (X,Y,px,py))
        S = np.arange(len(X), dtype=float)*4
        LX = np.cos(S); LY = np.sin(S)
        expected = reference(px,py,X,Y,S,LX,LY)
        actual = project(px,py,X,Y,S,LX,LY)
        for a,b in zip(actual,expected): np.testing.assert_array_equal(a,b)

    def test_curved_production_scale_coordinates(self):
        rng = np.random.default_rng(812)
        X = 442000+np.linspace(0,5000,1200)
        Y = 5750000+np.sin(X/200)*500
        self.compare(442000+rng.uniform(-400,5400,6000),
                     5750000+rng.uniform(-900,900,6000),X,Y)

    def test_ties_duplicates_and_near_ties_match_first_index(self):
        self.compare([0,1,1+1e-14,1-1e-14,0,100], [0,1,1,1,2,100],
                     [0,2,0,0,4],[0,0,0,4,4])
        self.compare([0,1,2,3,4],[1000000]*5,[0,2,4],[0,0,0])

    def test_empty_single_sample_and_multiple_query_blocks(self):
        self.compare([],[],[1],[2])
        self.compare([0,2],[0,3],[1],[2])
        self.compare(np.arange(66000),np.zeros(66000),[0,40000,70000],[0,0,0])

    def test_bad_shapes_and_nonfinite_inputs_refused(self):
        args = [np.array([0.,1.]) for _ in range(7)]
        for index in range(7):
            bad = list(args); bad[index] = np.array([0.,np.nan])
            with self.assertRaises(ValueError): project(*bad)
        with self.assertRaises(ValueError): project([],[],[],[],[],[],[])
        with self.assertRaises(ValueError): project([1],[],[1],[1],[1],[1],[1])


if __name__=='__main__': unittest.main()
