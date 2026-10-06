"""Download spatially selected public USGS DEM tiles; preserve original units."""
from pathlib import Path
import sys
import json
import hashlib
import urllib.request
from urllib.parse import urlencode
import xml.etree.ElementTree as ET
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'physics/data/real_world/south_fork_american_chili_bar/reconstruction_2026_09'
PREFIX = 'StagedProducts/Elevation/OPR/Projects/CA_UpperSouthAmerican_Eldorado_2019_B19/CA_UpperSouthAmerican_Eldorado_2019/TIFF/USGS_OPR_CA_UpperSouthAmerican_Eldorado_2019_B19_'


def download(selection, output):
        tile_id = selection['attributes']['Tile_ID']
        url = 'https://prd-tnm.s3.amazonaws.com/?' + urlencode({'list-type': 2, 'prefix': PREFIX + tile_id, 'max-keys': 10})
        listing_path = output / f'{tile_id}.xml'
        if listing_path.exists():
            listing = listing_path.read_bytes()
        else:
            with urllib.request.urlopen(url, timeout=45) as response:
                listing = response.read()
            listing_path.write_bytes(listing)
        xml = ET.fromstring(listing)
        ns = {'s': 'http://s3.amazonaws.com/doc/2006-03-01/'}
        matches = [item for item in xml.findall('s:Contents', ns) if item.find('s:Key', ns).text.endswith('.tif')]
        if len(matches) != 1:
            raise ValueError(f'{tile_id}: expected one actual DEM, got {len(matches)}')
        key = matches[0].find('s:Key', ns).text
        size = int(matches[0].find('s:Size', ns).text)
        if size > 100_000_000:
            raise ValueError(f'{tile_id}: exceeds 100 MB per tile intake limit')
        target = output / Path(key).name
        source = 'https://prd-tnm.s3.amazonaws.com/' + key
        if not target.exists():
            with urllib.request.urlopen(source, timeout=60) as response:
                data = response.read(size + 1)
            if len(data) != size:
                raise ValueError(f'{tile_id}: incomplete download')
            target.write_bytes(data)
        data = target.read_bytes()
        if len(data) != size:
            raise ValueError(f'{tile_id}: cached size mismatch')
        return {'tile_id': tile_id, 'file': target.name, 'url': source,
                'bytes': size, 'sha256': hashlib.sha256(data).hexdigest(), 'leads': selection['leads']}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--full-reach', action='store_true')
    args = parser.parse_args()
    output = BASE / 'sources/dem'
    output.mkdir(exist_ok=True)
    selection_name = 'full-reach-lidar-tile-selection.json' if args.full_reach else 'lidar-tile-selection.json'
    report_name = 'full-reach-downloads.json' if args.full_reach else 'downloads.json'
    selections = json.loads((BASE / selection_name).read_text())
    records, failures = [], []
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {executor.submit(download, selection, output): selection for selection in selections}
        for future in as_completed(futures):
            try:
                record = future.result()
                records.append(record)
                print(f'{len(records)}/{len(selections)} {record["tile_id"]}: {record["bytes"]} bytes', flush=True)
            except Exception as exc:
                failures.append({'tile': futures[future]['attributes']['Tile_ID'], 'error': str(exc)})
                print(json.dumps(failures[-1]), flush=True)
            records.sort(key=lambda item: item['tile_id'])
            (output / report_name).write_text(json.dumps(records, indent=2), encoding='utf-8')
    (output / (report_name + '.failures.json')).write_text(json.dumps(failures, indent=2), encoding='utf-8')
    if failures:
        raise RuntimeError(f'{len(failures)} tiles failed; rerun to resume verified cached downloads')


if __name__ == '__main__':
    main()
