"""Full-resolution, bounded crop of the provider's alternate EPT delivery.

EPT is additive: retain EVERY overlapping ancestor and leaf, without a depth
or density shortcut. The original large-tile download remains independent.
Provider-node ordinals are retained, not falsely called original LAS ordinals.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import http.client
import json
from pathlib import Path
import time
import urllib.error
import urllib.request

import numpy as np

from build_chili_bar_captured_canopy import BASE, OUT, PHOTO, PHOTO_META, ROOT, raster_samples, receipt, sha
from fetch_chili_bar_canopy_lidar import TILES

URL = 'https://usgs-lidar-public.s3.amazonaws.com/CA_UpperSouthAmerican_Eldorado_2019'


def node_bounds(key, bounds):
    depth, *indices = map(int, key.split('-'))
    if depth < 0 or depth > 30 or len(indices) != 3 or any(i < 0 or i >= 2**depth for i in indices):
        raise ValueError('Invalid provider octree node')
    bounds = np.asarray(bounds, float)
    size = (bounds[3:]-bounds[:3])/2**depth
    lower = bounds[:3]+size*np.asarray(indices)
    return np.r_[lower, lower+size]


def overlaps_xy(key, bounds, crop):
    box = node_bounds(key, bounds)
    return bool(box[0] <= crop[2] and box[3] >= crop[0] and box[1] <= crop[3] and box[4] >= crop[1])


def collect_nodes(load, bounds, crop):
    pending, visited, nodes = ['0-0-0-0'], set(), {}
    while pending:
        root = pending.pop()
        if root in visited:
            raise ValueError('Repeated hierarchy subtree')
        visited.add(root)
        page = load(root)
        if root not in page or page[root] <= 0:
            raise ValueError('Unresolved hierarchy subtree')
        for key, count in page.items():
            if not overlaps_xy(key, bounds, crop):
                continue
            if type(count) is not int or count == 0 or count < -1:
                raise ValueError('Invalid hierarchy point count')
            if count == -1:
                pending.append(key)
            elif key in nodes:
                raise ValueError('Duplicate EPT data node')
            else:
                nodes[key] = count
        if len(nodes) > 10000 or len(visited) > 1000:
            raise ValueError('Crop exceeds bounded source intake')
    return nodes


def main():
    import laspy
    from pyproj import CRS, Transformer
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cache', type=Path, required=True)
    args = parser.parse_args()
    cache = args.cache.resolve()
    if not cache.is_relative_to(ROOT/'tmp'):
        raise ValueError('EPT cache must be project-local tmp')
    if (OUT/'source.json').exists() or (OUT/'classified_returns.npz').exists():
        raise FileExistsError('Preserve prior extraction')
    evidence = OUT/'ept_sources'
    evidence.mkdir(parents=True, exist_ok=True)
    records = {}

    def acquire(relative, durable=False):
        path = (evidence if durable else cache)/relative
        path.parent.mkdir(parents=True, exist_ok=True)
        stamp = path.with_suffix(path.suffix+'.receipt.json')
        url = URL+'/'+relative
        if path.exists():
            if not stamp.exists():
                raise FileExistsError('Inspect unreceipted source instead of overwriting: '+str(path))
            record = json.loads(stamp.read_text())
            if record['url'] != url or record['sha256'] != sha(path) or record['bytes'] != path.stat().st_size:
                raise ValueError('Cached provider source changed')
        else:
            request = urllib.request.Request(url, headers={'User-Agent': 'RaftSim-source-reconstruction/1.0'})
            for attempt in range(3):
                try:
                    with urllib.request.urlopen(request, timeout=45) as response:
                        payload = response.read(64_000_001)
                        expected = response.headers.get('Content-Length')
                    if expected is not None and len(payload) != int(expected):
                        raise http.client.IncompleteRead(payload,int(expected)-len(payload))
                    break
                except (urllib.error.URLError,TimeoutError,ConnectionError,http.client.IncompleteRead,http.client.RemoteDisconnected):
                    if attempt == 2:
                        raise
                    time.sleep(attempt+1)
            if not payload or len(payload) > 64_000_000:
                raise ValueError('Unexpected provider node size')
            if relative.endswith('.laz') and payload[:4] != b'LASF':
                raise ValueError('Provider did not return LAS data')
            with path.open('xb') as stream:
                stream.write(payload)
            record = dict(url=url, sha256=hashlib.sha256(payload).hexdigest(), bytes=len(payload),
                          file=path.relative_to(ROOT).as_posix())
            with stamp.open('x') as stream:
                json.dump(record, stream, indent=2)
        records[relative] = record
        return path

    metadata_path = acquire('ept.json', True)
    meta = json.loads(metadata_path.read_text())
    if meta['dataType'] != 'laszip' or meta['hierarchyType'] != 'json' or meta['srs']['horizontal'] != '3857':
        raise ValueError('Unexpected EPT delivery format')
    # Preserve the provider's original-file CRS and explicit reprojection chain.
    # Z bounds prove the foot->metre unit conversion, with no vertical shift.
    lineage = []
    for tile in TILES:
        name = 'USGS_LPC_CA_UpperSouthAmerican_Eldorado_2019_B19_'+tile
        path = acquire('ept-sources/'+name+'.json', True)
        info = json.loads(path.read_text())
        original = info['metadata']['readers.las']
        crs = CRS.from_wkt(original['comp_spatialreference'])
        if not crs.is_compound or [c.to_epsg() for c in crs.sub_crs_list] != [6418, 6360]:
            raise ValueError('Unexpected original survey datum')
        for endpoint, bound in [('minz', 2), ('maxz', 5)]:
            if abs(original[endpoint]*(1200/3937)-info['bounds'][bound]) > .002:
                raise ValueError('Provider vertical conversion is not the documented unit conversion')
        if info['pipeline'][1:] != [dict(out_srs='EPSG:3857', type='filters.reprojection')]:
            raise ValueError('Unexpected source processing')
        lineage.append(info['path'])
    footprint = json.loads(PHOTO_META.read_text())['extent']
    if footprint['spatialReference']['wkid'] != 32610:
        raise ValueError('Expected UTM source imagery')
    project = Transformer.from_crs(32610, 3857, always_xy=True)
    crop = project.transform_bounds(*(footprint[k] for k in ('xmin','ymin','xmax','ymax')))
    to_metric = Transformer.from_crs(3857, 32610, always_xy=True)
    def hierarchy(key):
        return json.loads(acquire('ept-hierarchy/'+key+'.json', True).read_text())
    nodes = collect_nodes(hierarchy, meta['bounds'], crop)
    if sum(nodes.values()) > 100_000_000:
        raise ValueError('Full-resolution crop exceeds bounded point intake')
    names = sorted(nodes, key=lambda key: tuple(map(int, key.split('-'))))
    print(f'Full-resolution crop: {len(names)} nodes, {sum(nodes.values())} source points before exact crop', flush=True)
    def fetch(key):
        path = acquire('ept-data/'+key+'.laz')
        print('Fetched', key, path.stat().st_size, flush=True)
        return path
    with ThreadPoolExecutor(max_workers=4) as pool:
        paths = list(pool.map(fetch, names))
    values = {key: [] for key in ('east_m','north_m','navd88_m','classification','source_node',
        'source_record','provider_xyz_integer','gps_time','point_source_id')}
    headers = []
    for index, (key, path) in enumerate(zip(names, paths)):
        data = laspy.read(path)
        if len(data) != nodes[key]:
            raise ValueError('Provider hierarchy/data point count mismatch')
        crs = data.header.parse_crs()
        if crs is None or crs.to_epsg() != 3857:
            raise ValueError('Provider node coordinate reference differs from metadata')
        headers.append(dict(node=key, scales=data.header.scales.tolist(), offsets=data.header.offsets.tolist()))
        ex, ny = to_metric.transform(np.asarray(data.x), np.asarray(data.y))
        mask = ((ex >= footprint['xmin']) & (ex < footprint['xmax']) & (ny > footprint['ymin'])
                & (ny <= footprint['ymax']) & (np.asarray(data.withheld) == 0))
        ids = np.flatnonzero(mask)
        if not len(ids):
            continue
        values['east_m'].append(ex[ids]); values['north_m'].append(ny[ids])
        values['navd88_m'].append(np.asarray(data.z)[ids])
        values['classification'].append(np.asarray(data.classification)[ids])
        values['source_node'].append(np.full(len(ids), index, np.uint16))
        values['source_record'].append(ids.astype(np.uint32))
        values['provider_xyz_integer'].append(np.column_stack((data.X[ids],data.Y[ids],data.Z[ids])))
        values['gps_time'].append(np.asarray(data.gps_time)[ids])
        values['point_source_id'].append(np.asarray(data.point_source_id)[ids])
        if index % 100 == 0:
            print('Extracted node',index+1,'of',len(names),flush=True)
    if not values['east_m']:
        raise ValueError('No provider returns in source footprint')
    packed = {key: np.concatenate(parts) for key, parts in values.items()}
    del values
    surface = BASE/'chili_bar/survey_surface_navd88_m.tif'
    water = BASE/'chili_bar/unknown_submerged_bed_mask.tif'
    ground = raster_samples(surface, packed['east_m'], packed['north_m'], order=1, outside=np.nan)
    packed['height_above_survey_surface_m'] = packed['navd88_m']-ground
    packed['survey_water_or_unknown'] = raster_samples(water, packed['east_m'], packed['north_m'], order=0, outside=255) != 0
    dry_ground = (packed['classification'] == 2) & ~packed['survey_water_or_unknown'] & np.isfinite(ground)
    errors = packed['height_above_survey_surface_m'][dry_ground]
    if len(errors) < 10000 or abs(np.median(errors)) > .5 or np.quantile(abs(errors), .95) > 2:
        raise ValueError('Provider ground disagrees with retained survey; investigate datum before placement')
    np.savez_compressed(OUT/'classified_returns.npz', **packed)
    counts = np.unique(packed['classification'], return_counts=True)
    result = dict(schema='raftsim.chili_bar.canopy_returns.v1', sources=receipt((PHOTO,PHOTO_META,surface,water,metadata_path)),
        extraction_script_sha256=sha(Path(__file__)), payload_sha256=sha(OUT/'classified_returns.npz'),
        return_count=len(ground), class_counts=dict(zip(map(str,counts[0]),map(int,counts[1]))),
        bounds_utm_m=footprint, horizontal_crs='EPSG:32610', vertical_datum='NAVD88',
        delivery='USGS EPT: same survey, provider-reprojected and millimetre-quantized; NOT original LAS integer coordinates',
        provider_url=URL, provider_sources=records, original_source_lineage=lineage, provider_node_headers=headers,
        full_resolution_all_overlapping_ancestor_and_leaf_nodes=True,
        source_node_and_record_indices_retained=True, original_record_indices_and_integer_xyz_retained=False,
        withheld_returns_excluded=True, source_dates_coincident=False, tree_inventory_surveyed=False,
        bathymetry_measured=False, raw_provider_nodes_local_only=True,
        vertical_authority='Original EPSG:6360 NAVD88 survey feet; provider lineage/bounds confirm conversion to metres, no fitted offset',
        dry_ground_comparison=dict(count=len(errors), median_m=float(np.median(errors)), absolute_p95_m=float(np.quantile(abs(errors),.95))),
        horizontal_registration='Provider EPSG:3857 to EPSG:32610; no local survey tie; metre-scale uncertainty remains')
    with (OUT/'source.json').open('x') as stream:
        json.dump(result, stream, indent=2); stream.write('\n')
    print(json.dumps(dict(return_count=len(ground), dry_ground_comparison=result['dry_ground_comparison'])), flush=True)


if __name__ == '__main__':
    main()
