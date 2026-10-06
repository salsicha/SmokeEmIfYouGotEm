"""Crop classified 2021 water polygons without inventing bank/rock elevations.

One-metre masks share the pool-bed crop grid. False means not classified as
water, NOT surveyed dry ground. Widths are water-intersection observations,
not boat clearances, successful-route widths or rapid difficulty grades.
"""
import argparse
import hashlib
import json
import math
import re
from pathlib import Path

import numpy as np
import shapefile
from pyproj import CRS
from rasterio.features import rasterize
from rasterio.transform import from_origin
from shapely.geometry import LineString, Point, box, mapping, shape
from shapely.ops import unary_union, clip_by_rect
from shapely.validation import explain_validity, make_valid


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def width_observation(water, x, y, tangent_x, tangent_y, half_span=250.):
    norm = math.hypot(tangent_x, tangent_y)
    if norm < 1e-8:
        raise ValueError('Degenerate profile tangent')
    lx, ly = -tangent_y/norm, tangent_x/norm
    transect = LineString([(x-half_span*lx, y-half_span*ly), (x+half_span*lx, y+half_span*ly)])
    cut = water.intersection(transect)
    lines = [cut] if cut.geom_type == 'LineString' else [g for g in getattr(cut, 'geoms', []) if g.geom_type == 'LineString']
    center = Point(x, y)
    containing = [g for g in lines if g.distance(center) < 1e-6]
    intervals = sorted([sorted(((p[0]-x)*lx+(p[1]-y)*ly for p in (g.coords[0], g.coords[-1]))) for g in lines if not g.is_empty])
    truncated = any(abs(v) >= half_span-1e-6 for interval in intervals for v in interval)
    return dict(classified_water_intervals_lateral_m=intervals,
                center_in_classified_water=water.covers(center),
                center_channel_width_m=containing[0].length if len(containing) == 1 and not truncated else None,
                total_classified_water_width_m=sum(g.length for g in lines),
                transect_truncated=truncated)


def valid_polygon(polygon):
    """Explicit topology-only repair; no buffering, dilation or island fill."""
    if polygon.is_valid:
        return polygon, None
    fixed = make_valid(polygon)
    components = [fixed] if fixed.geom_type in ('Polygon', 'MultiPolygon') else [
        g for g in fixed.geoms if g.geom_type in ('Polygon', 'MultiPolygon')]
    fixed = unary_union(components)
    delta = abs(fixed.area-polygon.area)
    # Self-touching raster-cell rings occur in the published shapes. Refuse
    # any repair that measurably changes area, rather than erasing islands.
    if not fixed.is_valid or fixed.is_empty or delta > 1e-4:
        raise ValueError('Source topology repair changes water area; manual review required')
    return fixed, dict(reason=explain_validity(polygon), area_before_m2=polygon.area,
                       area_after_m2=fixed.area, area_delta_m2=delta,
                       method='Shapely make_valid; retain polygon components, no buffering')


