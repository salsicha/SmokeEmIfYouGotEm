import copy
import unittest
import numpy as np

from register_pacuare_catalog_locations import build, controls, register, validate_route


class PacuareLocationsTests(unittest.TestCase):
    def setUp(self):
        self.route=np.array([[-83.,10.,0.],[-82.9,10.1,1000.],[-82.8,10.2,3000.]])
        self.anchors=[dict(guide_km=4.,source_chain_m=0.,osm_node_id=1,original_lon_lat=[-83.01,10.]),
            dict(guide_km=5.,source_chain_m=1000.,osm_node_id=2,original_lon_lat=[-82.91,10.1]),
            dict(guide_km=6.,source_chain_m=3000.,osm_node_id=3,original_lon_lat=[-82.81,10.2])]

    def test_interpolates_between_controls_not_uniform_order_or_single_offset(self):
        first=register(4.5,self.anchors,self.route)
        second=register(5.5,self.anchors,self.route)
        self.assertEqual(first['source_chain_m'],500.)
        self.assertEqual(second['source_chain_m'],2000.)
        self.assertEqual(second['bracketing_osm_node_ids'],[2,3])
        np.testing.assert_allclose(second['lon_lat'],[-82.85,10.15])

    def test_original_control_coordinates_are_not_replaced_by_route_projection(self):
        result=register(5.,self.anchors,self.route)
        self.assertEqual(result['lon_lat'],[-82.91,10.1])
        self.assertEqual(result['route_projection_lon_lat'],[-82.9,10.1])

    def test_extrapolation_and_nonfinite_distances_are_not_silent(self):
        for km in (3.33,6.01):
            self.assertIsNone(register(km,self.anchors,self.route)['lon_lat'])
        for km in (float('nan'),float('inf'),-1):
            with self.assertRaises(ValueError):register(km,self.anchors,self.route)

    def test_broken_source_route_and_controls_are_refused(self):
        data=dict(schema='raftsim.osm_river_centreline.v1',relation=12000489,
            join_max_endpoint_gap_deg=0,centreline_lon_lat_chain=self.route.tolist(),
            nodes=[dict(id=i,chain_m=s,lon=x,lat=y,offset_from_centreline_m=2.)
                   for i,(x,y,s) in enumerate(self.route,1)])
        evidence=dict(osm_control_guide_km=[[1,4.],[2,5.],[3,6.]])
        self.assertEqual(len(controls(data,evidence)),3)
        for key,value in [('join_max_endpoint_gap_deg',.001),('relation',1),
                          ('centreline_lon_lat_chain',self.route[::-1].tolist())]:
            bad=copy.deepcopy(data);bad[key]=value
            with self.assertRaises(ValueError):validate_route(bad)
        bad=copy.deepcopy(evidence);bad['osm_control_guide_km'][1][1]=7.
        with self.assertRaises(ValueError):controls(data,bad)

    def test_real_registration_preserves_unresolved_entries_and_source_frames(self):
        result=build();rows={r['name']:r for r in result['rapid_locations']}
        self.assertEqual(len(rows),15)
        self.assertAlmostEqual(result['single_offset_spread_m'],167.6)
        self.assertFalse(result['offset_spread_is_accuracy_bound'])
        for name in ('Bienvenidos','Bobo Falls','Las Ranitas'):
            self.assertIsNone(rows[name]['location']['lon_lat'])
        self.assertEqual(rows['Bienvenidos']['location']['guide_km'],3.33)
        self.assertEqual(rows['Lower Huacas']['location']['source_chain_m'],83041.6)
        self.assertEqual(rows['Dos Montanas']['location']['source_chain_m'],92483.4)
        self.assertTrue(all(r['rapid_boundary_coordinates'] is None for r in rows.values()))
        self.assertTrue(all(r['runtime_placement_authorized'] is False for r in rows.values()))
        self.assertFalse(result['production_promoted'])


if __name__=='__main__':unittest.main()
