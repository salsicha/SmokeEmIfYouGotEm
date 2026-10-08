import unittest
from types import SimpleNamespace
import numpy as np
import shapely
from build_futaleufu_continuous_water_domain import cell_centres, initial_fields, connected_tiles, labels_at, observe_branches, NAMES


class ContinuousWaterDomainTests(unittest.TestCase):
    def test_centres_northward_negative_indices_and_no_shared_cells(self):
        a = cell_centres((-1,-1), [1000,2000], span=4, spacing=2)
        np.testing.assert_array_equal(a, [[[997,1997],[999,1997]],[[997,1999],[999,1999]]])
        b = cell_centres((0,-1), [1000,2000], span=4, spacing=2)
        self.assertEqual(b[0,0,0]-a[0,-1,0], 2.)
        fine = cell_centres((-1,-1), [1000,2000], span=4, spacing=1)
        self.assertEqual(fine.shape,(4,4,2))
        np.testing.assert_array_equal(fine[0,0], [996.5,1996.5])

    def test_missing_or_nonfinite_terrain_refused(self):
        with self.assertRaises(ValueError): initial_fields([np.nan], [2.], np.array([True]))
        with self.assertRaises(ValueError): initial_fields([1.], [2.], np.array([1]))
        with self.assertRaises(ValueError): initial_fields([1.,2.], [2.], np.array([True]))

    def test_dry_banks_not_excavated_and_no_unowned_water(self):
        h, wet = initial_fields([0.,3.,0.,1.], [2.,2.,2.,1.04], np.array([True,True,False,True]))
        np.testing.assert_allclose(h, [2.,0.,0.,.04])
        np.testing.assert_array_equal(wet, [True,False,False,False])

    def test_face_connection_across_both_seams(self):
        a = np.ones((2,2), bool)
        labels, offset, counts = connected_tiles({(-1,-1):a,(0,-1):a,(-1,0):a})
        self.assertEqual(len(counts)-1,1)
        self.assertEqual(counts[1],12)
        np.testing.assert_array_equal(offset, [-2,-2])

    def test_diagonal_and_missing_tiles_do_not_connect(self):
        a = np.eye(2, dtype=bool)
        labels, offset, counts = connected_tiles({(0,0):a,(1,1):a,(3,3):a})
        self.assertEqual(len(counts)-1,6)

    def test_coordinate_lookup_does_not_clamp_or_reverse_north(self):
        components = np.array([[1,2],[3,4]])
        values = labels_at([[997,1997],[999,1999],[996,1996],[1000,2000],[995.9,1998]],
            components, np.array([-2,-2]), [1000,2000], 2.)
        np.testing.assert_array_equal(values, [1,4,1,0,0])
        with self.assertRaises(ValueError): labels_at([[np.inf,0]],components,[0,0],[0,0],2.)

    def test_sparse_domain_allocation_is_bounded(self):
        a = np.ones((2,2),bool)
        with self.assertRaises(ValueError): connected_tiles({(0,0):a,(100000,100000):a})

    def test_route_check_requires_one_component_for_every_arm_and_section(self):
        lines = [shapely.LineString(p) for p in (
            [(10,70),(10,10)], [(70,10),(10,10)], [(10,10),(70,70)])]
        arrays = {name:dict(station_m=[0,line.length], left_m=[-2,-2], right_m=[2,2])
                  for name,line in zip(NAMES,lines)}
        bed = SimpleNamespace(lines=lines, arrays=arrays)
        components = np.ones((80,80), np.int32)
        rows, common = observe_branches(bed, components, [0,0], [0,0], 1.)
        self.assertEqual(common,[1])
        self.assertEqual({r['branch'] for r in rows},set(NAMES))
        components[30:41,:] = 0
        rows, common = observe_branches(bed, components, [0,0], [0,0], 1.)
        self.assertEqual(common,[])
        self.assertTrue(any(not r['wet_components'] for r in rows))
        components[30:,:] = 2
        rows, common = observe_branches(bed, components, [0,0], [0,0], 1.)
        self.assertTrue(all(r['wet_components'] for r in rows))
        self.assertEqual(common,[])  # Locally wet is not a connected descent.


if __name__ == '__main__': unittest.main()
