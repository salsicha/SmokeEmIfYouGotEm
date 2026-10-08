import json
import math
import subprocess
import unittest
from register_pacuare_highway_bridge import DATA, ROOT, build, crossing, search_point


class PacuareBridgeTests(unittest.TestCase):
    def test_saved_registration_reproduces_from_current_sources(self):
        receipt=DATA/'review/highway_bridge_registration_2026_10_08.json'
        self.assertEqual(json.loads(receipt.read_text(encoding='utf-8')),build())

    def test_hash_locked_text_sources_have_portable_checkout_bytes(self):
        paths=[p for p in build()['sources_sha256'] if p.endswith(('.py','.osm'))]
        self.assertEqual(len(paths),4)
        raw=subprocess.check_output(['git','check-attr','-z','eol','--',*paths],cwd=ROOT)
        fields=raw.decode('utf-8').rstrip('\0').split('\0')
        attributes=dict((fields[i],fields[i+2]) for i in range(0,len(fields),3))
        self.assertEqual(attributes,dict.fromkeys(paths,'lf'))

    def test_actual_sources_supply_two_distinct_downstream_controls(self):
        result=build()
        self.assertEqual(len(result['alternatives']),2)
        self.assertGreater(result['search_station_span_m'][1],result['search_station_span_m'][0])
        for a in result['alternatives']:
            self.assertLess(result['lower_control']['source_chain_m'],a['search_location']['source_chain_m'])
            self.assertLess(a['search_location']['source_chain_m'],a['highway_control']['source_chain_m'])
            self.assertEqual(a['highway_control']['tags']['ref'],'32')
        self.assertIsNone(result['rapid_boundary_coordinates'])
        self.assertFalse(result['runtime_placement_authorized'])
        self.assertFalse(result['production_promoted'])

    def test_crossing_uses_segment_not_bridge_midpoint(self):
        result=crossing([[0,0,0],[10,0,100]],[(2,-1),(2,9)])
        self.assertEqual(result['source_chain_m'],20)
        self.assertEqual(result['lon_lat'],[2,0])

    def test_vertex_crossing_is_not_double_counted(self):
        self.assertEqual(crossing([[0,0,0],[2,0,20],[10,0,100]],[(2,-1),(2,9)])['source_chain_m'],20)

    def test_missing_or_multiple_crossings_refuse(self):
        for river in ([[0,0,0],[1,0,10]],[[0,0,0],[10,0,100],[0,1,200]]):
            with self.assertRaises(ValueError):crossing(river,[(2,-1),(2,9)])

    def test_no_extrapolation_or_reversed_control(self):
        low=dict(guide_km=2,source_chain_m=20);high=dict(guide_km=8,source_chain_m=80)
        route=[[0,0,0],[10,0,100]]
        self.assertEqual(search_point(5,low,high,route)['source_chain_m'],50)
        for km in (1,9,math.nan):
            with self.assertRaises(ValueError):search_point(km,low,high,route)
        with self.assertRaises(ValueError):search_point(5,high,low,route)


if __name__=='__main__':unittest.main()