def extract(source, windows, out, names=(), margin_m=80):
    if out.exists():
        raise ValueError('Fresh water-crop output required')
    manifest = json.loads((source/'manifest.json').read_text(encoding='utf-8'))
    for receipt in manifest['files']:
        path = source/receipt['file']
        if path.stat().st_size != receipt['bytes'] or sha(path) != receipt['sha256']:
            raise ValueError('Captured source checksum mismatch: '+str(path))
    base = source/'WaterClassification_GC_2021'
    if CRS.from_wkt(base.with_suffix('.prj').read_text()).to_epsg() != 6404:
        raise ValueError('Unexpected water-polygon CRS')
    index = json.loads((windows/'index.json').read_text(encoding='utf-8'))
    definitions, clips, boxes = [], [], []
    from extract_colorado_bed_windows import crop_bounds, selected_windows
    for entry in selected_windows(index,names):
        key = re.sub(r'[^a-z0-9]+', '_', entry['name'].lower()).strip('_')
        definition = json.loads((windows/(key+'.json')).read_text(encoding='utf-8'))
        bbox = crop_bounds(definition['bounds_epsg6404'],margin_m)
        if (bbox[2]-bbox[0])*(bbox[3]-bbox[1]) > 8_000_000:
            raise ValueError('Water crop exceeds memory budget')
        definitions.append((key, definition, bbox)); boxes.append(box(*bbox)); clips.append([])
    # No SHX required. Process one shape at a time; the mainstem may be large.
    reader = shapefile.Reader(shp=str(base.with_suffix('.shp')), dbf=str(base.with_suffix('.dbf')), encoding='utf-8')
    if len(reader) != 30571:
        raise ValueError('Polygon count disagrees with captured publisher metadata')
    counts = [0]*len(boxes)
    repairs = []
    for record_index, record in enumerate(reader.iterShapeRecords()):
        if record.record.as_dict().get('Channel') != 'Colorado River':
            continue
        envelope = box(*record.shape.bbox)
        selected = [i for i, b in enumerate(boxes) if b.intersects(envelope)]
        if not selected:
            continue
        polygon = shape(record.shape.__geo_interface__)
        for i in selected:
            # The mainstem has millions of vertices. Clip the coordinate
            # rings first, then validate the SMALL derived geometry. A full
            # topological overlay per window needlessly processes 450 km.
            clipped = clip_by_rect(polygon, *boxes[i].bounds)
            if not clipped.is_empty and clipped.area > 0:
                clipped, repair = valid_polygon(clipped)
                if repair:
                    repairs.append(dict(source_record_index=record_index, window=definitions[i][0], **repair))
                    print(f"Explicit crop topology repair: record {record_index}, window={definitions[i][0]}, area change={repair['area_delta_m2']:.9g} m2", flush=True)
                clips[i].append(clipped); counts[i] += 1
    reader.close()
    out.mkdir(parents=True)
    receipts = []
    for i, (key, definition, bbox) in enumerate(definitions):
        if not clips[i]:
            raise ValueError('No classified Colorado water in '+key)
        water = unary_union(clips[i])
        x0, y0, x1, y1 = bbox
        transform = from_origin(x0, y1, 1., 1.)
        mask = rasterize([(mapping(water), 1)], out_shape=(y1-y0, x1-x0), transform=transform,
                         fill=0, all_touched=False, dtype='uint8').astype(bool)
        np.savez_compressed(out/(key+'.npz'), classified_water_mask=mask,
                            corner_east_north_m=np.array((x0, y1)), cell_m=np.array((1., 1.)))
        geometry_file = key+'.geojson'
        (out/geometry_file).write_text(json.dumps(dict(type='FeatureCollection',
            crs=dict(type='name', properties=dict(name='urn:ogc:def:crs:EPSG::6404')),
            features=[dict(type='Feature', properties=dict(source_doi=manifest['source_doi'],
                evidence='2021 imagery-classified water'), geometry=mapping(water))]),
            separators=(',', ':'), allow_nan=False)+'\n', encoding='utf-8')
        samples = definition['samples']
        widths = []
        for j, sample in enumerate(samples):
            a, b = samples[max(0, j-1)], samples[min(len(samples)-1, j+1)]
            widths.append(dict(station_m=sample['local_arc_station_m'],
                **width_observation(water, sample['easting'], sample['northing'],
                                    b['easting']-a['easting'], b['northing']-a['northing'])))
        product = dict(name=definition['name'], file=key+'.npz', geometry_file=geometry_file,
            bbox_epsg6404=bbox, shape=list(mask.shape), classified_water_cells=int(mask.sum()),
            contributing_source_polygons=counts[i], centerline_samples_in_water=sum(w['center_in_classified_water'] for w in widths),
            profile_sample_count=len(widths), widths=widths,
            files_sha256={p: sha(out/p) for p in (key+'.npz', geometry_file)})
        receipts.append(product)
        print(f"{product['name']}: {int(mask.sum())} classified water cells; "
              f"centre samples inside={product['centerline_samples_in_water']}/{len(widths)}", flush=True)
    result = dict(schema='raftsim.colorado_classified_water_windows.v1',
        source_doi=manifest['source_doi'], rights=manifest['rights'], rights_url=manifest['rights_url'],
        source_manifest_sha256=sha(source/'manifest.json'), construction_index_sha256=sha(windows/'index.json'),
        horizontal_crs='EPSG:6404', imagery_dates=manifest['imagery_dates'],
        dam_release_cms_approx=227, formal_accuracy_assessment=False,
        derived_geometry_topology_repairs=repairs,
        limitations=['False mask values are not classified water, not proof of dry terrain.',
                    'Cut boundaries are construction margins; endpoint width observations may be clipped.',
                    'No underwater geometry or hazard height can be inferred from a water hole alone.',
                    'Water widths are not navigable widths or validated boat routes.'],
        construction_margin_m=margin_m,playable_maps_created=0, windows=receipts)
    (out/'manifest.json').write_text(json.dumps(result, indent=2, allow_nan=False)+'\n', encoding='utf-8')
    return result


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source', type=Path, required=True)
    p.add_argument('--windows', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--names',nargs='*',default=[])
    p.add_argument('--margin-m',type=int,default=80)
    a = p.parse_args()
    extract(a.source, a.windows, a.out,a.names,a.margin_m)
