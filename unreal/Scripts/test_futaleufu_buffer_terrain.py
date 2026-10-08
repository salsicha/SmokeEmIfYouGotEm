import unittest
import numpy as np
import shapely
from build_futaleufu_buffer_terrain import candidate_indices


class BufferTerrainTests(unittest.TestCase):
    def test_only_outer_buffer_neighborhoods_are_selected(self):
        lines=[shapely.LineString([(0,0),(4000,0)]),shapely.LineString([(4000,4000),(4000,0)]),
               shapely.LineString([(4000,0),(8000,0)])]
        result=candidate_indices(lines,[350,350,350],np.array([0.,0.]),100.)
        for index in ((0,0),(-2,-2),(40,39),(79,0)):self.assertIn(index,result)
        for index in ((20,0),(40,0),(60,0)):self.assertNotIn(index,result)

    def test_incomplete_short_or_nonfinite_buffers_refused(self):
        line=shapely.LineString([(0,0),(1000,0)])
        for lengths in ([300,300],[300,299,300],[300,np.nan,300]):
            with self.assertRaises(ValueError):candidate_indices([line]*3,lengths,np.array([0.,0.]),252.)


if __name__=='__main__':unittest.main()
