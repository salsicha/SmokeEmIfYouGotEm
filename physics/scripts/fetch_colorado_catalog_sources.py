"""Acquire bounded, hash-locked public USGS inputs for missing Colorado reaches.

This does not construct a map or certify a rapid. Point labels locate rapids;
the centerline does not measure their wet width or submerged obstacles. The
2021 profile is not a cross-section bathymetric survey. Preserve raw metadata
and distinguish these limits before reconstructing each reach.
"""
import argparse
import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError

BASE='https://grandcanyon.usgs.gov/server/rest/services/Basedata/GrandCanyonBaseLayers/MapServer'
PROFILE='https://www.sciencebase.gov/catalog/item/6859a0e6d4be024dfd7cac21?format=json'
RIGHTS='https://www.usgs.gov/data/continuous-and-high-resolution-profiles-water-surface-and-riverbed-elevation-282-miles'
MAX_BYTES=20*1024*1024  # no automatic hundred-megabyte raster/archive pulls


def read(url, limit=MAX_BYTES):
    for attempt in range(3):
        try:
            with urlopen(Request(url, headers={'User-Agent':'RaftSim-evidence-import/1.0'}),timeout=60) as response:
                data=response.read(limit+1)
            break
        except HTTPError as error:
            # Bounded retry of temporary upstream failures only. Never retry
            # authorization errors or reinterpret an HTML error as source data.
            if error.code not in (502,503,504) or attempt==2: raise
            time.sleep(attempt+1)
    if len(data)>limit: raise ValueError('Response exceeds the bounded source budget')
    return data


def validate_json(data):
    value=json.loads(data)
    if 'error' in value: raise ValueError(f'USGS API error: {value["error"]}')
    if value.get('exceededTransferLimit'): raise ValueError('Truncated geospatial response')
    return value


def acquire(out):
    if out.exists(): raise ValueError('Fresh source directory required; never overwrite captured evidence')
    out.mkdir(parents=True)
    receipts=[]

    def save(name,url,*,json_data=False,expected_md5=None,expected_size=None):
        data=read(url)
        value=validate_json(data) if json_data else None
        if expected_size is not None and len(data)!=expected_size: raise ValueError('Source size mismatch')
        if expected_md5 and hashlib.md5(data).hexdigest()!=expected_md5: raise ValueError('Source checksum mismatch')
        (out/name).write_bytes(data)
        receipts.append(dict(file=name,url=url,bytes=len(data),sha256=hashlib.sha256(data).hexdigest()))
        print(f'{name}: {len(data)} bytes',flush=True)
        return value

    profile=save('profile_release.json',PROFILE,json_data=True)
    for f in profile['files']:
        # Fetch the small profile and survey-control packages plus metadata;
        # record but do not silently download the 102 MB bathymetry archive.
        if f['size']>2*1024*1024: continue
        name=f['name']
        if Path(name).name!=name or '/' in name or '\\' in name: raise ValueError('Unsafe source filename')
        checksum=f.get('checksum',{})
        save(name,f['downloadUri'],expected_size=f['size'],
             expected_md5=checksum.get('value') if checksum.get('type')=='MD5' else None)
    for layer,name in ((4,'centerline'),(5,'rapid_points'),(3,'tenth_mile_points')):
        save(name+'_metadata.json',f'{BASE}/{layer}?f=pjson',json_data=True)
        url=f'{BASE}/{layer}/query?'+urlencode(dict(where='1=1',outFields='*',returnGeometry='true',outSR=6404,f='json',returnIdsOnly='true'))
        ids=save(name+'_ids.json',url,json_data=True)['objectIds']
        # Explicit object-id batches avoid both silent server limits and
        # unstable pagination. Raw responses retain the declared CRS.
        for index in range(0,len(ids),400):
            url=f'{BASE}/{layer}/query?'+urlencode(dict(objectIds=','.join(map(str,sorted(ids)[index:index+400])),
                outFields='*',returnGeometry='true',outSR=6404,f='json'))
            value=save(f'{name}_{index//400:03d}.json',url,json_data=True)
            if len(value.get('features',[]))!=min(400,len(ids)-index): raise ValueError('Missing requested features')
            crs=value.get('spatialReference',{})
            if crs.get('latestWkid',crs.get('wkid'))!=6404: raise ValueError('Unexpected coordinate reference system')
    manifest=dict(schema='raftsim.colorado_catalog_sources.v1',acquired_utc=datetime.now(timezone.utc).isoformat(),
        profile_release_doi='10.5066/P135FNFM',profile_rights='CC0 1.0 Universal',profile_rights_source=RIGHTS,
        centerline_authority='USGS Grand Canyon Monitoring and Research Center',
        centerline_rights_source='https://www.usgs.gov/data/colorado-river-mile-system-grand-canyon-arizona',
        centerline_release_doi='10.5066/P9IRL3GV',horizontal_crs='EPSG:6404 NAD83(2011) / Arizona Central metres',
        vertical_reference='Read individual profile metadata before using heights; no assumed NAVD88 conversion',
        limits=['Rapid labels are approximate points, not rapid boundaries or surveyed boulders.',
                'The river line is not a wet polygon or complete submerged-bed surface.',
                'Profile tables need coverage, interpolation and datum review before terrain construction.',
                'No playable map, verified flow variant or difficulty-class acceptance is implied.'],files=receipts)
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    return manifest


def acquire_bathymetry(source, out):
    """Explicit second-stage pull; never silently increase the first-stage budget."""
    if out.exists(): raise ValueError('Fresh bathymetry output required')
    captured=json.loads((source/'manifest.json').read_text(encoding='utf-8'))
    release_path=source/'profile_release.json'
    receipt=next(r for r in captured['files'] if r['file']=='profile_release.json')
    if hashlib.sha256(release_path.read_bytes()).hexdigest()!=receipt['sha256']:
        raise ValueError('Source release metadata checksum mismatch')
    release=json.loads(release_path.read_text(encoding='utf-8'))
    entry=next(f for f in release['files'] if f['name']=='bathymetry_rasters.7z')
    size=entry['size']
    if size>120*1024*1024: raise ValueError('Bathymetry archive exceeds explicit 120 MiB budget')
    checksum=entry.get('checksum',{})
    if checksum.get('type')!='MD5': raise ValueError('Expected publisher checksum is absent')
    data=read(entry['downloadUri'],limit=size)
    if len(data)!=size or hashlib.md5(data).hexdigest()!=checksum['value']:
        raise ValueError('Bathymetry download does not match publisher receipt')
    out.mkdir(parents=True)
    (out/entry['name']).write_bytes(data)
    manifest=dict(schema='raftsim.colorado_bathymetry_capture.v1',
        acquired_utc=datetime.now(timezone.utc).isoformat(),
        doi=captured['profile_release_doi'],rights=captured['profile_rights'],
        rights_source=captured['profile_rights_source'],url=entry['downloadUri'],
        file=entry['name'],bytes=size,sha256=hashlib.sha256(data).hexdigest(),
        publisher_md5=checksum['value'],
        limitation='Survey coverage must be measured after extraction; do not fill or relabel NoData as measured bed.')
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    print(f"{entry['name']}: {size} bytes; publisher checksum verified",flush=True)
    return manifest


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--bathymetry-from',type=Path,
        help='Explicitly acquire the bounded bathymetry archive using a previously captured release manifest')
    args=parser.parse_args()
    if args.bathymetry_from: acquire_bathymetry(args.bathymetry_from,args.out)
    else: acquire(args.out)
