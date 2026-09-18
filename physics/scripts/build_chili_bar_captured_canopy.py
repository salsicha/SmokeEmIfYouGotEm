"""Source-supported Chili Bar canopy, not a surveyed tree inventory.

Extract original classified returns in the retained NAIP footprint, then infer
crown centres with the same deterministic policy used at Troublemaker. Ground
roots come from the installed full-river coarse triangles, not the point cloud
or a bilinear raster. No terrain, water, collision, or source image is edited.
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from build_troublemaker_captured_canopy import image_pixels, separated_peaks
from south_fork_composite_terrain import sample_regular_triangles
from prepare_south_fork_canopy_placement import FORMS, PREFIX

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT/'physics/data/real_world/south_fork_american_chili_bar/reconstruction_2026_09'
OUT = BASE/'chili_bar/canopy_20260918'
INTAKE = BASE/'sources/point_cloud/chili_bar_downloads_20260918.json'
PHOTO = BASE/'sources/chili_bar_naip.png'
PHOTO_META = BASE/'sources/chili_bar_naip_export.json'


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def receipt(paths):
    return {p.relative_to(ROOT).as_posix(): sha(p) for p in paths}


def check_sources(record):
    for name, digest in record.items():
        path = (ROOT/name).resolve()
        if not path.is_relative_to(ROOT) or sha(path) != digest:
            raise ValueError('Captured source changed: '+name)


def green_pixels(rgb):
    rgb = np.asarray(rgb, float)
    return (rgb[..., 1] > 1.04*rgb[..., 0]) & (rgb[..., 1] > 1.10*rgb[..., 2])


def raster_samples(path, east, north, *, order, outside):
    import rasterio
    from scipy.ndimage import map_coordinates
    with rasterio.open(path) as ds:
        x, y = (~ds.transform)*(east, north)
        return map_coordinates(ds.read(1), [y-.5, x-.5], order=order,
                               mode='constant', cval=outside)


def extract():
    import laspy
    from pyproj import Transformer
    if (OUT/'classified_returns.npz').exists() or (OUT/'source.json').exists():
        raise FileExistsError('Preserve previous source extraction')
    intake = json.loads(INTAKE.read_text())
    bounds = json.loads(PHOTO_META.read_text())['extent']
    if bounds['spatialReference']['wkid'] != 32610:
        raise ValueError('Expected registered north-up UTM imagery')
    to_source = Transformer.from_crs(32610, 6418, always_xy=True)
    to_metric = Transformer.from_crs(6418, 32610, always_xy=True)
    box = to_source.transform_bounds(bounds['xmin'], bounds['ymin'], bounds['xmax'], bounds['ymax'])
    values = {key: [] for key in ('east_m', 'north_m', 'navd88_m', 'classification',
        'source_tile', 'source_record', 'native_xyz_integer')}
    headers = []
    for tile_id, source in enumerate(intake['sources']):
        path = (ROOT/source['cache_path']).resolve()
        if not path.is_relative_to(ROOT/'tmp') or sha(path) != source['sha256']:
            raise ValueError('Raw LAZ receipt mismatch')
        with laspy.open(path) as reader:
            crs = reader.header.parse_crs()
            horizontal = crs.sub_crs_list[0] if crs and crs.is_compound else crs
            if horizontal is None or horizontal.to_epsg() != 6418:
                raise ValueError('Unexpected original LAZ CRS')
            if not crs.is_compound or crs.sub_crs_list[1].to_epsg() != 6360:
                raise ValueError('Expected NAVD88 US survey foot vertical CRS')
            headers.append(dict(tile_id=source['tile_id'], original_crs_wkt=crs.to_wkt(),
                scales=reader.header.scales.tolist(), offsets=reader.header.offsets.tolist(),
                point_count=int(reader.header.point_count), source_sha256=source['sha256']))
            offset = 0
            for points in reader.chunk_iterator(1_000_000):
                x, y = np.asarray(points.x), np.asarray(points.y)
                take = ((x >= box[0]) & (x <= box[2]) & (y >= box[1]) & (y <= box[3])
                        & (np.asarray(points.withheld) == 0))
                ids = np.flatnonzero(take)
                if len(ids):
                    east, north = to_metric.transform(x[ids], y[ids])
                    inside = ((east >= bounds['xmin']) & (east < bounds['xmax'])
                              & (north > bounds['ymin']) & (north <= bounds['ymax']))
                    ids = ids[inside]
                    values['east_m'].append(east[inside])
                    values['north_m'].append(north[inside])
                    values['navd88_m'].append(np.asarray(points.z)[ids]*(1200/3937))
                    values['classification'].append(np.asarray(points.classification)[ids])
                    values['source_tile'].append(np.full(len(ids), tile_id, np.uint8))
                    values['source_record'].append(ids.astype(np.int64)+offset)
                    values['native_xyz_integer'].append(np.column_stack((points.X[ids], points.Y[ids], points.Z[ids])))
                offset += len(points)
        print('Extracted original returns:', source['tile_id'], flush=True)
    if not values['east_m']:
        raise ValueError('No original returns in source footprint')
    packed = {key: np.concatenate(parts) for key, parts in values.items()}
    if not len(packed['east_m']):
        raise ValueError('No original returns in source footprint')
    surface = BASE/'chili_bar/survey_surface_navd88_m.tif'
    water = BASE/'chili_bar/unknown_submerged_bed_mask.tif'
    ground = raster_samples(surface, packed['east_m'], packed['north_m'], order=1, outside=np.nan)
    packed['height_above_survey_surface_m'] = packed['navd88_m']-ground
    packed['survey_water_or_unknown'] = raster_samples(water, packed['east_m'], packed['north_m'], order=0, outside=255) != 0
    OUT.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(OUT/'classified_returns.npz', **packed)
    classes, counts = np.unique(packed['classification'], return_counts=True)
    result = dict(schema='raftsim.chili_bar.canopy_returns.v1',
        sources=receipt((INTAKE, PHOTO, PHOTO_META, surface, water)),
        extraction_script_sha256=sha(Path(__file__)), payload_sha256=sha(OUT/'classified_returns.npz'),
        return_count=len(ground), class_counts=dict(zip(map(str, classes), map(int, counts))),
        original_headers=headers, bounds_utm_m=bounds, horizontal_crs='EPSG:32610',
        vertical_datum='NAVD88', original_vertical_units='US survey feet (1200/3937 metres)',
        original_record_indices_and_integer_xyz_retained=True, withheld_returns_excluded=True,
        horizontal_registration='PROJ NAD83(2011) to WGS84; no local survey tie; metre-scale uncertainty remains',
        source_dates_coincident=False, bathymetry_measured=False, tree_inventory_surveyed=False)
    with (OUT/'source.json').open('x') as out:
        json.dump(result, out, indent=2)
        out.write('\n')
    print(json.dumps(dict(return_count=len(ground), class_counts=result['class_counts'])), flush=True)


def triangle_root_metrics(z, valid, water, x0, y0, cell, xy):
    """Retain source-domain roots with a conservative two-metre dry collar.

    Check every grid vertex and quad touched by a +/-2m XY square. Return
    indices instead of clamping queries into missing terrain or inferred bed.
    """
    if (z.ndim != 2 or water.shape != z.shape or valid.shape != (z.shape[0]-1,z.shape[1]-1)
            or valid.dtype != bool or not np.isfinite(cell) or cell <= 0
            or xy.ndim != 2 or xy.shape[1] != 2 or not np.isfinite(xy).all()):
        raise ValueError('Registered finite XY and matching terrain topology required')
    cf, rf = (xy[:, 0]-x0)/cell, (y0-xy[:, 1])/cell
    col, row = np.floor(cf).astype(int), np.floor(rf).astype(int)
    radius = int(np.ceil(2/cell))+1
    selected = np.flatnonzero((row >= radius) & (col >= radius)
        & (row+radius < valid.shape[0]) & (col+radius < valid.shape[1]))
    r, c = row[selected], col[selected]
    keep = np.ones(len(selected), bool)
    for dr in range(-radius, radius+1):
        for dc in range(-radius, radius+1):
            keep &= valid[r+dr, c+dc] & (water[r+dr, c+dc] == 0)
            keep &= np.isfinite(z[r+dr, c+dc])
    selected = selected[keep]
    r, c = row[selected], col[selected]
    u, v = cf[selected]-c, rf[selected]-r
    a, b, cc, d = z[r, c], z[r, c+1], z[r+1, c], z[r+1, c+1]
    east_slope = np.where(u+v <= 1, b-a, d-cc)/cell
    north_slope = np.where(u+v <= 1, a-cc, b-d)/cell
    up = 1/np.sqrt(1+east_slope**2+north_slope**2)
    keep = up >= .55
    selected = selected[keep]
    ground = sample_regular_triangles(z, x0, y0, cell, xy[selected, 0], xy[selected, 1])
    return selected, ground, up[keep]


def prepare():
    import rasterio
    from PIL import Image
    destination = OUT/'placement.json'
    if destination.exists():
        raise FileExistsError('Preserve earlier canopy placement')
    source_path = OUT/'source.json'
    source = json.loads(source_path.read_text())
    check_sources(source['sources'])
    # Alternate EPT metadata is durable; large raw provider nodes remain a
    # reproducible local cache. Verify all retained lineage/hierarchy records.
    for name, record in source.get('provider_sources', {}).items():
        if not name.startswith('ept-data/'):
            check_sources({record['file']: record['sha256']})
    point_path = OUT/'classified_returns.npz'
    if sha(point_path) != source['payload_sha256']:
        raise ValueError('Extracted original returns changed')
    with np.load(point_path, allow_pickle=False) as data:
        east, north, top, height, classes, wet = (data[key] for key in
            ('east_m', 'north_m', 'navd88_m', 'height_above_survey_surface_m', 'classification', 'survey_water_or_unknown'))
    bounds = source['bounds_utm_m']
    rgb = np.asarray(Image.open(PHOTO).convert('RGB'))
    ids = np.flatnonzero(~wet & np.isfinite(height) & (height >= 3.5) & (height <= 30)
                         & np.isin(classes, (1, 3, 4, 5)))
    rr, cc = image_pixels(east[ids], north[ids], bounds, rgb.shape)
    ids = ids[green_pixels(rgb[rr, cc])]
    ncols = int(np.ceil((bounds['xmax']-bounds['xmin'])/3))
    tile_c = np.floor((east[ids]-bounds['xmin'])/3).astype(int)
    tile_r = np.floor((north[ids]-bounds['ymin'])/3).astype(int)
    cells = tile_r*ncols+tile_c
    order = np.argsort(cells, kind='stable')
    groups = np.split(order, np.flatnonzero(np.diff(cells[order]))+1)
    candidates = []
    for group in groups:
        if len(group) >= 12:
            selected = ids[group]
            candidates.append((np.median(east[selected]), np.median(north[selected]),
                               np.quantile(top[selected], .9), len(selected), cells[group[0]]))
    if not candidates:
        raise ValueError('No supported canopy; no invented fallback scatter')
    candidates = np.asarray(candidates)
    rr, cc = image_pixels(candidates[:, 0], candidates[:, 1], bounds, rgb.shape)
    candidates = candidates[green_pixels(rgb[rr, cc])]
    extension = BASE/'full_reach/source_context_extension'
    manifest_path = extension/'manifest.json'
    manifest = json.loads(manifest_path.read_text())
    for name in ('coarse_bed_navd88_m.tif', 'unknown_submerged_bed_mask.tif', 'topology.npz'):
        if sha(extension/name) != manifest['artifacts'][name]:
            raise ValueError('Current terrain source changed: '+name)
    with rasterio.open(extension/'coarse_bed_navd88_m.tif') as ds:
        z = ds.read(1)
        transform, crs, grid_shape = ds.transform, ds.crs, ds.shape
        if (crs.to_epsg() != 32610 or list(ds.xy(0,0)) != manifest['grid']['first_vertex_utm_m']
                or transform.a != manifest['grid']['cell_m'] or transform.e != -transform.a
                or transform.b != 0 or transform.d != 0):
            raise ValueError('Terrain raster is not registered to its source grid')
    with rasterio.open(extension/'unknown_submerged_bed_mask.tif') as ds:
        if ds.transform != transform or ds.crs != crs or ds.shape != grid_shape:
            raise ValueError('Water mask is not registered to the terrain grid')
        water = ds.read(1)
    with np.load(extension/'topology.npz') as data:
        valid = data['valid_quads']
    x0, y0 = manifest['grid']['first_vertex_utm_m']
    selected, roots, up = triangle_root_metrics(z, valid, water, x0, y0,
                                               manifest['grid']['cell_m'], candidates[:, :2])
    candidates = candidates[selected]
    # The representative captured crown top stays at its source elevation;
    # the inferred trunk root follows the actual rendered triangle exactly.
    heights = candidates[:, 2]-roots
    good = (heights >= 3.5) & (heights <= 30)
    candidates, roots, heights, up = candidates[good], roots[good], heights[good], up[good]
    selected = separated_peaks(candidates[:, :2], heights)
    route_path = BASE/'full_reach/playable_route/coordinate_map.json'
    route = json.loads(route_path.read_text())
    if route['world_y_sign'] != -1 or route['horizontal_crs'] != 'EPSG:32610':
        raise ValueError('Unexpected playable world registration')
    origin, datum = route['origin_utm_m'], route['vertical_datum_m']
    instances = []
    for i in selected:
        ex, ny, top, count, source_cell = candidates[i]
        instances.append(dict(id=int(source_cell), world_root_cm=[float((ex-origin[0])*100),
            float((origin[1]-ny)*100), float((roots[i]-datum)*100)],
            utm_xy_m=[float(ex), float(ny)], root_navd88_m=float(roots[i]), crown_top_navd88_m=float(top),
            height_m=float(heights[i]), ground_normal_up=float(up[i]), support_return_count=int(count),
            yaw_degrees=float((int(round(ex*100))*17+int(round(ny*100))*31) % 360),
            form_index=int(source_cell) % 3, ground_authority='captured_dry_coarse_triangle'))
    if not instances:
        raise ValueError('No supported dry-ground instances')
    assets = []
    for form in FORMS:
        package = PREFIX+form
        assets.append(dict(package=package, sha256=sha(ROOT/'unreal/Content'/(package.removeprefix('/Game/')+'.uasset'))))
    dependencies = [source_path, point_path, PHOTO, PHOTO_META, manifest_path, route_path,
                    *(extension/name for name in ('coarse_bed_navd88_m.tif', 'unknown_submerged_bed_mask.tif', 'topology.npz'))]
    result = dict(schema='raftsim.chili_bar.captured_canopy_placement.v1',
        level='/Game/RaftSim/Maps/L_SouthForkAmerican_FullReach', scenario_id='south_fork_full_descent',
        sources=receipt(dependencies), builder_sha256=sha(Path(__file__)),
        origin_utm_m=origin, vertical_datum_m=datum, world_y_sign=-1,
        method='3m groups; >=12 non-withheld class 1/3/4/5 returns 3.5..30m above source ground; green pixels and centre; 90th-percentile crown top; conservative >=2m dry collar; original rendered triangles; slope normal.z>=.55; deterministic separated peaks',
        candidate_count=len(candidates), instance_count=len(instances), assets=assets, instances=instances,
        tree_inventory_surveyed=False, species_and_trunk_positions_measured=False,
        appearance='Existing project-authored live-oak family; species, form and trunk location inferred',
        source_dates_coincident=False, terrain_or_hydraulic_geometry_modified=False,
        collision='Visual canopy only; no verified solid tree collision',
        no_rapid_scenario=True, photoreal_accepted=False, normal_map_integrated=False)
    with destination.open('x') as out:
        json.dump(result, out, indent=2, allow_nan=False)
        out.write('\n')
    print(json.dumps(dict(instance_count=len(instances), placement_sha256=sha(destination))), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase', choices=('extract', 'prepare'))
    args = parser.parse_args()
    (extract if args.phase == 'extract' else prepare)()
