"""Reconstruct georeferenced route, DEM and hydro-boundaries from captured data.

Produces a separate candidate package, never silently mixes the corrected route
with the old 49 km geometry/cooks. Hydro-flattened water remains UNKNOWN BED.
"""
from pathlib import Path
import sys
import json
import hashlib
from contextlib import ExitStack

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tmp/south-fork-geospatial-deps'))
import numpy as np
import rasterio
from rasterio.warp import reproject, Resampling
from rasterio.transform import from_origin
from rasterio.features import rasterize
from pyproj import Transformer, CRS
from shapely.geometry import Point, LineString, box, mapping
from shapely.ops import transform, substring, unary_union
from shapely import from_wkb
from pyogrio.raw import read as read_gdb

BASE = ROOT / 'physics/data/real_world/south_fork_american_chili_bar'
OUT = BASE / 'reconstruction_2026_09'
FT_US_TO_M = 1200 / 3937
TO_METRIC = Transformer.from_crs(4326, 32610, always_xy=True)
TO_GEO = Transformer.from_crs(32610, 4326, always_xy=True)


def validated_horizontal_crs(dataset):
    """Strip compound vertical CRS after explicitly converting heights once."""
    crs = CRS.from_user_input(dataset.crs)
    horizontal = crs.sub_crs_list[0] if crs.is_compound else crs
    if horizontal.to_epsg() != 6418 or dataset.units[0] != 'US survey foot':
        raise ValueError('Unexpected native horizontal CRS or elevation units')
    if crs.is_compound and crs.sub_crs_list[1].to_epsg() != 6360:
        raise ValueError('Unexpected survey vertical datum')
    return horizontal.to_wkt()


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False), encoding='utf-8')


def pixel_to_metric(control, metadata):
    x, y = control['pixel_xy']
    width, height = metadata['width'], metadata['height']
    if not (0 <= x <= width and 0 <= y <= height):
        raise ValueError('Control outside source image')
    e = metadata['extent']
    if e['spatialReference']['wkid'] != 32610:
        raise ValueError('Unexpected image CRS; never assume coordinate units')
    return (e['xmin'] + x / width * (e['xmax'] - e['xmin']),
            e['ymax'] - y / height * (e['ymax'] - e['ymin']))


def validate_origin(line, origin):
    # A label and a matching downstream endpoint cannot validate the put-in.
    error = Point(line.coords[0]).distance(Point(origin))
    if error > 150:
        raise ValueError(f'Route origin is {error:.1f} m from independently imaged bridge')


def reconstruct_route(controls):
    old = json.loads((BASE / 'hydrography/full_reach_adopted_route.geojson').read_text())
    feature = next(f for f in old['features'] if f['geometry']['type'] == 'LineString')
    line = LineString([TO_METRIC.transform(*xy[:2]) for xy in feature['geometry']['coordinates']])
    bridge = controls['chili_bar_bridge_channel_crossing']['metric_xy']
    if line.distance(Point(bridge)) > 100:
        raise ValueError('Bridge does not match the captured river route')
    offset = line.project(Point(bridge))
    corrected = substring(line, offset, line.length)
    validate_origin(corrected, bridge)
    features = [{'type': 'Feature', 'id': 'chili_bar_bridge_to_salmon_falls_candidate',
                 'properties': {'axis_id': 'chili_bar_imaged_bridge_metric_v2_candidate',
                     'station_start_m': 0, 'station_end_m': corrected.length,
                     'authority': 'NHD_directed_geometry_clipped_at_orthophoto_bridge',
                     'production_promoted': False,
                     'removed_upstream_length_m': offset},
                 'geometry': mapping(transform(TO_GEO.transform, corrected))}]
    for f in old['features']:
        props = f.get('properties', {})
        if 'label' not in props or 'published_river_mile_alias' not in props:
            continue
        label = props['label']
        station = props['published_river_mile_alias'] * 1609.344
        authority = 'approximate_guide_mile_from_corrected_origin_not_verified_rapid'
        if label == 'Troublemaker':
            station = corrected.project(Point(controls['troublemaker_crux_search']['metric_xy']))
            authority = 'orthophoto_crux_candidate_not_exact_hole_lip'
        if station > corrected.length:
            continue
        features.append({'type': 'Feature', 'properties': {
            'label': label, 'station_m': station, 'authority': authority,
            'published_river_mile_alias': props['published_river_mile_alias'],
            'production_promoted': False},
            'geometry': mapping(transform(TO_GEO.transform, corrected.interpolate(station)))})
    for name, c in controls.items():
        features.append({'type': 'Feature', 'id': name, 'properties': c,
                         'geometry': {'type': 'Point', 'coordinates': list(TO_GEO.transform(*c['metric_xy']))}})
    write_json(OUT / 'corrected_route_candidate.geojson', {'type': 'FeatureCollection', 'features': features})
    return corrected, offset


