"""Capture dated public orthophotos at guide-based rapid search locations.

An atlas entry is a search lead, never automatic confirmation of a rapid.
"""
from pathlib import Path
import sys
import json
import re
import hashlib
from urllib.request import urlopen
from urllib.parse import urlencode,urlparse
from concurrent.futures import ThreadPoolExecutor

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tmp/south-fork-geospatial-deps'))
from pyproj import Transformer
BASE=ROOT/'physics/data/real_world/south_fork_american_chili_bar/reconstruction_2026_09'
SERVICE='https://imagery.nationalmap.gov/arcgis/rest/services/USGSNAIPImagery/ImageServer/'


def fetch_json(url):
    with urlopen(url,timeout=60) as response: result=json.loads(response.read(10_000_000))
    if 'error' in result: raise ValueError(result['error'])
    return result


def acquire(feature):
    name=feature['properties']['label']
    slug=re.sub(r'[^a-z0-9]+','_',name.lower()).strip('_')
    out=BASE/'sources/rapid_atlas'/slug; out.mkdir(parents=True,exist_ok=True)
    done=out/'manifest.json'
    if done.exists(): return json.loads(done.read_text())
    point=feature['geometry']['coordinates']
    east,north=Transformer.from_crs(4326,32610,always_xy=True).transform(*point[:2])
    bbox=','.join(map(str,[east-260,north-260,east+260,north+260]))
    query=SERVICE+'query?'+urlencode({'geometry':bbox,'geometryType':'esriGeometryEnvelope','inSR':32610,
        'spatialRel':'esriSpatialRelIntersects','where':'Category=1','outFields':'*','returnGeometry':'false','f':'pjson'})
    catalog=fetch_json(query)
    if not catalog.get('features'): raise ValueError(f'No dated imagery: {name}')
    (out/'catalog.json').write_text(json.dumps(catalog,indent=2),encoding='utf-8')
    attrs=[f['attributes'] for f in catalog['features']]
    # Retain exactly the catalog's returned raster IDs. Metadata accompanies
    # imagery so mixed acquisition dates can never be labeled as one date.
    ids=[a['OBJECTID'] for a in attrs]
    mosaic={'mosaicMethod':'esriMosaicLockRaster','lockRasterIds':ids,'ascending':True,'mosaicOperation':'MT_FIRST'}
    url=SERVICE+'exportImage?'+urlencode({'bbox':bbox,'bboxSR':32610,'imageSR':32610,'size':'1024,1024',
        'format':'png','mosaicRule':json.dumps(mosaic),'f':'pjson'})
    export=fetch_json(url)
    href=export.get('href','')
    if urlparse(href).hostname!='imagery.nationalmap.gov': raise ValueError('Unexpected orthophoto export host')
    with urlopen(href,timeout=60) as response: image=response.read(20_000_001)
    if len(image)>20_000_000 or not image.startswith(b'\x89PNG'): raise ValueError('Invalid or oversized NAIP PNG')
    (out/'reference.png').write_bytes(image)
    (out/'export.json').write_text(json.dumps(export,indent=2),encoding='utf-8')
    report={'rapid':name,'status':'guide_location_search_reference_not_verified_rapid',
        'search_center_lon_lat':point,'image_path':(out/'reference.png').relative_to(ROOT).as_posix(),
        'image_sha256':hashlib.sha256(image).hexdigest(),'query_url':query,'export_url':url,
        'source_raster_ids':ids,'source_metadata':attrs,'actual_returned_extent':export['extent'],
        'production_promoted':False}
    done.write_text(json.dumps(report,indent=2),encoding='utf-8')
    return report


def main():
    features=json.loads((BASE/'survey_constrained_route_candidate.geojson').read_text())['features']
    features=[f for f in features if f['properties'].get('label')]
    output=BASE/'sources/rapid_atlas'; output.mkdir(exist_ok=True)
    records=[]; failures=[]
    def safe(feature):
        try:return acquire(feature)
        except Exception as error:return {'rapid':feature['properties']['label'],'error':str(error)}
    with ThreadPoolExecutor(max_workers=3) as pool:
        for record in pool.map(safe,features):
            (failures if 'error' in record else records).append(record)
            print(record['rapid'],record.get('status',record.get('error')),flush=True)
            (output/'index.json').write_text(json.dumps({'entries':records,'failures':failures},indent=2),encoding='utf-8')
    if failures: raise SystemExit(1)


if __name__=='__main__':main()
