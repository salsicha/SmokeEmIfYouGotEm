"""Fit unchanged-size Cartesian regions inside retained source coverage.

The source was clipped around an earlier geographic axis. Moving a sampling
window is allowed; moving captured terrain or filling missing cells is not.
"""
import json
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT/'physics/data/real_world/south_fork_american_chili_bar/reconstruction_2026_09/full_reach'


def source_fit_plan():
    import rasterio
    from scipy.ndimage import minimum_filter
    from scipy.spatial import cKDTree
    from prepare_south_fork_hydraulic_regions import region_centers, coverage_margin, HALF_LIVE_M
    coordinates = json.loads((BASE/'playable_route/coordinate_map.json').read_text())
    points = np.asarray(coordinates['points'])
    origin = np.asarray(coordinates['origin_utm_m'])
    with rasterio.open(BASE/'captured_surface_navd88_m.tif') as ds:
        source = ds.read(1)
        affine = ds.transform
    assert affine.a == 2 and affine.e == -2
    # A 320 m rectangle plus the extra source vertices needed by exact
    # triangle and bilinear surface sampling. No tolerance/extent reduction.
    allowed = minimum_filter(np.isfinite(source).astype(np.uint8), size=163, mode='constant', cval=0) != 0
    row, col = np.nonzero(allowed)
    possible = np.column_stack((affine.c+(col+.5)*2, affine.f-(row+.5)*2))
    if not len(possible):
        raise ValueError('No complete source-backed 320 m regions')
    tree = cKDTree(possible)
    stations, requested = region_centers(points, origin)
    distance, selected = tree.query(requested, p=np.inf)
    centers = possible[selected]
    query = np.concatenate([points[:, 1:3]+origin+side*12*points[:, 3:5] for side in (0, -1, 1)])
    margins, _ = coverage_margin(query, centers)
    supplements = []
    while margins.min() < HALF_LIVE_M:
        i = int(np.argmin(margins))
        _, selected = tree.query(query[i], p=np.inf)
        center = possible[selected]
        if np.min(np.max(np.abs(centers-center), axis=1)) < .01:
            break
        centers = np.vstack((centers, center))
        stations = np.r_[stations, points[i % len(points), 0]]
        supplements.append(center.tolist())
        margins, _ = coverage_margin(query, centers)
    order = np.argsort(stations, kind='stable')
    # Probe all captured water vertices as well; a guided axis alone does not
    # prove that a freely paddled raft has a complete hydraulic neighborhood.
    with rasterio.open(BASE/'unknown_submerged_bed_mask.tif') as ds:
        wet_row, wet_col = np.nonzero(ds.read(1) == 1)
    wet_query = np.column_stack((affine.c+(wet_col+.5)*2, affine.f-(wet_row+.5)*2))
    water_margin, _ = coverage_margin(wet_query, centers)
    best_distance, _ = tree.query(wet_query, p=np.inf)
    impossible = best_distance > 160-HALF_LIVE_M
    result = dict(region_extent_m=[320,320], live_extent_m=[224,224], geometry_moved=False,
        required_margin_m=HALF_LIVE_M, candidate_source_centers=len(possible),
        initial_center_max_shift_m=float(distance.max()), supplemental_centers_utm_m=supplements,
        axis_side_probe_count=len(query), axis_side_minimum_margin_m=float(margins.min()),
        axis_side_coverage_passed=bool((margins >= HALF_LIVE_M).all()),
        captured_water_probe_count=len(wet_query), captured_water_minimum_margin_m=float(water_margin.min()),
        captured_water_unsupported_probe_count=int((water_margin < HALF_LIVE_M).sum()),
        captured_water_uncoverable_without_more_source_count=int(impossible.sum()),
        best_possible_water_minimum_margin_m=float(160-best_distance.max()),
        first_uncoverable_water_utm_m=wet_query[impossible][:20].tolist(),
        stations_m=stations[order].tolist(), centers_utm_m=centers[order].tolist(),
        normal_map_integrated=False, hydraulic_validation_passed=False)
    return result


if __name__ == '__main__':
    output = BASE/'hydraulic_regions/source_fit_plan.json'
    assert not output.exists(), 'Preserve existing fit evidence'
    report = source_fit_plan()
    output.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ('stations_m','centers_utm_m')}, indent=2), flush=True)
