"""Compare provisional class-20 observations with the immutable registered base.

This base is NOT the final terrain/cap union. Residuals do not establish a
playable defect. Neighborhoods are source support, not semantic rock labels.
"""
import argparse
import json
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
from audit_eldorado_ignored_ground import audit, ROOT, SOURCE
from build_troublemaker_dem_rock_cap import PARENT, PARENT_SHA, ORIGIN
from south_fork_registered_mesh import RegisteredMeshSampler
from south_fork_rock_union import sha


def peer_support(xyz, classes, query_ids, radius_m=.5):
    xyz, classes, query_ids = np.asarray(xyz), np.asarray(classes), np.asarray(query_ids)
    if xyz.ndim != 2 or xyz.shape[1] != 3 or classes.shape != (len(xyz),):
        raise ValueError('Matching source XYZ and classifications required')
    if not np.isfinite(xyz).all() or not np.isfinite(radius_m) or radius_m <= 0:
        raise ValueError('Finite XYZ and positive radius required')
    if query_ids.ndim != 1 or not np.issubdtype(query_ids.dtype, np.integer) or np.any(query_ids < 0) or np.any(query_ids >= len(xyz)):
        raise ValueError('Original query indices required')
    eligible = np.flatnonzero(np.isin(classes, [1, 2, 20]))
    tree = cKDTree(xyz[eligible, :2])
    rows = []
    for index, neighbors in zip(query_ids, tree.query_ball_point(xyz[query_ids, :2], radius_m)):
        peers = eligible[neighbors]
        peers = peers[peers != index]  # Never count the observation as corroboration.
        ground = peers[np.isin(classes[peers], [2, 20])]
        rows.append(dict(original_return_index=int(index), peer_count=len(peers),
            classified_ground_peer_count=len(ground),
            classified_ground_peer_indices=ground.tolist(),
            classified_ground_peer_height_delta_m=(xyz[ground, 2]-xyz[index, 2]).tolist()))
    return rows


def run():
    previous = audit()
    if sha(PARENT) != PARENT_SHA:
        raise ValueError('Registered base identity changed')
    with np.load(PARENT, allow_pickle=False) as mesh:
        sampler = RegisteredMeshSampler(mesh)
    ids = np.array([row['original_return_index'] for row in previous['added_candidates']], dtype=np.int64)
    with np.load(SOURCE, allow_pickle=False) as source:
        xyz = np.column_stack([source[k] for k in ('utm_easting_m', 'utm_northing_m', 'navd88_m')])
        rows = peer_support(xyz, source['classification'], ids)
        queries = xyz[ids]
    heights = sampler.sample(queries[:, 0]-ORIGIN[0], queries[:, 1]-ORIGIN[1])+ORIGIN[2]
    for row, point, height in zip(rows, queries, heights):
        row.update(source_utm_navd88_m=point.tolist(), registered_base_navd88_m=float(height),
            source_minus_registered_base_m=float(point[2]-height))
    if sha(PARENT) != PARENT_SHA or sha(SOURCE) != previous['source_sha256']:
        raise ValueError('Inputs changed during audit')
    return dict(schema='raftsim.ignored_ground_registered_base_screen.v1',
        source_sha256=previous['source_sha256'], registered_base_sha256=PARENT_SHA,
        registered_base_path=PARENT.relative_to(ROOT).as_posix(),
        neighborhood_radius_m=.5, self_counted_as_peer=False,
        query_count=len(rows), rows=rows, current_playable_union_audited=False,
        geometry_modified=False, playable_integrated=False,
        interpretation='Registered base only; not final cap union or proof of a rock or playable defect.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    output = parser.parse_args().output.resolve()
    if output.exists() or not output.is_relative_to(ROOT):
        raise ValueError('Fresh in-repository output required')
    result = run()
    with output.open('x', encoding='utf-8') as handle:
        handle.write(json.dumps(result, indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k != 'rows'}, indent=2))
