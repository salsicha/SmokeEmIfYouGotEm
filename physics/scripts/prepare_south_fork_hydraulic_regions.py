"""Prepare source-exact Cartesian hydraulic geometry across the full descent.

This is geometry and captured-surface initialization data, NOT settled flow.
All regions share one metre lattice and orientation, so runtime overlaps can
preserve cells without rotating or resampling the state. No missing terrain is
filled, no acceptance gate is changed, and no normal map is modified.
"""
import hashlib
import argparse
import json
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT/'physics/data/real_world/south_fork_american_chili_bar/reconstruction_2026_09/full_reach'
OUT = BASE/'hydraulic_regions'
HALF_SOURCE_M = 160
HALF_LIVE_M = 112


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def region_centers(points, origin, stride_m=80.):
    """Keep original source corners; snap centres, never deform the polyline."""
    points = np.asarray(points, dtype=float)
    stations = np.r_[np.arange(points[0, 0], points[-1, 0], stride_m), points[-1, 0]]
    xy = np.column_stack([np.interp(stations, points[:, 0], points[:, i]) for i in (1, 2)])+origin
    return stations, np.rint(xy).astype(np.int64)


def coverage_margin(queries, centers, half_source=HALF_SOURCE_M):
    """Best complete-square margin, not just distance to a river station."""
    from scipy.spatial import cKDTree
    queries = np.asarray(queries)
    # The largest square margin is the nearest centre in Chebyshev distance.
    distance, index = cKDTree(centers).query(queries, p=np.inf)
    return half_source-distance, index


