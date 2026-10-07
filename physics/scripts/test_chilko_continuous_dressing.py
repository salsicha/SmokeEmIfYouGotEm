import unittest
import numpy as np
from build_chilko_continuous_dressing import eligible, MESHES, MESH_ROOT
from build_colorado_continuous_dressing import candidates


class ChilkoDressingTests(unittest.TestCase):
    def test_both_water_sources_steep_and_unknown_ground_exclude_plants(self):
        z=np.full(10,100.); z[4]=np.nan
        slope=np.zeros(10); slope[3]=np.tan(np.deg2rad(30)); slope[5]=np.nan
        source=np.array([12,11.99,20,20,20,20,350,350.01,np.inf,20])
        solved=np.array([12,20,11.99,20,20,20,20,20,20,np.inf])
        np.testing.assert_array_equal(eligible(z,slope,source,solved),
            [True,False,False,False,False,False,True,False,False,False])

    def test_profile_sampling_is_reproducible_and_chunk_order_independent(self):
        kw=dict(seed_prefix='chilko-conifer-shrub-v1',probability=.55)
        a=candidates([443000,5751000],**kw)
        b=candidates([443252,5751000],**kw)
        np.testing.assert_array_equal(a,candidates([443000,5751000],**kw))
        self.assertFalse(set(map(tuple,a[:,:2])) & set(map(tuple,b[:,:2])))
        self.assertGreater(len(a),150)
        self.assertEqual(set(a[:,4]),{0,1,2,3})
        self.assertTrue(((a[:,3]>=.65)&(a[:,3]<1.2)).all())
        self.assertFalse(np.array_equal(a,candidates([443000,5751000])))

    def test_invalid_candidate_sampling_is_rejected(self):
        for kw in (dict(spacing=0),dict(span=-1),dict(probability=-.1),
                   dict(probability=1.1),dict(probability=np.nan)):
            with self.assertRaises(ValueError):candidates([0,0],**kw)
        self.assertEqual(candidates([0,0],probability=0).shape,(0,5))

    def test_only_existing_temperate_profile_is_selected(self):
        self.assertEqual(len(set(MESHES)),4)
        self.assertIn('/TemperateRivers/',MESH_ROOT)
        self.assertTrue(all('Temperate_' in name and 'OpaqueV1' in name for name in MESHES))


if __name__=='__main__':unittest.main()
