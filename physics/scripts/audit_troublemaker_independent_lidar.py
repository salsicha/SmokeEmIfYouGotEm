"""Compare a separate survey with retained cap anchors, without changing geometry.

Neighbourhoods are coordinate queries, NOT registered point correspondences.
NAVD88 values from different geoid realizations are not silently adjusted.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tmp/south-fork-geospatial-deps'))
import laspy
import numpy as np
from pyproj import CRS, Transformer


def summarize_neighbours(nearby, target_z, radius):
    if not np.isfinite(target_z) or not np.isfinite(radius) or radius <= 0:
        raise ValueError('Expected finite height and positive radius')
    if any(not np.isfinite(p[1:3]).all() or p[1] < 0 for p in nearby):
        raise ValueError('Invalid neighbour distance or height')
    subset = [p for p in nearby if p[1] <= radius]
    classes = sorted({p[3] for p in subset})
    return dict(radius_m=radius, count=len(subset),
        classes={str(c): sum(p[3] == c for p in subset) for c in classes},
        height_delta_quantiles_m=np.quantile([p[2]-target_z for p in subset], [0,.5,1]).tolist() if subset else None)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('laz', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError('Refusing to overwrite an earlier report')
    base = ROOT / 'physics/data/real_world/south_fork_american_chili_bar/reconstruction_2026_09/troublemaker'
    witness = ROOT / 'docs/reconstruction-review-2026-09-07/downstream-cap-provenance/original-pulses.json'
    prior = json.loads(witness.read_text())
    source = base / 'classified_lidar_returns.npz'
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    if digest != prior['source_identities']['returns']['sha256']:
        raise ValueError('Original source has changed')
    # Audit rows refer to actual original-point indices, not a nearest neighbour.
    if prior['schema'] != 'raftsim.downstream_cap_original_pulses.v1':
        raise ValueError('Unexpected witness schema')
    rows = prior['neighbouring_returns']
    ids = np.array([r['original_id'] for r in rows], dtype=int)
    with np.load(source) as old:
        targets = np.column_stack([old['utm_easting_m'][ids], old['utm_northing_m'][ids], old['navd88_m'][ids]])
    neighbours = [[] for _ in ids]
    with laspy.open(args.laz) as reader:
        crs = reader.header.parse_crs()
        if crs is None:
            raise ValueError('Missing source CRS')
        horizontal = crs.sub_crs_list[0] if crs.is_compound else crs
        if horizontal.to_epsg() != 6339:
            raise ValueError(f'Unexpected source CRS: {crs}')
        if not crs.is_compound or crs.sub_crs_list[1].to_epsg() != 5703:
            raise ValueError('Expected explicit NAVD88 metre vertical CRS')
        transform = Transformer.from_crs(horizontal, CRS.from_epsg(32610), always_xy=True)
        count = reader.header.point_count
        offset = 0
        for points in reader.chunk_iterator(500000):
            x, y = transform.transform(np.asarray(points.x), np.asarray(points.y))
            z = np.asarray(points.z)
            classification = np.asarray(points.classification)
            for i, target in enumerate(targets):
                distance = np.hypot(x-target[0], y-target[1])
                selected = np.flatnonzero(distance <= 3.0)
                for j in selected:
                    neighbours[i].append((int(offset+j), float(distance[j]), float(z[j]), int(classification[j])))
            offset += len(points)
        if offset != count:
            raise ValueError('Incomplete point stream')
    result = []
    for original_id, target, nearby in zip(ids, targets, neighbours):
        radii = [summarize_neighbours(nearby, target[2], radius)
                 for radius in (0.3, 0.5, 1.0, 3.0)]
        result.append(dict(original_id=int(original_id), original_utm_navd88_m=target.tolist(),
            neighbourhoods=radii, nearest=min(nearby, key=lambda p: p[1]) if nearby else None))
    report = dict(schema='raftsim.independent_lidar_neighbourhoods.v1',
        production_promoted=False, point_correspondences_established=False,
        caveat='Unregistered separate epochs; GEOID12B versus GEOID18 NAVD88 realizations. Classes are not certified rock labels. No bathymetry inference.',
        laz=str(args.laz), laz_sha256=hashlib.sha256(args.laz.read_bytes()).hexdigest(),
        original_sha256=digest, witness_sha256=hashlib.sha256(witness.read_bytes()).hexdigest(),
        header_crs=crs.to_wkt(), horizontal_transform=transform.description,
        horizontal_transform_accuracy_m=transform.accuracy, total_points=count, anchors=result)
    args.output.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(dict(total_points=count, anchors=len(result),
        anchors_with_returns_within_30cm=sum(r['neighbourhoods'][0]['count']>0 for r in result),
        laz_sha256=report['laz_sha256'])))


if __name__ == '__main__':
    main()