def main():
    import rasterio
    from scipy.ndimage import map_coordinates
    from south_fork_composite_terrain import CompositeTerrainSampler
    parser = argparse.ArgumentParser()
    parser.add_argument('--context-extension', action='store_true')
    args = parser.parse_args()
    global OUT
    extension = BASE/'source_context_extension' if args.context_extension else None
    if extension:
        OUT = BASE/'hydraulic_regions_context'
    assert not OUT.exists(), 'Use a fresh revision; existing region evidence must be retained'
    coordinates = json.loads((BASE/'playable_route/coordinate_map.json').read_text())
    points = np.asarray(coordinates['points'])
    origin = np.asarray(coordinates['origin_utm_m'])
    stations, centers = region_centers(points, origin)
    # Audit every dense axis point and both 12 m side offsets. If a sharp
    # bend needs an extra source region, add it instead of shrinking coverage.
    query = np.concatenate([points[:, 1:3]+origin+side*12*points[:, 3:5] for side in (0, -1, 1)])
    original_water_probe_count = 0
    if extension:
        from scipy.spatial import cKDTree
        with rasterio.open(BASE/'unknown_submerged_bed_mask.tif') as ds:
            wr, wc = np.nonzero(ds.read(1) == 1)
            water_query = np.column_stack((ds.transform.c+(wc+.5)*2, ds.transform.f-(wr+.5)*2))
        original_water_probe_count = len(water_query)
        query = np.vstack((query, water_query))
        centers = np.unique(np.rint(water_query/80).astype(np.int64)*80, axis=0)
        _, nearest = cKDTree(points[:,1:3]+origin).query(centers)
        stations = points[nearest,0]
    margins, _ = coverage_margin(query, centers)
    added = []
    while margins.min() < HALF_LIVE_M:
        index = int(np.argmin(margins))
        center = np.rint(query[index]).astype(np.int64)
        if any(np.array_equal(center, existing) for existing in centers):
            raise ValueError('Cannot provide complete live-window coverage')
        centers = np.vstack((centers, center))
        if index < 3*len(points):
            station = float(points[index % len(points), 0])
        else:
            station = float(points[np.argmin(np.sum((points[:,1:3]+origin-center)**2,axis=1)),0])
        stations = np.r_[stations, station]
        added.append(dict(station_m=station, center_utm_m=center.tolist()))
        margins, _ = coverage_margin(query, centers)
    order = np.argsort(stations, kind='stable')
    centers, stations = centers[order], stations[order]
    unique = set()
    records = []
    terrain = CompositeTerrainSampler(BASE/'composite_terrain', extension)
    surface_directory = extension or BASE
    with rasterio.open(surface_directory/'captured_surface_navd88_m.tif') as ds:
        surface, transform = ds.read(1), ds.transform
    with rasterio.open(surface_directory/'unknown_submerged_bed_mask.tif') as ds:
        assert ds.transform == transform and ds.shape == surface.shape
        source_water = ds.read(1)
    offsets = np.arange(-HALF_SOURCE_M, HALF_SOURCE_M+1, dtype=np.float64)
    dx, dy = np.meshgrid(offsets, offsets)
    report = dict(schema='raftsim.south_fork.cartesian_hydraulic_geometry.v1',
        source_geometry_sha256=sha((extension or BASE/'composite_terrain')/'manifest.json'),
        base_geometry_sha256=sha(BASE/'composite_terrain/manifest.json'),
        context_extension_included=bool(extension), original_water_domain_probe_count=original_water_probe_count,
        coordinate_map_sha256=sha(BASE/'playable_route/coordinate_map.json'),
        grid_spacing_m=1., region_extent_m=[320., 320.], supported_live_extent_m=[224., 224.],
        world_origin_utm_m=origin.tolist(), vertical_datum_navd88_m=coordinates['vertical_datum_m'],
        lattice_origin_utm_m=[0, 0], solver_axes='x east, y north; world Y reflection only at engine boundary',
        full_route_axis_and_12m_side_probe_count=3*len(points), total_coverage_probe_count=len(query),
        minimum_complete_window_margin_m=float(margins.min()),
        supplemental_regions=added, regions=records, completed=False,
        settled_hydraulics_available=False, normal_map_integrated=False, full_reconstruction_accepted=False)
    OUT.mkdir()
    for station, center in zip(stations, centers):
        if tuple(center) in unique:
            continue
        unique.add(tuple(center))
        east, north = center[0]+dx, center[1]+dy
        try:
            bed, owners = terrain.sample(east, north, with_owner=True)
            c, r = (~transform)*(east, north)
            captured = map_coordinates(surface, [r-.5, c-.5], order=1, mode='constant', cval=np.nan)
            water = map_coordinates(source_water, [r-.5, c-.5], order=0, mode='constant', cval=0) == 1
            if not np.isfinite(captured).all():
                raise ValueError('Captured surface missing inside region')
        except ValueError as error:
            report['failure'] = dict(station_m=float(station), center_utm_m=center.tolist(), reason=str(error))
            (OUT/'manifest.json').write_text(json.dumps(report, indent=2)+'\n')
            raise
        name = f'region_{len(records):04d}'
        path = OUT/(name+'.npz')
        np.savez_compressed(path, bed_navd88_m=bed, captured_surface_navd88_m=captured,
            captured_water_mask=water.astype(np.uint8), terrain_owner=owners)
        lower = center-HALF_SOURCE_M
        records.append(dict(name=name, station_hint_m=float(station), center_utm_m=center.tolist(),
            bounds_utm_m=[*lower.tolist(), *(center+HALF_SOURCE_M).tolist()],
            grid_origin_local_m=(lower-origin).tolist(), shape=list(bed.shape),
            geometry_file=path.relative_to(ROOT).as_posix(), geometry_sha256=sha(path),
            owner_cell_counts={str(k): int((owners == k).sum()) for k in (1, 2, 3, 4)},
            captured_water_cell_count=int(water.sum()), all_geometry_samples_finite=True))
        (OUT/'manifest.json').write_text(json.dumps(report, indent=2)+'\n')
        if len(records) % 25 == 0:
            print(f'Prepared {len(records)}/{len(centers)} shared-grid geometry regions', flush=True)
    report.update(completed=True, region_count=len(records), source_sample_count=len(records)*dx.size)
    (OUT/'manifest.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k != 'regions'}, indent=2), flush=True)


if __name__ == '__main__':
    main()