def read_breaklines():
    path = '/vsizip/' + (OUT / 'sources/eldorado_2019_breaklines.zip').as_posix() + '/Breaklines.gdb'
    metadata, fids, geometries, fields = read_gdb(path, layer='Rivers_Streams', return_fids=True)
    if 'US survey foot' not in metadata['crs']:
        raise ValueError('Unexpected breakline units')
    # Explicit horizontal-only conversion. Z remains NAVD88 orthometric height,
    # converted from US survey feet, NEVER treated as WGS84 ellipsoid height.
    project = Transformer.from_crs(6418, 32610, always_xy=True)
    def convert(x, y, z=None):
        xx, yy = project.transform(x, y)
        return (xx, yy, np.asarray(z) * FT_US_TO_M) if z is not None else (xx, yy)
    return [(int(fid), transform(convert, from_wkb(g))) for fid, g in zip(fids, geometries)]


def reconstruct_window(label, breaklines, tiles, export_metadata=None, preselected=False):
    metadata = export_metadata if export_metadata is not None else json.loads((OUT / f'sources/{label}_naip_export.json').read_text())
    e = metadata['extent']
    resolution = .5
    xmin, ymin = np.floor([e['xmin'], e['ymin']])
    xmax, ymax = np.ceil([e['xmax'], e['ymax']])
    width, height = int((xmax-xmin)/resolution), int((ymax-ymin)/resolution)
    affine = from_origin(xmin, ymax, resolution, resolution)
    ground = np.full((height, width), np.nan, dtype=np.float32)
    selected = [tile for tile in tiles if (label == 'chili_bar' and 'chili_bar_bridge_search' in tile['leads'])
                or (label == 'troublemaker' and 'hazard_below_troublemaker' in tile['leads'])]
    if preselected:
        selected=tiles
    sources = []
    for item in selected:
        path = OUT / 'sources/dem' / item['file']
        with rasterio.open(path) as src:
            source_horizontal_crs = validated_horizontal_crs(src)
            data = src.read(1).astype(np.float32)
            data[data == src.nodata] = np.nan
            data *= FT_US_TO_M
            reproject(source=data, destination=ground, src_transform=src.transform,
                      src_crs=source_horizontal_crs, src_nodata=np.nan, dst_transform=affine,
                      dst_crs='EPSG:32610', dst_nodata=np.nan, init_dest_nodata=False,
                      resampling=Resampling.bilinear)
            sources.append({'file': item['file'], 'sha256': item['sha256'],
                            'native_cell_size_m': src.res[0]*FT_US_TO_M})
    extent = box(xmin, ymin, xmax, ymax)
    clipped = [(fid, geom.intersection(extent)) for fid, geom in breaklines if geom.intersects(extent)]
    water = unary_union([geom for _, geom in clipped])
    if water.is_empty:
        raise ValueError(f'{label}: no actual surveyed hydro-boundary coverage')
    wet = rasterize([(mapping(water), 1)], out_shape=ground.shape, transform=affine, dtype='uint8')
    target = OUT / label
    target.mkdir(parents=True,exist_ok=True)
    profile = dict(driver='GTiff', width=width, height=height, count=1, dtype='float32',
                   crs='EPSG:32610', transform=affine, compress='deflate', nodata=np.nan)
    with rasterio.open(target / 'survey_surface_navd88_m.tif', 'w', **profile) as dst:
        dst.write(ground, 1)
        dst.set_band_unit(1, 'metre')
        dst.update_tags(vertical_datum='NAVD88', water_pixels='hydroflattened_surface_NOT_bathymetry')
    with rasterio.open(target / 'unknown_submerged_bed_mask.tif', 'w', **dict(profile, dtype='uint8', nodata=255)) as dst:
        dst.write(np.where(np.isfinite(ground), wet, 255).astype('uint8'), 1)
    features = [{'type': 'Feature', 'properties': {'source_fid': fid,
                 'authority': 'USGS_2019_2020_lidar_hydrobreakline', 'vertical_datum': 'NAVD88',
                 'z_units': 'metres', 'is_bathymetry': False},
                 'geometry': mapping(transform(TO_GEO.transform, geom))} for fid, geom in clipped]
    write_json(target / 'survey_water_boundaries.geojson', {'type': 'FeatureCollection', 'features': features})
    manifest = {'status': 'captured_surface_candidate_not_game_integrated',
        'horizontal_crs': 'EPSG:32610', 'vertical_datum': 'NAVD88', 'z_units': 'metres',
        'horizontal_datum_registration': 'PROJ NAD83(2011) to WGS84 transform; no local survey tie, retain metre-scale registration uncertainty',
        'grid_resolution_m': resolution, 'bounds_utm_m': [xmin, ymin, xmax, ymax],
        'shape_rows_cols': [height, width], 'valid_fraction': float(np.isfinite(ground).mean()),
        'survey_water_fraction': float(wet.mean()),
        'elevation_range_navd88_m': [float(np.nanmin(ground)), float(np.nanmax(ground))],
        'dem_sources': sources, 'survey_water_boundary_features': len(clipped),
        'bathymetry_known': False, 'production_promoted': False,
        'random_boulders_added': 0,
        'requirements': ['Infer submerged bed separately without changing measured dry ground',
            'Use the SAME metric bed/rock geometry for render and collision and hydraulic cells',
            'Do not apply old procedural corridor bank widening or generic S-bend to captured geometry',
            'Calibrate flow/stage against dated footage; source imagery discharge is unknown']}
    write_json(target / 'manifest.json', manifest)
    print(label, json.dumps(manifest), flush=True)
    return manifest


def main():
    visual = json.loads((OUT / 'visual_controls.json').read_text())
    controls = {}
    for c in visual['controls']:
        metadata = json.loads((OUT / f"sources/{c['image']}_naip_export.json").read_text())
        controls[c['id']] = {**c, 'metric_xy': pixel_to_metric(c, metadata),
                            'source_acquisition_date': visual['source_acquisition_date']}
    route, offset = reconstruct_route(controls)
    print('Corrected candidate route length:', route.length, 'removed upstream:', offset, flush=True)
    breaklines = read_breaklines()
    tiles = json.loads((OUT / 'sources/dem/downloads.json').read_text())
    reports = {label: reconstruct_window(label, breaklines, tiles) for label in ('chili_bar', 'troublemaker')}
    write_json(OUT / 'reconstruction_manifest.json', {'status': 'geographic_reconstruction_in_progress',
        'corrected_route_length_m': route.length, 'removed_wrong_upstream_reach_m': offset,
        'source_windows': reports, 'game_geometry_updated': False, 'hydraulics_recooked': False,
        'all_south_fork_rapids_reconstructed': False, 'not_for_navigation': True})


if __name__ == '__main__':
    main()
