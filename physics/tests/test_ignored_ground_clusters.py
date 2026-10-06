import unittest
from review_ignored_ground_clusters import clusters


def row(i,x,peers=3):
    return dict(original_return_index=i,source_utm_navd88_m=[x,0.,2.],classified_ground_peer_count=peers)


class ClusterTests(unittest.TestCase):
    def test_transitive_stable_selection(self):
        result=clusters([row(3,6),row(1,0),row(2,3)])
        self.assertEqual([[r['original_return_index'] for r in g] for g in result],[[1,2,3]])

    def test_isolated_and_unsupported_not_promoted(self):
        self.assertEqual(clusters([row(1,0),row(2,1,2),row(3,10)]),[])

    def test_bad_radius_or_duplicate_rejected(self):
        for radius in (0,-1,float('nan')):
            with self.assertRaises(ValueError): clusters([row(1,0)],radius)
        with self.assertRaises(ValueError): clusters([row(1,0),row(1,1)])
