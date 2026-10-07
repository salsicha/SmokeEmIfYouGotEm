import unittest

from audit_chilko_catalog_locations import audit, project, runtime_centreline, validate_identity_checks


class ChilkoLocations(unittest.TestCase):
    def test_stored_and_terrain_chainage_are_explicitly_distinct(self):
        result = audit()
        self.assertAlmostEqual(result['route_lengths_m']['stored'], 55845.695680, places=3)
        self.assertAlmostEqual(result['route_lengths_m']['terrain_projected'], 55930.122579, places=3)
        anchors = {a['id']: a for a in result['anchors']}
        self.assertGreater(anchors['bcww_bidwell']['terrain_route_station_m'],
                           anchors['bcww_bidwell']['route_station_m'] + 40)
        green = next(e for e in result['entries'] if e['name'] == 'Green Mile')
        self.assertEqual(green['terrain_marker_bracket_m_not_rapid_bounds'],
                         [anchors[key]['terrain_route_station_m']
                          for key in ('bcww_bidwell', 'bcww_white_mile')])
        self.assertIsNone(green['boundary_lon_lat'])

    def test_runtime_stationing_uses_geographic_origin_without_y_reflection(self):
        chart = dict(schema='raftsim.curved_river_coordinate_map.v1',
            horizontal_crs='EPSG:3157 NAD83(CSRS) / UTM zone 10N', world_y_sign=-1,
            horizontal_origin_m=[400000, 5700000],
            points=[[0, 2, -3, 1, 0], [10, 4, 7, 1, 0]])
        self.assertEqual(runtime_centreline(chart).tolist(),
                         [[400002, 5699997, 0], [400004, 5700007, 10]])
        chart['horizontal_crs'] = 'EPSG:4326'
        with self.assertRaises(ValueError):
            runtime_centreline(chart)

    def test_projection_uses_segment_not_nearest_vertex(self):
        result = project([4, 3], [[0, 0], [10, 0]], [100, 110])
        self.assertAlmostEqual(result['route_station_m'], 104)
        self.assertAlmostEqual(result['point_to_route_m'], 3)

    def test_invalid_route_refused(self):
        for xy, station in [([[0, 0], [0, 0]], [0, 1]),
                            ([[0, 0], [1, 1]], [1, 0]),
                            ([[0, 0], [float('nan'), 1]], [0, 1])]:
            with self.assertRaises(ValueError):
                project([0, 0], xy, station)

    def test_source_points_do_not_become_invented_rapid_bounds(self):
        result = audit()
        self.assertFalse(result['runtime_ready'])
        self.assertFalse(result['modified_runtime_assets'])
        anchors = {a['id']: a for a in result['anchors']}
        self.assertLess(abs(anchors['bcww_bidwell']['route_station_m'] -
                            anchors['caltopo_bidwell']['route_station_m']), 100)
        self.assertLess(anchors['bcww_bidwell']['point_to_route_m'], 10)
        self.assertLess(anchors['bcww_white_mile']['point_to_route_m'], 10)
        for entry in result['entries']:
            self.assertIsNone(entry['boundary_lon_lat'])
        green = next(e for e in result['entries'] if e['name'] == 'Green Mile')
        self.assertEqual(green['location_status'], 'sequence_bracket_only')
        self.assertLess(green['source_marker_bracket_m_not_rapid_bounds'][1],
                        result['current_centreline_route_extent_m'][0])
        self.assertTrue(all(c['displacement_from_source_marker_m'] > 4000
                            for c in result['current_map_comparisons']))

    def test_shared_sequence_is_not_proof_of_alias_or_two_distinct_rapids(self):
        result = audit()
        entries = {entry['name']: entry for entry in result['entries']}
        self.assertEqual(entries['Green Mile']['source_marker_bracket_m_not_rapid_bounds'],
                         entries['White Kilometer']['source_marker_bracket_m_not_rapid_bounds'])
        for check in result['identity_checks']:
            self.assertEqual(check['relationship'], 'unresolved')
            self.assertFalse(check['automatic_alias_allowed'])
            self.assertFalse(check['distinct_geographic_sections_confirmed'])

    def test_unresolved_identity_cannot_be_promoted_by_flag(self):
        for flag in ('automatic_alias_allowed', 'distinct_geographic_sections_confirmed'):
            check = dict(names=['a', 'b'], sources=['trip'], relationship='unresolved',
                         automatic_alias_allowed=False, distinct_geographic_sections_confirmed=False)
            check[flag] = True
            with self.assertRaises(ValueError):
                validate_identity_checks(dict(sources={'trip': {}}, identity_checks=[check]))

    def test_magic_canyon_is_a_research_lead_not_a_placed_catalog_entry(self):
        result = audit()
        magic = next(item for item in result['qualitative_location_constraints']
                     if item['name'] == 'Magic Canyon')
        self.assertEqual(magic['upstream_sequence'], ['Bidwell', 'Green Mile', 'White Mile'])
        self.assertEqual(magic['downstream_landmark'], 'Taseko confluence')
        self.assertFalse(magic['coordinate_placement_authorized'])
        check = next(item for item in result['identity_checks']
                     if item['names'] == ['Miracle Canyon', 'Magic Canyon'])
        self.assertEqual(check['relationship'], 'unresolved')
        self.assertFalse(check['automatic_alias_allowed'])
        self.assertNotIn('Magic Canyon', [item['name'] for item in result['entries']])

    def test_identity_requires_traceable_source(self):
        with self.assertRaises(ValueError):
            validate_identity_checks(dict(sources={}, identity_checks=[dict(
                names=['a', 'b'], sources=['missing'], relationship='unresolved',
                automatic_alias_allowed=False, distinct_geographic_sections_confirmed=False)]))

    def test_additional_trip_accounts_do_not_create_coordinate_authority(self):
        # Historical sequence and hazard descriptions are not surveyed bounds.
        result = audit()
        self.assertFalse(result['runtime_ready'])
        for name in ('Green Mile', 'Miracle Canyon'):
            entry = next(item for item in result['entries'] if item['name'] == name)
            self.assertIsNone(entry['boundary_lon_lat'])
            self.assertNotIn('shandro_1992', entry['sources'])
            self.assertNotIn('wells_expedition_part_one', entry['sources'])

    def test_fisheries_magic_mile_is_not_a_rafting_canyon_alias(self):
        result = audit()
        lead = next(item for item in result['rejected_location_leads']
                    if item['source_name'] == 'Magic Mile')
        self.assertEqual(lead['source'], 'psc_chinook_2011')
        self.assertIn('Miracle Canyon', lead['not_an_authorized_alias_for'])
        self.assertFalse(lead['coordinate_placement_authorized'])
        self.assertNotIn('Magic Mile', [item['name'] for item in result['entries']])

    def test_eyewitness_landmarks_remain_qualitative_not_coordinates(self):
        result = audit()
        white = next(item for item in result['qualitative_location_constraints']
                     if item['name'] == 'White Mile')
        self.assertEqual(white['source'], 'collins_2004')
        self.assertEqual(white['upstream_sequence'], ['Bidwell', 'White Kilometer'])
        self.assertFalse(white['coordinate_placement_authorized'])
        self.assertFalse(result['runtime_ready'])
        kilometre = next(item for item in result['entries'] if item['name'] == 'White Kilometer')
        self.assertIn('collins_2004', kilometre['sources'])
        self.assertIsNone(kilometre['boundary_lon_lat'])


if __name__ == '__main__':
    unittest.main()
