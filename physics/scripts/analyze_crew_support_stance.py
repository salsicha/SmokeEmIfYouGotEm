"""Exact triangle-query stance search; hypotheses, not runtime acceptance.

Uses exported production geometry and measured rest-joint segment lengths.
Searches level, forward-facing paired boots without relaxing the 4 cm span or
1 cm reach margin. Outputs fresh evidence only; never changes game assets.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np


def top_at_many(points, triangles):
    result = np.full(len(points), -np.inf)
    minimum = triangles[:, :, :2].min(axis=1)
    maximum = triangles[:, :, :2].max(axis=1)
    cells = np.floor(points[:, :2]/20).astype(int)
    for cell in np.unique(cells, axis=0):
        ids = np.flatnonzero(np.all(cells == cell, axis=1))
        local = points[ids]
        nearby = triangles[np.all(maximum >= cell*20-1.e-6, axis=1) &
                           np.all(minimum <= (cell+1)*20+1.e-6, axis=1)]
        heights = np.full(len(ids), -np.inf)
        for a, b, c in nearby:
            det = (b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
            if abs(det) < 1.e-8:
                continue
            u = ((b[1]-c[1])*(local[:, 0]-c[0])+(c[0]-b[0])*(local[:, 1]-c[1]))/det
            v = ((c[1]-a[1])*(local[:, 0]-c[0])+(a[0]-c[0])*(local[:, 1]-c[1]))/det
            inside = np.minimum(np.minimum(u, v), 1-u-v) >= -1.e-6
            z = u*a[2]+v*b[2]+(1-u-v)*c[2]
            heights[inside] = np.maximum(heights[inside], z[inside])
        result[ids] = heights
    return result


def analyze(data):
    triangles = np.concatenate([np.asarray(s['points_cm'])[np.asarray(s['indices']).reshape(-1, 3)] for s in data['sections']])
    results = []
    for crew in data['crew']:
        origin = np.asarray(crew['origin_cm'])
        basis = np.asarray(crew['basis'])
        if not np.allclose(basis, np.eye(3), atol=1.e-5):
            raise ValueError('This bounded analysis requires the exported unrotated validation raft')
        side = -1 if origin[1] < 0 else 1
        # Expanded paired search, no shape or acceptance-limit changes.
        xx, yy = np.meshgrid(np.arange(-80., 81., 2.), np.arange(-60., 61., 1.))
        centers = np.column_stack((xx.ravel(), yy.ravel(), np.zeros(xx.size)))
        accepted = np.ones(len(centers), dtype=bool)
        per_foot = []
        for foot, suffix in enumerate(('l', 'r')):
            boot = next(b for b in crew['boots'] if b['name'] == ('ProductionLeftBoot' if foot == 0 else 'ProductionRightBoot'))
            lo = np.asarray(boot['minimum_cm'])*boot['scale']
            hi = np.asarray(boot['maximum_cm'])*boot['scale']
            offsets = np.asarray([[x, y, 0.] for x in np.linspace(lo[0], hi[0], 5) for y in np.linspace(lo[1], hi[1], 3)])
            feet = centers+np.asarray([20., -7. if foot == 0 else 7., 0.])
            points = (feet[:, None, :]+offsets[None, :, :]+origin).reshape(-1, 3)
            support = top_at_many(points, triangles).reshape(len(feet), len(offsets))
            all_supported = np.isfinite(support).all(axis=1)
            span = np.full(len(feet), np.inf)
            span[all_supported] = np.ptp(support[all_supported], axis=1)
            feet[:, 2] = support.max(axis=1)-origin[2]-boot['minimum_cm'][2]*crew['profile'][2]+0.1
            hip = np.asarray(crew['joints']['thigh_'+suffix])-origin
            knee = np.asarray(crew['joints']['calf_'+suffix])-origin
            rest_foot = np.asarray(crew['joints']['foot_'+suffix])-origin
            upper, lower = np.linalg.norm(hip-knee), np.linalg.norm(knee-rest_foot)
            hip[1] += side*28.
            reach = np.linalg.norm(feet-hip, axis=1)
            valid = all_supported & (span <= 4.) & (reach < upper+lower-1.) & (reach > abs(upper-lower)+1.)
            accepted &= valid
            per_foot.append(dict(feet=feet, span=span, valid=valid,
                upper_cm=float(upper), lower_cm=float(lower)))
        ids = np.flatnonzero(accepted)
        ids = ids[np.argsort(np.linalg.norm(centers[ids, :2], axis=1))]
        # Test whether the rigid paired translation, rather than missing
        # support, prevents a fit. Keep ordering, non-overlapping footprints
        # with 1 cm clearance, and no split-level stance greater than 10 cm.
        feasible = [np.flatnonzero(f['valid']) for f in per_foot]
        independent = []
        if all(len(v) for v in feasible):
            left = per_foot[0]['feet'][feasible[0]]
            right = per_foot[1]['feet'][feasible[1]]
            delta = right[None, :, :]-left[:, None, :]
            boot = crew['boots'][0]
            size = (np.asarray(boot['maximum_cm'])-boot['minimum_cm'])*boot['scale']
            valid_pair = ((delta[:, :, 1] >= 4.) & (np.abs(delta[:, :, 2]) <= 10.) &
                          ((delta[:, :, 1] >= size[1]+1.) | (np.abs(delta[:, :, 0]) >= size[0]+1.)))
            costs = np.linalg.norm(centers[feasible[0], :2], axis=1)[:, None] + np.linalg.norm(centers[feasible[1], :2], axis=1)[None, :]
            costs[~valid_pair] = np.inf
            for flat in np.argsort(costs, axis=None)[:3]:
                l, r = np.unravel_index(flat, costs.shape)
                if not np.isfinite(costs[l, r]):
                    break
                independent.append(dict(feet_local_cm=[left[l].tolist(), right[r].tolist()],
                    spans_cm=[float(per_foot[0]['span'][feasible[0][l]]), float(per_foot[1]['span'][feasible[1][r]])],
                    displacement_cost_cm=float(costs[l, r])))
        results.append(dict(crew=crew['name'], origin_cm=crew['origin_cm'],
            independently_feasible=[int(f['valid'].sum()) for f in per_foot],
            paired_feasible=len(ids), independent_pairs=independent, leg_lengths_cm=[[f['upper_cm'], f['lower_cm']] for f in per_foot],
            nearest=[dict(along_cm=float(centers[i, 0]), lateral_cm=float(centers[i, 1]),
                feet_local_cm=[f['feet'][i].tolist() for f in per_foot],
                spans_cm=[float(f['span'][i]) for f in per_foot]) for i in ids[:8]]))
    return results


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('geometry', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    raw = args.geometry.read_bytes()
    results = analyze(json.loads(raw))
    report = dict(schema='raftsim.crew_support_stance.v1', source_sha256=hashlib.sha256(raw).hexdigest(),
                  geometry=str(args.geometry.resolve()), accepted_for_play=False, results=results)
    with args.output.open('x', encoding='utf-8') as stream:
        json.dump(report, stream, indent=2, allow_nan=False)
        stream.write('\n')
    print(json.dumps(results, indent=2))
