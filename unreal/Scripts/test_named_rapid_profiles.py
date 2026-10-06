import copy
import json
import math
import unittest
from build_named_rapid_profiles import CATALOGUES, ROOT, OUTPUT, compile_catalogue, lateral_centres, render


class NamedProfiles(unittest.TestCase):
    def test_generated_asset_matches_catalogues(self):
        self.assertEqual(OUTPUT.read_text(), render())

    def test_all_supported_hydraulics_have_rows_but_rocks_are_not_faked(self):
        for map_name, relative in CATALOGUES.items():
            data = json.loads((ROOT/'physics/data/real_world'/relative).read_text())
            rows = compile_catalogue(map_name, data)
            ids = {r[0] for r in rows}
            self.assertTrue(rows)
            for f in data['features']:
                if f['type'] in ('boulder', 'rock_garden', 'drop', 'sill'):
                    self.assertNotIn(f['id'], ids)
            self.assertTrue(all(all(math.isfinite(v) for v in r[1:]) for r in rows))
            self.assertTrue(all(0 < r[4] <= 1.2 for r in rows))

    def test_catalog_class_is_not_a_force_coefficient(self):
        for map_name, relative in CATALOGUES.items():
            data = json.loads((ROOT/'physics/data/real_world'/relative).read_text())
            before = compile_catalogue(map_name, data)
            for rapid in data['rapids']:
                rapid['rapid_class'] = 'VI'
            self.assertEqual(before, compile_catalogue(map_name, data))

    def test_evidence_frame_cannot_be_silently_used_as_scenario(self):
        with self.assertRaises(ValueError):
            compile_catalogue('unknown', {'station_frame':'evidence','features':[]})

    def test_width_has_no_gaps_in_existing_compact_roller(self):
        for width in (1, 6, 10, 12, 16, 24, 36, 60):
            points = lateral_centres(width)
            self.assertTrue(all(b-a <= 6.001 for a,b in zip(points,points[1:])))
            self.assertAlmostEqual(sum(points), 0.)

    def test_portage_remains_portage(self):
        data=json.loads((ROOT/'physics/data/real_world'/CATALOGUES['L_Zambezi']).read_text())
        self.assertFalse(any(r[0].startswith('r9_') for r in compile_catalogue('L_Zambezi',data)))

    def test_nonfinite_or_nonpositive_relief_is_refused(self):
        for field,value in (('amplitude_m',float('nan')),('amplitude_m',0),
                            ('amplitude_m',-1),('angle_deg',float('inf'))):
            feature=dict(id='test',type='wave_train',station_m=50,lateral_m=0,width_m=10)
            feature[field]=value
            with self.assertRaises(ValueError):
                compile_catalogue('test',dict(station_frame='scenario',features=[feature]))


if __name__=='__main__':
    unittest.main()
