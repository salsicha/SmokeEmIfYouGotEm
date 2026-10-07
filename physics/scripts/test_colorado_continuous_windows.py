import unittest
import numpy as np

from build_colorado_continuous_windows import partition
from build_colorado_catalog_evidence import infer_depth


class ContinuousWindows(unittest.TestCase):
    def test_depth_bins_share_global_phase_across_shifted_crops(self):
        # Two source windows begin at different sub-bin phases; interior
        # shoreline, slope and physical sample positions are identical.
        def depth(start,finish):
            s=np.arange(start,finish,dtype=float)
            wet=np.ones((8,len(s)),dtype=bool)
            edge=np.broadcast_to(np.arange(1,9)[:,None],wet.shape)
            local=np.broadcast_to(s-start,wet.shape)
            return s,infer_depth(wet,edge,local,s-start,900-.001*s,100,
                                 station_origin_m=float(start))
        a,da=depth(0,900);b,db=depth(203,1100)
        np.testing.assert_allclose(da[:,350:700],db[:,147:497],atol=1e-10,rtol=0)

    def profile(self):
        return [dict(easting=1000+i*10, northing=3000+i*2,
                     ws_final_source='r10', ws_final=900-i*.01,
                     ws_nonincreasing=900-i*.01, min_bed_height=None)
                for i in range(351)]

    def test_cores_cover_every_metre_without_reset(self):
        rows = partition(self.profile())
        self.assertEqual(rows[0]['source_core_interval_m'][0], 0)
        self.assertAlmostEqual(rows[-1]['source_core_interval_m'][1], (3500**2+700**2)**.5)
        for a, b in zip(rows, rows[1:]):
            self.assertEqual(a['source_core_interval_m'][1], b['source_core_interval_m'][0])
            self.assertGreaterEqual(a['source_halo_interval_m'][1]-b['source_halo_interval_m'][0],600)

    def test_overlap_retains_identical_source_coordinates_and_evidence(self):
        original = self.profile()
        rows = partition(original)
        for tile in rows:
            self.assertIsNone(tile['rapid_point_local_station_m'])
            self.assertFalse(tile['rapid_entry_exit_bounds_verified'])
            for row in tile['samples']:
                self.assertIsNone(row['min_bed_height'])
                for key, value in original[row['source_profile_index']].items():
                    self.assertEqual(row[key], value)
                self.assertAlmostEqual(row['global_arc_station_m'],
                    row['local_arc_station_m']+tile['source_halo_interval_m'][0])

    def test_bad_dimensions_or_disconnected_source_refused(self):
        for core, halo in [(0,300),(1200,0),(float('nan'),300),(1200,501)]:
            with self.assertRaises(ValueError):
                partition(self.profile(),core,halo)
        rows=self.profile()
        rows[20]['easting']+=100
        with self.assertRaises(ValueError):
            partition(rows)


if __name__ == '__main__':
    unittest.main()
