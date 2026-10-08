import unittest
import json
import numpy as np
from build_futaleufu_continuous_canopy import forest_cover,cover_at,eligible,crown_radius,same_bed_source,chunk_index


class ContinuousCanopyTests(unittest.TestCase):
    def test_chunk_ownership_floors_negative_offsets_and_is_json_serializable(self):
        key=chunk_index([999.9,1999.9],[1000.,2000.],252.)
        self.assertEqual(key,(-1,-1));self.assertEqual(json.dumps(list(key)),'[-1, -1]')
        self.assertEqual(chunk_index([1252.,2252.],[1000.,2000.],252.),(1,1))

    def test_export_lineage_may_extend_but_not_replace_bed_sources(self):
        bed=dict(sources_sha256={'source':'one'},depth=1.8)
        self.assertTrue(same_bed_source(dict(sources_sha256={'source':'one','export':'two'},depth=1.8),bed))
        self.assertFalse(same_bed_source(dict(sources_sha256={'source':'changed'},depth=1.8),bed))
        self.assertFalse(same_bed_source(dict(sources_sha256={'source':'one'},depth=2.),bed))

    def source(self):
        return dict(valid=np.ones((7,7),bool),green=np.full((7,7),1400,np.uint16),
            red=np.full((7,7),1200,np.uint16),nir=np.full((7,7),4000,np.uint16))

    def test_majority_never_grows_forest_into_water_or_missing_pixels(self):
        raw=self.source();raw['nir'][3,3]=1100
        mask=forest_cover(raw);self.assertFalse(mask[3,3]);self.assertTrue(mask[2,2])
        raw['nir'][3,3]=0;mask=forest_cover(raw)
        self.assertFalse(mask[2:5,2:5].any());self.assertFalse(mask[0].any())

    def test_bright_pasture_is_not_closed_forest(self):
        raw=self.source();raw['green'][:]=1900
        self.assertFalse(forest_cover(raw).any())

    def test_native_pixel_frame_no_edge_clamping(self):
        cover=np.zeros((3,4),bool);cover[1,2]=True
        grid=dict(epsg=32718,transform=[10.,0.,100.,0.,-10.,200.],shape=[3,4])
        np.testing.assert_array_equal(cover_at([[125,185],[125,205],[99,185],[145,185]],cover,grid),[True,False,False,False])

    def test_clearance_covers_rotated_crown_and_ground_support(self):
        np.testing.assert_array_equal(eligible([1,1,1,np.nan],[0,0,2,0],[20,12,20,20],[8,8,8,8]),[True,False,False,False])
        bounds=dict(min=[-300,-400,-5],max=[200,200,1000])
        self.assertEqual(crown_radius(bounds,[2,2,1]),10.)


if __name__=='__main__':unittest.main()
