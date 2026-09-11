"""Fetch only the original classified LAZ tile containing the imaged crux."""
import io
import json
import sys
import zipfile
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urljoin
from urllib.request import urlopen
import hashlib
import re

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tmp/south-fork-geospatial-deps'))
import shapefile
from shapely.geometry import shape, Point
from shapely.ops import transform
from pyproj import Transformer

BASE = ROOT / 'physics/data/real_world/south_fork_american_chili_bar/reconstruction_2026_09'
URL = 'https://rockyweb.usgs.gov/vdelivery/Datasets/Staged/Elevation/LPC/Projects/CA_UpperSouthAmerican_Eldorado_2019_B19/CA_UpperSouthAmerican_Eldorado_2019/LAZ/'


class Links(HTMLParser):
    def __init__(self):
        super().__init__(); self.links = []
    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            self.links.extend(value for key, value in attrs if key == 'href')


def main():
    features = json.loads((BASE / 'corrected_route_candidate.geojson').read_text())['features']
    control = next(f for f in features if f.get('id') == 'troublemaker_crux_search')
    point = Point(control['properties']['metric_xy'])
    tiles = []
    with zipfile.ZipFile(BASE / 'sources/eldorado_2019_tile_index.zip') as archive:
        names = archive.namelist()
        reader = shapefile.Reader(shp=io.BytesIO(archive.read(next(n for n in names if n.endswith('.shp')))),
                                  dbf=io.BytesIO(archive.read(next(n for n in names if n.endswith('.dbf')))))
        project = Transformer.from_crs(archive.read(next(n for n in names if n.endswith('.prj'))).decode(), 32610, always_xy=True)
        for item in reader.iterShapeRecords():
            geom = transform(project.transform, shape(item.shape.__geo_interface__))
            if geom.distance(point) < 80:
                tiles.append(item.record.as_dict()['Tile_ID'])
    out = BASE / 'sources/point_cloud'
    out.mkdir(exist_ok=True)
    listing_path = out / 'usgs_laz_index.html'
    if not listing_path.exists():
        with urlopen(URL, timeout=60) as response:
            listing_path.write_bytes(response.read(10_000_000))
    parser = Links(); parser.feed(listing_path.read_text())
    records = []
    for tile in tiles:
        matches = [link for link in parser.links if tile in link and link.lower().endswith('.laz')]
        if len(matches) != 1:
            raise ValueError(f'{tile}: expected one source LAZ link, found {len(matches)}')
        url = urljoin(URL, matches[0])
        filename = Path(matches[0]).name
        size_match=re.search(re.escape(matches[0])+r'[^\n]*?\s(\d+)\s*(?:\n|$)',listing_path.read_text())
        if not size_match:
            raise ValueError(f'No authoritative listing size for {filename}')
        expected_size=int(size_match.group(1))
        if expected_size>300_000_000:
            raise ValueError('Selected source tile exceeds the 300 MB per-file acquisition budget')
        target = out / filename
        if not target.exists():
            print('Downloading', url, flush=True)
            temporary=out/(filename+'.partial')
            with urlopen(url, timeout=60) as response:
                received=0
                with temporary.open('wb') as stream:
                    while True:
                        chunk=response.read(8_000_000)
                        if not chunk: break
                        received+=len(chunk)
                        if received>expected_size: raise ValueError('LAZ exceeds published size')
                        stream.write(chunk)
                        print(f'{tile}: {received}/{expected_size} bytes',flush=True)
            if received!=expected_size: raise ValueError('Incomplete LAZ download')
            temporary.replace(target)
        data = target.read_bytes()
        if len(data)!=expected_size: raise ValueError('Cached LAZ differs from authoritative listing size')
        record = {'tile_id': tile, 'file': filename, 'url': url, 'bytes': len(data),
                  'sha256': hashlib.sha256(data).hexdigest(),
                  'metadata_source': 'https://www.fisheries.noaa.gov/inport/item/66639'}
        records.append(record)
        (out / 'downloads.json').write_text(json.dumps(records, indent=2), encoding='utf-8')
        print(json.dumps(record), flush=True)


if __name__ == '__main__':
    main()
