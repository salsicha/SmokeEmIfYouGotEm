"""Acquire the four already-indexed USGS source tiles for Chili Bar canopy.

Raw tile cache is local-only; immutable download receipts retain source URLs,
byte sizes and SHA256. No tree, ground or bathymetry inference is made here.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import urllib.request

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT/'physics/data/real_world/south_fork_american_chili_bar/reconstruction_2026_09'
TILES = ('10SFH896041', '10SFH896043', '10SFH898041', '10SFH898043')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cache', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    cache, report = args.cache.resolve(), args.report.resolve()
    if not cache.is_relative_to(ROOT/'tmp') or not report.is_relative_to(ROOT):
        raise ValueError('Project-local raw tmp cache and receipt required')
    if report.exists():
        raise FileExistsError('Preserve earlier receipts')
    index = BASE/'sources/point_cloud/usgs_laz_index.html'
    names = ['USGS_LPC_CA_UpperSouthAmerican_Eldorado_2019_B19_'+tile+'.laz' for tile in TILES]
    listing = index.read_text()
    if not all('href="'+name+'"' in listing for name in names):
        raise ValueError('Requested LAZ is absent from retained original index')
    parent = json.loads((BASE/'sources/point_cloud/downloads.json').read_text())[0]['url'].rsplit('/', 1)[0]
    if not parent.startswith('https://rockyweb.usgs.gov/vdelivery/Datasets/'):
        raise ValueError('Unexpected source host')
    cache.mkdir(parents=True, exist_ok=True)

    def fetch(pair):
        tile, name = pair
        path = cache/name
        receipt = path.with_suffix('.receipt.json')
        if path.exists() and receipt.exists():
            record = json.loads(receipt.read_text())
            with path.open('rb') as f:
                digest = hashlib.file_digest(f, 'sha256').hexdigest()
            if digest != record['sha256'] or path.stat().st_size != record['bytes']:
                raise ValueError('Cached source mismatch')
            return record
        if path.exists():
            raise FileExistsError('Unreceipted cache requires inspection, not overwrite')
        url = parent+'/'+name
        request = urllib.request.Request(url, headers={'User-Agent': 'RaftSim-source-reconstruction/1.0'})
        digest = hashlib.sha256()
        size = 0
        with urllib.request.urlopen(request, timeout=60) as response, path.open('xb') as output:
            expected = response.headers.get('Content-Length')
            if expected is not None and not 0 < int(expected) <= 400_000_000:
                raise ValueError('Source exceeds bounded tile intake')
            while chunk := response.read(1024*1024):
                size += len(chunk)
                if size > 400_000_000:
                    raise ValueError('Source exceeds bounded tile intake')
                digest.update(chunk)
                output.write(chunk)
            if size == 0 or (expected is not None and size != int(expected)):
                raise ValueError('Incomplete source download')
        record = dict(tile_id=tile, file=name, cache_path=str(path.relative_to(ROOT)).replace('\\', '/'),
            url=url, bytes=size, sha256=digest.hexdigest(),
            metadata_source='https://www.fisheries.noaa.gov/inport/item/66639')
        with receipt.open('x') as out:
            json.dump(record, out, indent=2)
        print(f'{tile}: {size} bytes, {record["sha256"]}', flush=True)
        return record

    with ThreadPoolExecutor(max_workers=2) as pool:
        records = list(pool.map(fetch, zip(TILES, names)))
    report.parent.mkdir(parents=True, exist_ok=True)
    with report.open('x') as out:
        json.dump(dict(schema='raftsim.chili_bar.lidar_intake.v1', sources=records,
            index_sha256=hashlib.sha256(index.read_bytes()).hexdigest(),
            raw_cache_local_only=True, measured_tree_inventory=False), out, indent=2)
        out.write('\n')


if __name__ == '__main__':
    main()
