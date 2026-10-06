import unittest
from build_badger_decision_controls import build


class BadgerControls(unittest.TestCase):
    def setUp(self):
        self.plan=build(dict(launch=dict(station_m=300),finish_station_m=1300,
                            cooked_fields='runtime/badger/cooked_flow_fields',
                            section_id='catalog_badger_creek',
                            map_package='/Game/RaftSim/Maps/Catalog/L_Colorado_BadgerCreek',
                            display_name='Badger Creek'))[0]

    def test_all_controls_use_same_whole_drop_and_no_resets(self):
        self.assertEqual(len(self.plan['trials']),7)
        for t in self.plan['trials']:
            self.assertEqual((t['start_m'],t['finish_m']),(700,1050))
            self.assertTrue(t['strict_route'])
            self.assertFalse(t['normal_rescue_inputs'])
            self.assertEqual([g['station_m'] for g in t['gates']],[740,790,875,1048])

    def test_correction_controls_share_initial_approach(self):
        rows={t['variant']:t for t in self.plan['trials']}
        early,late=rows['right-early'],rows['right-late']
        self.assertEqual(early['route_laterals'][0],late['route_laterals'][0])
        self.assertEqual(early['lookahead_m'],late['lookahead_m'])
        self.assertLess(early['route_laterals'][1][0],late['route_laterals'][1][0])
        self.assertEqual(rows['hands-off']['variant'],'hands-off')


if __name__=='__main__':unittest.main()
