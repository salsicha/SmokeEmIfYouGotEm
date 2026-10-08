import copy
import json
import unittest
from xml.etree.ElementTree import Element, SubElement, tostring

from pyproj import Transformer

from register_colorado_takeout import register, sha, EVIDENCE


class TakeoutRegistration(unittest.TestCase):
    def fixture(self):
        evidence = json.loads(EVIDENCE.read_text())
        transform = Transformer.from_crs(4326, 6404, always_xy=True)
        x, y = transform.transform(*evidence['takeout']['lon_lat'])
        # Synthetic north-flowing metric route: takeout 10 m on left bank.
        chart = dict(schema='raftsim.curved_river_coordinate_map.v1',
            river_id='colorado_river', section_id='colorado_continuous_source_route',
            world_y_sign=-1, horizontal_origin_epsg6404_m=[x+10, y-100],
            points=[[0, 0, 0, -1, 0], [1000, 0, 1000, -1, 0]])
        inverse = Transformer.from_crs(6404, 4326, always_xy=True)
        evidence['downstream_rapid']['lon_lat'] = list(inverse.transform(x+10, y+500))
        return chart, evidence

    def run_fixture(self, chart, evidence):
        evidence = copy.deepcopy(evidence)
        root = Element('osm')
        for key in ('takeout', 'downstream_rapid'):
            item = evidence[key]
            node = SubElement(root, 'node', id=item['node_id'], version=item['version'],
                timestamp=item['timestamp'], lon=str(item['lon_lat'][0]), lat=str(item['lon_lat'][1]))
            SubElement(node, 'tag', k='name', v=item['name'])
            SubElement(node, 'tag', k=item['required_tag'][0], v=item['required_tag'][1])
        osm = tostring(root)
        encoded = json.dumps(chart).encode()
        evidence['source_chart_sha256'] = sha(encoded)
        evidence['osm_capture']['sha256'] = sha(osm)
        return register(encoded, json.dumps(evidence).encode(), osm)

    def test_left_bank_source_station_not_runtime_or_guide_miles(self):
        result = self.run_fixture(*self.fixture())
        self.assertAlmostEqual(result['takeout']['source_route_station_m'], 100, places=3)
        self.assertAlmostEqual(result['takeout']['source_left_lateral_m'], 10, places=3)
        self.assertAlmostEqual(result['takeout_to_rapid_source_distance_m'], 500, places=2)
        self.assertIsNone(result['runtime_finish_station_m'])
        self.assertFalse(result['runtime_ready'])
        self.assertFalse(result['runtime_assets_changed'])
        self.assertEqual(result['retained_source_extent_m'], [0, 1000])
        self.assertEqual(result['license'], 'ODbL-1.0')

    def test_mislabelled_numerical_chart_rejected(self):
        chart, evidence = self.fixture()
        chart['section_id'] = 'colorado_continuous'
        with self.assertRaisesRegex(ValueError, 'geographic source route'):
            self.run_fixture(chart, evidence)

    def test_endpoint_clamping_is_not_registration(self):
        chart, evidence = self.fixture()
        chart['horizontal_origin_epsg6404_m'][1] += 200
        with self.assertRaisesRegex(ValueError, 'clamped to endpoint'):
            self.run_fixture(chart, evidence)

    def test_point_far_from_channel_rejected(self):
        chart, evidence = self.fixture()
        chart['horizontal_origin_epsg6404_m'][0] += 200
        with self.assertRaisesRegex(ValueError, 'outside source corridor'):
            self.run_fixture(chart, evidence)

    def test_station_scale_cannot_be_changed_to_guide_miles(self):
        chart, evidence = self.fixture()
        chart['points'][1][0] = 1609.344
        with self.assertRaisesRegex(ValueError, 'metric route geometry'):
            self.run_fixture(chart, evidence)

    def test_takeout_downstream_of_rapid_rejected(self):
        chart, evidence = self.fixture()
        t = Transformer.from_crs(6404, 4326, always_xy=True)
        x, y = chart['horizontal_origin_epsg6404_m']
        evidence['downstream_rapid']['lon_lat'] = list(t.transform(x, y+50))
        with self.assertRaisesRegex(ValueError, 'upstream of the rapid'):
            self.run_fixture(chart, evidence)

    def test_live_evidence_is_bound_to_source_hash_not_mutable_url(self):
        evidence = json.loads(EVIDENCE.read_text())
        self.assertEqual(len(evidence['source_chart_sha256']), 64)
        with self.assertRaisesRegex(ValueError, 'Source route identity changed'):
            register(b'{}', json.dumps(evidence).encode(), b'<osm/>')


if __name__ == '__main__':
    unittest.main()
