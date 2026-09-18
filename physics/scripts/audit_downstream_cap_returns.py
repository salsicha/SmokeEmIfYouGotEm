"""Recover original pulse metadata for the cap hit in an actual player view.

Neither nearby lower returns nor pulse multiplicity classify a point as rock
or vegetation. Preserve all original XYZ and classifications. This is source
interpretation evidence, not permission to smooth captured anchors.
"""
import argparse
import json
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree

from build_troublemaker_dem_rock_cap import ROOT, BASE, ORIGIN
from south_fork_rock_union import sha


def neighbour_evidence(vertices, original_ids, xyz, classification, radius_m=.3):
    if not np.isfinite(radius_m) or radius_m <= 0:
        raise ValueError('Positive finite diagnostic radius required')
    if not np.array_equal(vertices, xyz[original_ids]):
        raise ValueError('Cap vertices must reproduce exact original returns')
    eligible = np.flatnonzero(np.isin(classification, [1, 2, 10]))
    tree = cKDTree(xyz[eligible, :2])
    rows = []
    for vertex, original_id in zip(vertices, original_ids):
        ids = eligible[tree.query_ball_point(vertex[:2], radius_m)]
        if not len(ids):
            raise ValueError('Original cap vertex absent from eligible source cloud')
        lowest = ids[np.lexsort((ids, xyz[ids, 2]))[0]]
        rows.append(dict(original_id=int(original_id), local_xyz_m=vertex.tolist(),
            nearby_original_count=len(ids), lowest_original_id=int(lowest),
            lowest_local_xyz_m=xyz[lowest].tolist(),
            lower_neighbour_drop_m=float(vertex[2]-xyz[lowest, 2]),
            horizontal_separation_m=float(np.linalg.norm(vertex[:2]-xyz[lowest, :2]))))
    return rows


