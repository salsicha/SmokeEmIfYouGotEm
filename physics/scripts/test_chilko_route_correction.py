import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
from pyproj import Transformer

import correct_chilko_route as route
from audit_chilko_catalog_locations import corrected_anchor_stationing
from chilko_corridor_chart import hydraulic_frame
from chilko_planform import route_planform_policy
from shapely.geometry import LineString


def lonlat(xy):
    xy=np.array(xy,dtype=float)
    return np.column_stack(Transformer.from_crs(3157,4326,always_xy=True).transform(
        xy[:,0]+400000,xy[:,1]+5700000))


def geometry(points):
    return dict(type='FeatureCollection',features=[dict(type='Feature',properties={},
        geometry=dict(type='LineString',coordinates=points.tolist()))])


class RouteCorrection(unittest.TestCase):
    def test_retirement_requires_original_pixels_and_independent_review(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);scene_id='S2B_10UDC_20231020_0_L2A'
            scene=root/scene_id;scene.mkdir()
            metadata=scene/'item.json';metadata.write_text('{}')
            pixels=scene/'red.tif';pixels.write_bytes(b'original captured pixels')
            capture=root/'capture.json'
            capture.write_text(json.dumps(dict(items=[dict(id=scene_id,item_sha256=route.sha(metadata),
                assets=[dict(name='red',sha256=route.sha(pixels))])])))
            evidence=root/'alignment.json'
            data=dict(schema='raftsim.chilko_route_alignment_evidence.v1',route_sha256='parent',
                observation_crs='EPSG:32610',named_rapid_placement_authorized=False,
                automatic_route_replacement_authorized=False,
                source_scene=dict(id=scene_id,local_capture_receipt_sha256=route.sha(capture)),
                observations=[dict(id=name,inspection_bounds_m=[423500,5732500,423800,5732800])
                    for name in ('upstream_bar_loop','downstream_bar_loop')])
            evidence.write_text(json.dumps(data))
            spec=dict(policy='retire_reviewed_bar_branches_outside_inferred_active_corridor_v1',
                measured_banks=False,evidence=dict(path=str(evidence),sha256=route.sha(evidence)),
                image_capture=dict(path=str(capture),sha256=route.sha(capture)))
            self.assertEqual(route.retirement_evidence(spec,'parent'),data)
            pixels.write_bytes(b'changed pixels')
            with self.assertRaisesRegex(ValueError,'pixels'):route.retirement_evidence(spec,'parent')
            pixels.write_bytes(b'original captured pixels')
            metadata.write_text('{"changed":true}')
            with self.assertRaisesRegex(ValueError,'metadata'):route.retirement_evidence(spec,'parent')
            metadata.write_text('{}')
            with self.assertRaisesRegex(ValueError,'branch areas'):route.retirement_evidence(spec,'other parent')
            for field,value in [('measured_banks',True),('policy','native_wet_mask')]:
                bad=copy.deepcopy(spec);bad[field]=value
                with self.assertRaisesRegex(ValueError,'hypothesis'):route.retirement_evidence(bad,'parent')
            data['observations'][0]['inspection_bounds_m'][2]+=1000
            evidence.write_text(json.dumps(data));spec['evidence']['sha256']=route.sha(evidence)
            with self.assertRaisesRegex(ValueError,'rectangles'):route.retirement_evidence(spec,'parent')

    def setUp(self):
        self.parent=lonlat([[0,0],[50,0],[100,-80],[150,0],[200,0]])
        midpoint=lonlat([[100,5]])[0]
        # Opposite digitisation directions must be handled explicitly.
        self.network=dict(type='FeatureCollection',features=[
            dict(type='Feature',properties=dict(OBJECTID=1,WATERSHED_KEY=356364103),
                geometry=dict(type='LineString',coordinates=[midpoint.tolist(),self.parent[1].tolist()])),
            dict(type='Feature',properties=dict(OBJECTID=2,WATERSHED_KEY=356364103),
                geometry=dict(type='LineString',coordinates=[midpoint.tolist(),self.parent[3].tolist()]))])

    def test_only_selected_interval_changes_and_endpoints_are_exact(self):
        result,changes=route.stitch(self.parent,self.network,[(1,2)])
        np.testing.assert_array_equal(result[:2],self.parent[:2])
        np.testing.assert_array_equal(result[-2:],self.parent[-2:])
        self.assertEqual(changes[0]['endpoint_snap_m'],[0.,0.])
        self.assertEqual((changes[0]['start_vertex'],changes[0]['end_vertex']),(1,3))
        self.assertLess(np.max(np.abs(route.projected(result)[:,1]-5700000)),6.)

    def test_network_z_is_not_promoted_to_bathymetry(self):
        with_z=copy.deepcopy(self.network)
        for f in with_z['features']:
            f['geometry']['coordinates']=[p+[9999.] for p in f['geometry']['coordinates']]
        np.testing.assert_array_equal(route.stitch(self.parent,with_z,[(1,2)])[0],
                                      route.stitch(self.parent,self.network,[(1,2)])[0])

    def test_disconnected_or_wrong_watershed_refused(self):
        for bad in ('connection','watershed'):
            network=copy.deepcopy(self.network)
            if bad=='connection':network['features'][1]['geometry']['coordinates'][0][0]+=.001
            else:network['features'][1]['properties']['WATERSHED_KEY']=123
            with self.assertRaises(ValueError):route.stitch(self.parent,network,[(1,2)])

    def test_duplicate_objects_and_duplicate_selected_edges_refused(self):
        network=copy.deepcopy(self.network);network['features'].append(network['features'][0])
        with self.assertRaises(ValueError):route.stitch(self.parent,network,[(1,2)])
        with self.assertRaises(ValueError):route.stitch(self.parent,self.network,[(1,1,2)])

    def test_inferred_connector_requires_explicit_bounded_original_anchor(self):
        network=copy.deepcopy(self.network)
        network['features'][0]['geometry']['coordinates'][0]=lonlat([[80,5]])[0].tolist()
        network['features'][1]['geometry']['coordinates'][0]=lonlat([[120,5]])[0].tolist()
        with self.assertRaisesRegex(ValueError,'Disconnected'):
            route.stitch(self.parent,network,[(1,2)])
        result,changes=route.stitch(self.parent,network,[(1,2)],{'1:2':[2]})
        receipt=changes[0]['inferred_connectors'][0]
        self.assertFalse(receipt['measured_geometry'])
        self.assertEqual(receipt['parent_via_vertices'],[2])
        self.assertEqual(receipt['between_objects'],[1,2])
        self.assertTrue(all(0<v<=250 for v in receipt['segment_lengths_m']))
        self.assertTrue(np.any(np.all(result==self.parent[2],axis=1)))
        for via in ([],[-1],[999],[2.0]):
            with self.assertRaisesRegex(ValueError,'original source vertices'):
                route.stitch(self.parent,network,[(1,2)],{'1:2':via})
        far_parent=self.parent.copy();far_parent[2]=lonlat([[100,-300]])[0]
        with self.assertRaisesRegex(ValueError,'local bound'):
            route.stitch(far_parent,network,[(1,2)],{'1:2':[2]})
        with self.assertRaisesRegex(ValueError,'Unused'):
            route.stitch(self.parent,self.network,[(1,2)],{'2:1':[2]})

    def test_overlap_and_reversed_progress_refused(self):
        with self.assertRaises(ValueError):route.stitch(self.parent,self.network,[(1,2),(1,2)])
        with self.assertRaises(ValueError):route.stitch(self.parent,self.network,[(2,1)])

    def test_projected_crs_and_outside_review_corridor_refused(self):
        network=copy.deepcopy(self.network);network['crs']=dict(properties=dict(name='EPSG:3157'))
        with self.assertRaises(ValueError):route.stitch(self.parent,network,[(1,2)])
        network=copy.deepcopy(self.network);distant=lonlat([[100,400]])[0].tolist()
        for f in network['features']:f['geometry']['coordinates'][0]=distant
        with self.assertRaisesRegex(ValueError,'corridor'):route.stitch(self.parent,network,[(1,2)])

    def test_lineage_reconstructs_and_rejects_changed_source_or_output(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(route,'REVIEWED_OBJECT_PATHS',((1,2),)):
            tmp=Path(tmp);parent=tmp/'parent.geojson';network=tmp/'network.geojson';out=tmp/'corrected.geojson'
            parent.write_text(json.dumps(geometry(self.parent)));network.write_text(json.dumps(self.network))
            receipt=route.build(parent,network,out)
            self.assertTrue(route.compatible_capture_route(out,route.sha(parent)))
            self.assertFalse(route.compatible_capture_route(out,'0'*64))
            self.assertTrue(route.compatible_capture_route(parent,route.sha(parent)))
            self.assertFalse(route.compatible_capture_route(parent,'0'*64))
            self.assertFalse(receipt['measured_banks'])
            parent_station=np.r_[0,np.cumsum(np.linalg.norm(np.diff(route.projected(self.parent),axis=0),axis=1))]
            anchors=[dict(id=str(i),lon_lat=self.parent[i].tolist(),terrain_route_station_m=parent_station[i]) for i in (0,4)]
            stationed=corrected_anchor_stationing(out,route.sha(parent),anchors,[])
            self.assertAlmostEqual(stationed['anchors'][0]['station_change_m'],0.)
            self.assertLess(stationed['anchors'][1]['station_change_m'],-80.)
            self.assertFalse(stationed['named_rapid_boundaries_established'])
            with self.assertRaisesRegex(ValueError,'different original route'):
                corrected_anchor_stationing(out,'0'*64,anchors,[])
            corrected_line=LineString(route.projected(route.route_points(json.loads(out.read_text()))))
            frame,policy=hydraulic_frame(corrected_line,route_planform_policy(out))
            self.assertTrue((np.diff(frame['source_station'])>=0).all())
            self.assertEqual(policy['chart_route']['sha256'],route.sha(parent))
            changed=route_planform_policy(out);changed['route_lineage_sha256']='0'*64
            with self.assertRaisesRegex(ValueError,'Changed'):
                hydraulic_frame(corrected_line,changed)
            saved=out.read_bytes();out.write_bytes(saved+b' ')
            with self.assertRaises(ValueError):route.lineage(out)
            out.write_bytes(saved);network.write_text('{}')
            with self.assertRaises(ValueError):route.lineage(out)


if __name__=='__main__':unittest.main()
