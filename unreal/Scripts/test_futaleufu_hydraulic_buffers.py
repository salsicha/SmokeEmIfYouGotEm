import unittest
import hashlib
import numpy as np
from build_futaleufu_hydraulic_buffers import extend_interval, exact_interval, verify_captured_text


class HydraulicBufferTests(unittest.TestCase):
    def setUp(self):
        self.xy=np.c_[[0,30,75,130,210,300,410],[0,2,7,3,0,6,0]]

    def test_both_buffers_retain_every_original_vertex(self):
        first,last,xy,info=extend_interval(self.xy,2,4,60,before=True,after=True)
        self.assertEqual((first,last),(0,5))
        a,b=info['retained_vertex_interval_in_buffer']
        np.testing.assert_array_equal(xy[a:b+1],self.xy[2:5])
        self.assertGreaterEqual(info['upstream_added_m'],60)
        self.assertGreaterEqual(info['downstream_added_m'],60)

    def test_no_tangent_extrapolation_when_capture_ends(self):
        with self.assertRaises(ValueError):extend_interval(self.xy,1,4,100,before=True)
        with self.assertRaises(ValueError):extend_interval(self.xy,2,5,200,after=True)

    def test_exact_subchain_does_not_snap_or_reverse(self):
        self.assertEqual(exact_interval(self.xy,self.xy[2:5]),(2,4))
        for subset in (self.xy[2:5][::-1],self.xy[2:5]+1.e-8,self.xy[[2,4]]):
            with self.assertRaises(ValueError):exact_interval(self.xy,subset)

    def test_duplicate_complete_match_is_ambiguous(self):
        repeated=np.vstack((self.xy,self.xy))
        with self.assertRaises(ValueError):exact_interval(repeated,self.xy[2:5])

    def test_invalid_buffer_request_refused(self):
        for distance in (0,-1,np.nan,np.inf,True):
            with self.assertRaises(ValueError):extend_interval(self.xy,2,4,distance,before=True)
        with self.assertRaises(ValueError):extend_interval(self.xy,True,4,20,before=True)

    def test_historical_hash_allows_only_exact_crlf_substitution(self):
        raw=b'{\n  "x": 1.25\n}\n';digest=hashlib.sha256(raw).hexdigest()
        self.assertFalse(verify_captured_text(raw,digest)['only_crlf_normalization_needed'])
        self.assertTrue(verify_captured_text(raw.replace(b'\n',b'\r\n'),digest)['only_crlf_normalization_needed'])
        for bad in (raw.replace(b'1.25',b'1.26'),raw.replace(b'  ',b' '),raw+b' '):
            with self.assertRaises(ValueError):verify_captured_text(bad,digest)


if __name__=='__main__':unittest.main()
