import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from capture_chilko_fwa_corridor import validate_collection,SCHEMA,WATERSHED,MAIN_WATERBODY
from chilko_planform import load_planform, retire_bar_footprints
from shapely.geometry import box


def feature(key,oid,x):
    return dict(type='Feature',properties=dict(WATERBODY_KEY=key,OBJECTID=oid,WATERSHED_KEY=WATERSHED,
        WATERSHED_GROUP_CODE='CHIR',WATERBODY_TYPE='R',FEATURE_CODE='GA24850000'),
        geometry=dict(type='Polygon',coordinates=[[[x,52],[x+.001,52],[x+.001,52.001],[x,52.001],[x,52]]]))


class PlanformTests(unittest.TestCase):
    def test_retirement_preserves_active_channel_and_unreviewed_ground(self):
        source=box(400000,5700000,401000,5701000)
        active=box(400450,5700000,400490,5701000)
        review=box(400200,5700200,400800,5700800)
        evidence=dict(observation_crs='EPSG:3157',observations=[dict(inspection_bounds_m=list(review.bounds))])
        result=retire_bar_footprints(source,active,evidence)
        self.assertTrue(result.covers(active))
        self.assertTrue(result.difference(source).is_empty)
        self.assertTrue(source.difference(result).difference(review).is_empty)
        self.assertAlmostEqual(source.area-result.area,review.difference(active).area)
        self.assertTrue(result.equals(source.difference(review.difference(active))))

    def test_retirement_does_not_create_water_outside_source(self):
        source=box(400000,5700000,401000,5701000)
        active=box(400450,5699900,400490,5701100)
        evidence=dict(observation_crs='EPSG:3157',observations=[dict(inspection_bounds_m=list(source.bounds))])
        self.assertTrue(retire_bar_footprints(source,active,evidence).equals(source.intersection(active)))

    def setUp(self):
        self.data=dict(type='FeatureCollection',features=[feature(MAIN_WATERBODY,1,-124),feature(2,2,-124.01)])

    def test_disconnected_mapped_branch_retained(self):
        p=validate_collection(self.data,[MAIN_WATERBODY,2])
        self.assertEqual(p.geom_type,'MultiPolygon')
        self.assertEqual(len(p.geoms),2)

    def test_incomplete_duplicate_or_other_watershed_is_not_accepted(self):
        for change in ('missing','duplicate','other','partial','invalid'):
            d=copy.deepcopy(self.data)
            if change=='missing':d['features'].pop()
            if change=='duplicate':d['features'].append(copy.deepcopy(d['features'][0]))
            if change=='other':d['features'][1]['properties']['WATERSHED_KEY']=123
            if change=='partial':d['exceededTransferLimit']=True
            if change=='invalid':
                ring=d['features'][1]['geometry']['coordinates'][0]
                ring[1],ring[2]=ring[2],ring[1]  # Self-intersecting bow tie, not a merely large valid polygon.
            with self.subTest(change=change),self.assertRaises(ValueError):validate_collection(d,[MAIN_WATERBODY,2])

    def test_loader_binds_collection_to_route_and_original_bytes(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'river.geojson';route=Path(folder)/'route.geojson'
            route.write_text('test route');raw=json.dumps(self.data).encode();path.write_bytes(raw)
            meta=dict(schema=SCHEMA,horizontal_crs='EPSG:4326',sha256=hashlib.sha256(raw).hexdigest(),
                watershed_key=WATERSHED,main_waterbody_key=MAIN_WATERBODY,selected_count=2,object_ids=[1,2],
                waterbody_keys=[MAIN_WATERBODY,2],route=str(route),route_sha256=hashlib.sha256(route.read_bytes()).hexdigest())
            path.with_suffix('.json').write_text(json.dumps(meta))
            self.assertTrue(load_planform(path,route).is_valid)
            route.write_text('changed')
            with self.assertRaisesRegex(ValueError,'different route'):load_planform(path,route)
            path.write_bytes(raw+b' ')
            with self.assertRaisesRegex(ValueError,'bytes'):load_planform(path,route)

    def test_original_single_body_capture_remains_compatible(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'river.geojson';d=dict(type='FeatureCollection',features=self.data['features'][:1])
            raw=json.dumps(d).encode();path.write_bytes(raw)
            path.with_suffix('.json').write_text(json.dumps(dict(schema='raftsim.chilko_fwa_polygon_capture.v1',
                horizontal_crs='EPSG:4326',sha256=hashlib.sha256(raw).hexdigest(),waterbody_key=MAIN_WATERBODY)))
            self.assertEqual(load_planform(path).geom_type,'Polygon')


if __name__=='__main__':unittest.main()
