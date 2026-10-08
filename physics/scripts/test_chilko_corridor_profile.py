import unittest
import numpy as np
from build_chilko_corridor_profile import channel_section, surface_reference, bridge_short_reference_gaps, reference_weights


class CorridorProfileTests(unittest.TestCase):
    def data(self):
        x=np.arange(-40,41,2.);h=np.full(len(x),100.,np.float32);k=np.ones(len(x),np.uint8)
        water=(x>=-20)&(x<=20)
        return x,water,h,k

    def test_islands_and_nearby_channels_are_not_flattened_together(self):
        x,w,h,k=self.data();w[x==14]=False;w[x>=24]=True;h[x>=16]=500
        r=channel_section(x,w,h,k)
        self.assertEqual(r['left_bank_m'],13);self.assertEqual(r['right_bank_m'],-21)
        self.assertEqual(r['width_m'],34);self.assertEqual(r['reference_m'],100)

    def test_high_emergent_samples_do_not_raise_surface_reference(self):
        x,w,h,k=self.data();h[x==0]=105
        r=channel_section(x,w,h,k)
        self.assertEqual(r['reference_m'],100);self.assertEqual(r['surface_sample_range_m'],[100,100])

    def test_conditioned_fallback_reference_stays_inferred(self):
        x,w,h,k=self.data();k[x<0]=3
        r=channel_section(x,w,h,k);self.assertEqual(r['surface_source_kind'],3)
        self.assertLess(r['native_support_count'],r['support_count'])

    def test_finer_sampling_resolves_narrow_branch_without_reducing_bank_margin(self):
        x=np.arange(-20,21,1.);h=np.full(len(x),100.,np.float32);k=np.ones(len(x),np.uint8)
        w=(x>=-7)&(x<=5);h[(x<-4)|(x>2)]=120
        r=channel_section(x,w,h,k)
        self.assertEqual(r['width_m'],13);self.assertEqual(r['reference_m'],100)
        self.assertEqual(r['support_count'],7)

    def test_missing_support_outside_source_and_truncated_width_refused(self):
        x,w,h,k=self.data();h[x==0]=np.nan;k[x==0]=0
        with self.assertRaisesRegex(ValueError,'interior'):channel_section(x,w,h,k)
        x,w,h,k=self.data();w[x==0]=False
        with self.assertRaisesRegex(ValueError,'leaves'):channel_section(x,w,h,k)
        with self.assertRaisesRegex(ValueError,'width'):channel_section(x,np.ones(len(x),bool),h,k)

    def test_diagnostic_gaps_are_not_silently_interpolated(self):
        sections=[dict(reference_m=100.,support_count=4,native_support_count=4),None,
                  dict(reference_m=101.,support_count=4,native_support_count=4)]
        raw,ref,support=surface_reference(sections)
        np.testing.assert_array_equal(support,[True,False,True])
        self.assertTrue(np.isnan(raw[1]));self.assertTrue(np.isnan(ref[1]))
        np.testing.assert_array_equal(ref[[0,2]],[100.5,100.5])

    def test_resampled_coarse_surface_does_not_outvote_native_surface(self):
        coarse=dict(reference_m=95.,support_count=30,native_support_count=0)
        native=dict(reference_m=100.,support_count=30,native_support_count=30)
        raw,ref,support=surface_reference([coarse,native])
        np.testing.assert_array_equal(raw,[95.,100.])
        np.testing.assert_allclose(ref,(95./900.+100.)/(1.+1./900.))
        self.assertLess(100.-ref[1],.006)
        np.testing.assert_array_equal(support,[True,True])
        np.testing.assert_allclose(reference_weights([coarse,native]),[30./900.,30.])

    def test_invalid_support_provenance_is_not_silently_native(self):
        with self.assertRaises(ValueError):
            surface_reference([dict(reference_m=100.,support_count=2,native_support_count=3)])

    def test_explicit_short_gap_stage_inference_preserves_source(self):
        stations=np.arange(6)*4.;raw=np.array([100,np.nan,np.nan,np.nan,np.nan,99.8])
        result,records=bridge_short_reference_gaps(stations,raw)
        np.testing.assert_allclose(result,np.linspace(100,99.8,6))
        self.assertTrue(np.isnan(raw[1:-1]).all());self.assertEqual(records[0]['inferred_sections'],4)
        self.assertEqual(records[0]['span_m'],20)

    def test_long_steep_uphill_and_endpoint_gaps_are_not_filled(self):
        for s,h in [([0,12,24],[100,np.nan,99.9]),([0,4,8],[100,np.nan,99]),
                    ([0,4,8],[100,np.nan,101]),([0,4,8],[np.nan,100,np.nan])]:
            result,records=bridge_short_reference_gaps(s,h)
            np.testing.assert_array_equal(result,h);self.assertFalse(records)


if __name__=='__main__':unittest.main()
