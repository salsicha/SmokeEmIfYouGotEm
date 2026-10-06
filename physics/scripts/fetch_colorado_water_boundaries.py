"""Capture the USGS 2021 water polygons with bounded, audited downloads.

These are imagery-classified water boundaries, not submerged rock surveys,
rapid entry/exit bounds, or water boundaries measured at the game discharge.
"""
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

from fetch_colorado_catalog_sources import read, validate_json

ITEM = 'https://www.sciencebase.gov/catalog/item/67e6d69fd34ee3695ea1d846?format=json'
RIGHTS = 'https://www.usgs.gov/data/water-classification-colorado-river-corridor-grand-canyon-arizona-2021-data'
PREFIX = 'https://prod-is-usgs-sb-prod-publish.s3.amazonaws.com/67e6d69fd34ee3695ea1d846/'
# pyshp can stream without the optional SHX index. The release's SHX manager
# record is not published; do not substitute its HTML response for an index.
NEEDED = {'.shp', '.dbf', '.prj', '.cpg'}


def capture(out):
    if out.exists():
        raise ValueError('Fresh source directory required; preserve existing evidence')
    data = read(ITEM)
    release = validate_json(data)
    files = release.get('files', []) + [f for facet in release.get('facets', []) for f in facet.get('files', [])]
    selected = [f for f in files if Path(f['name']).suffix.lower() in NEEDED or f['name'].lower().endswith('.xml')]
    if {Path(f['name']).suffix.lower() for f in selected} != NEEDED | {'.xml'}:
        raise ValueError('Missing required source component or metadata')
    if len({f['name'].lower() for f in selected}) != len(selected):
        raise ValueError('Ambiguous source filenames')
    if sum(f['size'] for f in selected) > 160 * 1024 * 1024:
        raise ValueError('Source exceeds explicit 160 MiB download budget')
    out.mkdir(parents=True)
    (out/'release.json').write_bytes(data)
    receipts = []
    for f in selected:
        name = f['name']
        if Path(name).name != name or '/' in name or '\\' in name:
            raise ValueError('Unsafe source filename')
        # Published objects expose an explicit public S3 URI; the manager's
        # download endpoint can return an HTML sign-in page even for CC0 data.
        url = f.get('publishedS3Uri')
        if not url and f.get('published') and f.get('bucket') == 'prod-is-usgs-sb-prod-publish' and f.get('key') == '67e6d69fd34ee3695ea1d846/'+name:
            url = PREFIX+name  # explicit bucket/key from the same publisher record
        url = url or f.get('downloadUri') or f.get('url')
        if not url or not (url.startswith(PREFIX) or url.startswith('https://www.sciencebase.gov/catalog/file/get/67e6d69fd34ee3695ea1d846') or url.startswith('https://sciencebase.usgs.gov/manager/download/')):
            raise ValueError('Unexpected source host/path')
        count = 0
        sha, md5 = hashlib.sha256(), hashlib.md5()
        with urlopen(Request(url, headers={'User-Agent': 'RaftSim-evidence-import/1.0'}), timeout=60) as response, (out/(name+'.partial')).open('xb') as target:
            while chunk := response.read(1 << 20):
                count += len(chunk)
                if count > f['size']:
                    raise ValueError('Source exceeded declared size; incomplete capture retained')
                target.write(chunk)
                sha.update(chunk)
                md5.update(chunk)
        if count != f['size']:
            raise ValueError('Source size mismatch; incomplete capture retained')
        checksum = f.get('checksum') or {}
        if checksum.get('type') == 'MD5' and md5.hexdigest() != checksum['value']:
            raise ValueError('Publisher checksum mismatch')
        (out/(name+'.partial')).rename(out/name)
        receipts.append(dict(file=name, bytes=count, url=url, sha256=sha.hexdigest(),
                             publisher_checksum=checksum or None))
        print(f'{name}: {count} bytes', flush=True)
    manifest = dict(schema='raftsim.colorado_water_boundaries_capture.v1',
        acquired_utc=datetime.now(timezone.utc).isoformat(), source_doi='10.5066/P13SRUPW',
        rights='CC0 1.0 Universal', rights_url=RIGHTS, release_url=ITEM,
        release_sha256=hashlib.sha256(data).hexdigest(), files=receipts,
        scope='2021 imagery-derived water classification; consult captured metadata for acquisition, uncertainty and CRS',
        imagery_dates='2021-05-29 through 2021-06-04', dam_release_cms_approx=227,
        horizontal_crs='EPSG:6404', formal_accuracy_assessment=False,
        limitations=['Not submerged bed/rocks.', 'Not rapid bounds or a navigable route.',
                    'Dam release approximately 227 cms (~8016 cfs), close to the 8000 cfs target; tributaries cause local discharge variation.',
                    'Whitewater omissions and shadows were manually edited; 0.2 m imagery resolution is not a 0.2 m positional accuracy claim.'])
    (out/'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n', encoding='utf-8')
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    capture(parser.parse_args().out)
