import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np
from shapely.geometry import LineString, Point, box

from export_chilko_corridor_terrain import corridor_chunks, export, LandscapeTriangles, SPAN, sha
from audit_chilko_corridor_bed import longest_supported_width,verify_mapped_mask


class CorridorExportTests(unittest.TestCase):
    def test_source_mask_cannot_invent_water_or_extrapolate_past_route_ends(self):
        line=LineString([(0,0),(10,0)]);polygon=box(-2,-2,12,2)
        xy=np.array([[-1.,0.],[2.,0.],[5.,3.],[11.,0.]])
        mask=np.array([False,True,False,False])
        np.testing.assert_array_equal(verify_mapped_mask(mask,xy,polygon,line),[2.])
        for i in (0,1,2,3):
            bad=mask.copy();bad[i]=~bad[i]
            with self.assertRaisesRegex(ValueError,'original mapped polygons'):
                verify_mapped_mask(bad,xy,polygon,line)

    def test_clearance_is_sample_span_not_inflated_cell_width(self):
        self.assertEqual(longest_supported_width([False, True, True, True, False]), 4.)
        self.assertEqual(longest_supported_width([False, True, False, True, False]), 0.)
        self.assertEqual(longest_supported_width([False, False]), 0.)
        self.assertEqual(longest_supported_width([True, True]), 2.)
        with self.assertRaises(ValueError): longest_supported_width([1, 2])

    def test_complete_route_buffer_selected_without_distant_rectangle_corners(self):
        line = LineString([(0, 0), (1000, 0), (1000, 1000)])
        indices = corridor_chunks(line, [0, 0], 100)
        for point in [Point(0, 0), Point(500, 90), Point(1090, 500), Point(1000, 1000)]:
            self.assertTrue(any(box(i*SPAN, j*SPAN, (i+1)*SPAN, (j+1)*SPAN).covers(point)
                                for i, j in indices))
        self.assertNotIn((0, 3), indices)
        with self.assertRaises(ValueError): corridor_chunks(line, [0, 0], 1001)

    def test_export_reloads_actual_png_triangles_and_keeps_source_receipts(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); terrain = root/'terrain'; terrain.mkdir()
            manifest = terrain/'manifest.json'; manifest.write_text('{}')
            profile = root/'profile.json'; profile.write_text('{}')
            def sample(xy):
                height = 1000 + .01*xy[..., 0] + .02*xy[..., 1]
                return dict(height_m=height, source_height_m=height.copy(),
                    source_kind=np.ones(height.shape, np.uint8), inferred_bed=np.zeros(height.shape, bool),
                    mapped_water=np.zeros(height.shape, bool), reference_m=np.full(height.shape, np.nan))
            model = SimpleNamespace(line=LineString([(0, 0), (260, 0)]), sample=sample,
                terrain=SimpleNamespace(folder=terrain, manifest=dict(source_kind={'1': 'native test terrain'})),
                receipt=dict(terrain_manifest_sha256=sha(manifest),
                             profile_manifest=str(profile), profile_manifest_sha256=sha(profile)))
            out = root/'out'
            with patch('export_chilko_corridor_terrain.CorridorBed', return_value=model):
                m = export(terrain, root, out, [0, 0], 900., buffer_m=100)
            reader = LandscapeTriangles(out)
            self.assertEqual(len(reader.chunks), len(m['chunks']))
            self.assertLessEqual(m['maximum_height_quantization_error_m'], 2400/65535/2+1e-9)
            self.assertEqual(m['vertex_counts_including_shared_edges']['inferred_bed'], 0)
            self.assertFalse(m['engine_validated']); self.assertFalse(m['full_river_complete'])
            self.assertEqual(m['geographic_scope']['route_interval_m'], [0., 260.])
            for entry in m['chunks']:
                self.assertEqual(sha(out/entry['source_receipt']), entry['source_receipt_sha256'])
                with np.load(out/entry['source_receipt']) as z:
                    np.testing.assert_array_equal(z['source_height_m'], z['height_m'])
            # The real reader must catch a modified encoded tile, not just text.
            p = out/m['chunks'][0]['heightfield']; p.write_bytes(p.read_bytes()+b'changed')
            with self.assertRaisesRegex(ValueError, 'Changed'): LandscapeTriangles(out)


if __name__ == '__main__': unittest.main()
