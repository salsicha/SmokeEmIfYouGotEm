import unittest
import numpy as np
from build_futaleufu_buffer_profile import splice_profile, SAMPLES, SECTIONS


def profile(start, length, z):
    s = np.linspace(0,length,3)
    return dict(station_m=s,stage_m=np.array(z,float),easting_m=start+s,
        northing_m=np.full(3,4.),left_m=np.full(3,-3.),right_m=np.full(3,7.),
        bank_span_mapped=np.ones(3,bool),raw_section_stage_m=np.array([z[0],z[-1]],float),
        fitted_section_stage_m=np.array([z[0],z[-1]],float),
        section_station_m=np.array([length/4,length*3/4]),spectral_span_interpolated=np.zeros(2,bool))


class BufferProfileTests(unittest.TestCase):
    def test_incoming_preserves_every_interior_value_with_station_offset(self):
        old = profile(40,100,[10,9,8]); extra = profile(0,40,[12,11,10])
        merged,(a,b) = splice_profile(old,extra,True)
        self.assertEqual((a,b),(2,5))
        for k in SAMPLES:
            np.testing.assert_array_equal(merged[k][a:b],old[k]+40 if k=='station_m' else old[k])
        for k in SECTIONS:
            np.testing.assert_array_equal(merged[k][-2:],old[k]+40 if k=='section_station_m' else old[k])
        self.assertTrue(np.all(np.diff(merged['station_m'])>0))
        self.assertEqual(old['station_m'][0],0)

    def test_outgoing_preserves_interior_and_does_not_duplicate_join(self):
        old = profile(0,100,[10,9,8]); extra = profile(100,40,[8,7,6])
        merged,(a,b) = splice_profile(old,extra,False)
        self.assertEqual((a,b),(0,3))
        for k in SAMPLES: np.testing.assert_array_equal(merged[k][:3],old[k])
        np.testing.assert_array_equal(merged['station_m'],[0,50,100,120,140])

    def test_join_mismatch_is_not_silently_interpolated(self):
        old = profile(40,100,[10,9,8])
        for k in ('stage_m','easting_m','northing_m','left_m','right_m'):
            extra = profile(0,40,[12,11,10]); extra[k][-1] += .001
            with self.assertRaises(ValueError): splice_profile(old,extra,True)

    def test_nonmonotone_stage_and_invalid_arrays_refused(self):
        old = profile(40,100,[10,9,8])
        for k,v in (('stage_m',np.array([12.,13.,10.])),('station_m',np.array([0.,0.,40.])),
                    ('left_m',np.full(3,np.nan)),('right_m',np.full(3,-4.))):
            extra = profile(0,40,[12,11,10]); extra[k] = v
            with self.assertRaises(ValueError): splice_profile(old,extra,True)


if __name__=='__main__': unittest.main()