def run(audit_path, output):
    import laspy
    from pyproj import Transformer
    if output.exists() or not output.resolve().is_relative_to(ROOT/'tmp'):
        raise ValueError('Fresh project tmp report required')
    review = json.loads(audit_path.read_text())
    if review.get('schema') != 'raftsim.terrain_camera_source_audit.v1' or review.get('all_probes_match') is not True:
        raise ValueError('Verified actual native/source ray audit required')
    sources = review['source_identities']
    for key in ('cap', 'returns'):
        if sha(ROOT/sources[key]['path']) != sources[key]['sha256']:
            raise ValueError('Audited source changed')
    with np.load(ROOT/sources['cap']['path'], allow_pickle=False) as data:
        cap = {k: data[k] for k in data.files}
    with np.load(ROOT/sources['returns']['path'], allow_pickle=False) as data:
        cloud = {k: data[k] for k in data.files}
    xyz = np.column_stack([cloud[k] for k in ('utm_easting_m', 'utm_northing_m', 'navd88_m')])
    roof_count = len(cap['vertices_m'])
    if not np.array_equal(cap['solid_vertices_m'][:roof_count], cap['vertices_m']) or len(cap['solid_vertices_m']) != 2*roof_count:
        raise ValueError('Expected original roof plus internal floor representation')
    ids = sorted({i % roof_count for r in review['probes'] if r['source_hit'] and r['source_hit']['source'] == 'cap'
                  for i in r['source_hit']['source_vertices']})
    if not ids:
        raise ValueError('No actual cap hits')
    rows = neighbour_evidence(cap['vertices_m'][ids], cap['original_return_index'][ids], xyz-ORIGIN, cloud['classification'])
    wanted = sorted({r[k] for r in rows for k in ('original_id', 'lowest_original_id')})
    # Use the exact same provider-to-UTM transformation and survey-foot factor
    # as the original extraction. Do not match merely by nearest XY/height.
    lookup = {}
    for index in wanted:
        lookup.setdefault(tuple(xyz[index]), []).append(index)
    found = {index: [] for index in wanted}
    source_records = json.loads((BASE/'sources/point_cloud/downloads.json').read_text())
    transform = Transformer.from_crs(6418, 32610, always_xy=True)
    inverse = Transformer.from_crs(32610, 6418, always_xy=True)
    selected = xyz[wanted]
    bounds = inverse.transform_bounds(selected[:, 0].min()-1, selected[:, 1].min()-1,
                                      selected[:, 0].max()+1, selected[:, 1].max()+1)
    fields = ('classification', 'return_number', 'number_of_returns', 'intensity',
              'point_source_id', 'gps_time', 'scanner_channel', 'scan_angle', 'scan_angle_rank',
              'scan_direction_flag', 'edge_of_flight_line', 'synthetic', 'key_point', 'withheld', 'overlap')
    tiles = []
    nearby_pulses = {}
    for record in source_records:
        path = BASE/'sources/point_cloud'/record['file']
        if sha(path) != record['sha256']:
            raise ValueError('Original LAZ identity changed')
        with laspy.open(path) as reader:
            crs = reader.header.parse_crs()
            horizontal = crs.sub_crs_list[0] if crs and crs.is_compound else crs
            if horizontal is None or horizontal.to_epsg() != 6418:
                raise ValueError('Unexpected original source CRS')
            dimensions = set(reader.header.point_format.dimension_names)
            offset = 0
            for points in reader.chunk_iterator(1_000_000):
                x, y = np.asarray(points.x), np.asarray(points.y)
                keep = np.flatnonzero((x >= bounds[0]) & (x <= bounds[2]) &
                    (y >= bounds[1]) & (y <= bounds[3]) & (np.asarray(points.withheld) == 0))
                if len(keep):
                    e, n = transform.transform(x[keep], y[keep])
                    recovered = np.column_stack([e, n, np.asarray(points.z)[keep]*(1200/3937)])
                    # Decode packed LAS bitfields once per chunk, not once per
                    # nearby point. Preserve only this bounded neighbourhood.
                    columns = {key: np.asarray(getattr(points, key))[keep]
                               for key in fields if key in dimensions}
                    for nearby_index, (chunk_index, point) in enumerate(zip(keep, recovered)):
                        metadata = {key: values[nearby_index].item() for key, values in columns.items()}
                        pulse = dict(tile=record['file'], point_index=int(offset+chunk_index),
                                     utm_navd88_xyz_m=point.tolist(), **metadata)
                        if 'gps_time' in metadata and 'point_source_id' in metadata:
                            key = (record['file'], metadata['point_source_id'], metadata['gps_time'], metadata.get('scanner_channel'))
                            nearby_pulses.setdefault(key, []).append(pulse)
                        for original_id in lookup.get(tuple(point), []):
                            if metadata['classification'] != int(cloud['classification'][original_id]):
                                raise ValueError('Exact XYZ matched a different source classification')
                            found[original_id].append(pulse)
                offset += len(points)
        tiles.append(dict(file=record['file'], sha256=record['sha256']))
    if any(not hits for hits in found.values()):
        raise ValueError('Original pulse metadata missing; no nearest-point substitution allowed')
    contexts = []
    seen = set()
    for hits in found.values():
        for hit in hits:
            key = (hit['tile'], hit['point_source_id'], hit['gps_time'], hit.get('scanner_channel'))
            if hit['number_of_returns'] <= 1 or key in seen:
                continue
            seen.add(key)
            returns = sorted(nearby_pulses[key], key=lambda row: row['return_number'])
            complete = [r['return_number'] for r in returns] == list(range(1, hit['number_of_returns']+1))
            contexts.append(dict(tile=key[0], point_source_id=key[1], gps_time=key[2],
                scanner_channel=key[3],
                every_reported_return_in_bounded_neighbourhood=complete, returns=returns))
    report = dict(schema='raftsim.downstream_cap_original_pulses.v1', ray_audit_sha256=sha(audit_path),
        source_identities=sources, laz_sources=tiles, exact_xyz_and_classification_matches=True,
        cap_vertices=ids, neighbour_radius_prior_m=.3, neighbouring_returns=rows,
        pulse_records=found, multi_return_pulse_context=contexts,
        source_geometry_modified=False, classification_modified=False,
        normal_play_changed=False, visual_or_physical_accepted=False,
        limits='0.3m radius is diagnostic, not a surveyed outline. Lower nearby points and pulse multiplicity do not distinguish vegetation, sharp rock, occlusion or source error. No anchor flattening authorized by this report.')
    output.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(dict(exactly_matched_original_ids=len(found), cap_vertices=len(ids),
                         maximum_neighbour_drop_m=max(r['lower_neighbour_drop_m'] for r in rows)), indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('ray_audit', type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    run(args.ray_audit, args.output)
