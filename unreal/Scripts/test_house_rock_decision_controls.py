import unittest
from build_house_rock_decision_controls import build


class HouseRockControls(unittest.TestCase):
    def setUp(self):
        self.contract=dict(launch=dict(station_m=300),finish_station_m=1300,
                           cooked_fields='runtime/house_rock/cooked_flow_fields',
                           section_id='catalog_house_rock',
                           map_package='/Game/RaftSim/Maps/Catalog/L_Colorado_HouseRock',
                           display_name='House Rock')
        self.plan=build(self.contract)[0]

    def test_whole_drop_including_both_holes_and_pool(self):
        self.assertEqual(len(self.plan['trials']),6)
        for t in self.plan['trials']:
            self.assertEqual((t['start_m'],t['finish_m']),(700,1060))
            self.assertTrue(t['strict_route'])
            self.assertFalse(t['normal_rescue_inputs'])
            self.assertEqual([g['station_m'] for g in t['gates']],[760,842,882,910,1058])

    def test_timing_pair_starts_at_same_place_and_preserves_right_passage(self):
        rows={t['variant']:t for t in self.plan['trials']}
        early,late=rows['left-early'],rows['left-late']
        self.assertEqual(early['route_laterals'][0],late['route_laterals'][0])
        self.assertEqual(early['route_laterals'][-1],late['route_laterals'][-1])
        self.assertEqual(early['lookahead_m'],late['lookahead_m'])
        self.assertLess(early['route_laterals'][1][0],late['route_laterals'][1][0])
        self.assertTrue(rows['left-no-steering']['disable_steering'])
        self.assertNotIn('disable_steering',rows['hands-off'])

    def test_wrong_map_and_partial_boundaries_refused(self):
        with self.assertRaises(ValueError):build(self.contract|dict(section_id='catalog_badger_creek'))
        with self.assertRaises(ValueError):build(self.contract|dict(finish_station_m=950))


if __name__=='__main__':unittest.main()
