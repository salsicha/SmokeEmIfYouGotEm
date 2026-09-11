import sys
from pathlib import Path
import unittest
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from liquid_contact_region import extract
from build_south_fork_liquid_contact import sample_packed


class ContactRegionTests(unittest.TestCase):
    def profile(self):
        # Deliberately larger than the live DI's 256-column limit.
        nc, nr = 300, 3
        triangles = []
        for r in range(nr):
            for c in range(nc):
                # Continuous tilted terrain, represented with local XY.
                z = 100+c*25+r*50
                triangles.extend([[0,0,z],[50,0,z+25],[0,-50,z+50],
                                  [50,0,z+25],[50,-50,z+75],[0,-50,z+50]])
        return dict(schema='raftsim.registered_liquid_contact.v2',
                    vertex_encoding='nominal-quad-local-xy-and-world-z-centimetres',
                    packed_vectors=[[10000,4000,50],[50,nc,nr],*triangles],
                    source_geometry_sha256='unchanged-test-identity',
                    query_seed_count=42, seed_query_max_error_cm=0)

    def test_crop_preserves_source_geometry_and_queries(self):
        source = self.profile()
        region = extract(source, 200, 1, 100, 2)
        self.assertEqual(region['source_geometry_sha256'], source['source_geometry_sha256'])
        self.assertEqual(region['packed_vectors'][0], [20000,3950,50])
        self.assertEqual(region['triangle_count'], 400)
        expected = np.asarray(source['packed_vectors'][2:]).reshape(3,300,6,3)[1:,200:]
        np.testing.assert_array_equal(np.asarray(region['packed_vectors'][2:]).reshape(2,100,6,3),expected)
        points = np.random.default_rng(73).uniform([20000.01,3850.01],[24999.99,3949.99],(10000,2)).astype(np.float32)
        np.testing.assert_array_equal(sample_packed(region['packed_vectors'],points,True),
                                      sample_packed(source['packed_vectors'],points,True))
        self.assertNotIn('query_seed_count', region)
        self.assertNotIn('seed_query_max_error_cm', region)
        self.assertFalse(region['region_query_accuracy_verified'])
        self.assertEqual(source['packed_vectors'][0], [10000,4000,50])

    def test_rejects_truncation_and_invalid_dimensions(self):
        for rectangle in [(0,0,257,1), (250,0,51,1), (0,-1,2,2), (0,0,1.5,2), (True,0,1,2)]:
            with self.assertRaises(ValueError): extract(self.profile(), *rectangle)
        malformed=self.profile();malformed['packed_vectors'].pop()
        with self.assertRaises(ValueError): extract(malformed,0,0,10,2)

    def test_anchored_pages_preserve_floor_decisions_at_rounding_boundaries(self):
        source = self.profile()
        source['packed_vectors'][0][:2] = [-13988.36328125, 8830.2412109375]
        # Move the origin near a large-coordinate cancellation boundary. Probe
        # both adjacent float32 values at every retained nominal quad edge.
        meta = np.asarray(source['packed_vectors'][0], dtype=np.float32)
        edge = np.float32(meta[0]+np.arange(201, 299)*50)
        xs = np.concatenate([np.nextafter(edge, -np.inf, dtype=np.float32), edge,
                             np.nextafter(edge, np.inf, dtype=np.float32)])
        points = np.c_[xs, np.full(len(xs), meta[1]-73.25, dtype=np.float32)]
        page = extract(source, 200, 0, 100, 3, stable_anchor=True)
        self.assertEqual(page['schema'], 'raftsim.registered_liquid_contact.v3')
        self.assertEqual(page['packed_vectors'][0], source['packed_vectors'][0])
        self.assertEqual(page['packed_vectors'][2], [200, 0, 0])
        np.testing.assert_array_equal(sample_packed(source['packed_vectors'], points, True),
                                      sample_packed(page['packed_vectors'], points, True, True))
        nested = extract(page, 0, 1, 100, 2)
        np.testing.assert_array_equal(sample_packed(source['packed_vectors'], points, True),
                                      sample_packed(nested['packed_vectors'], points, True, True))


if __name__ == '__main__': unittest.main()
