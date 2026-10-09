"""One water-surface profile for the whole Lower Pacuare run.

build_pacuare_evidence_grid.py anchors the surface where a contour level first
comes within a few metres of a bank, then spreads each drop between anchors
by the orthophoto whitewater share. A single window sees whitewater only
inside itself, so overlapping windows disagree by up to ~17 m where they
meet, and a window that does not reach far enough upstream finds a later
crossing of the same contour.

From a first pass of segment builds this writes one profile:
- anchors: every segment's crossings, keeping the upstream-most station per
  contour level (the builder's own rule, applied to the union of windows);
- whitewater share: each segment's share over the chainage it owns (where
  its window and photograph cover the river);
- the same drop distribution as the builder (pool weight + share).

The second pass passes this file to build_pacuare_evidence_grid.py
--ws-profile, so every segment's banks and inferred bed hang from one surface.
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def segment(folder):
    folder = Path(folder)
    manifest = json.loads((folder / 'manifest.json').read_text())
    profile = json.loads((folder / 'profile.json').read_text())
    centre = json.loads((folder / 'centreline.json').read_text())
    pts = np.asarray(centre['points_xy_station'], float)
    order = np.argsort(pts[:, 2])
    station, chain = pts[order, 2], np.asarray(centre['osm_chain_m'], float)[order]
    n = min(len(profile['station_center_m']), len(profile['whitewater_share']))
    share_chain = np.interp(np.asarray(profile['station_center_m'][:n], float), station, chain)
    return dict(folder=folder, range=manifest['parameters']['chain_m'], pool_weight=manifest['parameters']['pool_weight'],
                anchors=[(float(a['osm_chain_m']), float(a['elevation_m'])) for a in profile['anchors']],
                share_chain=share_chain, share=np.asarray(profile['whitewater_share'][:n], float),
                files={str(folder / name): sha(folder / name) for name in ('manifest.json', 'profile.json', 'centreline.json')})


def build(folders, out, step=1.0, extend_to=None):
    segs = sorted((segment(f) for f in folders), key=lambda s: s['range'][0])
    weights = {s['pool_weight'] for s in segs}
    if len(weights) != 1:
        raise ValueError('Segments disagree on the pool weight')
    pool_weight = weights.pop()
    bounds = [segs[0]['range'][0]] + [0.5 * (b['range'][0] + a['range'][1]) for a, b in zip(segs, segs[1:])] + [segs[-1]['range'][1]]
    # Anchors: upstream-most crossing per contour level across all windows.
    first = {}
    for s in segs:
        for chain, z in s['anchors']:
            first[z] = min(chain, first.get(z, np.inf))
    anchors = sorted((c, z) for z, c in first.items())
    kept = [anchors[0]]
    for c, z in anchors[1:]:
        if z < kept[-1][1] and c - kept[-1][0] > 20:
            kept.append((c, z))
    a_c = np.array([a[0] for a in kept])
    a_z = np.array([a[1] for a in kept])
    # Whitewater share over owned chainage.
    sc, sv = [], []
    for s, lo, hi in zip(segs, bounds, bounds[1:]):
        keep = (s['share_chain'] >= lo) & (s['share_chain'] < hi)
        sc.append(s['share_chain'][keep])
        sv.append(s['share'][keep])
    sc, sv = np.concatenate(sc), np.concatenate(sv)
    order = np.argsort(sc)
    chain = np.arange(np.floor(min(a_c[0], bounds[0])), np.ceil(max(a_c[-1], bounds[-1])) + step, step)
    share = np.interp(chain, sc[order], sv[order], left=0.0, right=0.0)
    w = pool_weight + share
    ws = np.full(len(chain), np.nan)
    index = np.searchsorted(chain, a_c)
    for i in range(len(a_c) - 1):
        j0, j1 = index[i], index[i + 1]
        c = np.concatenate([[0.0], np.cumsum(w[j0:j1])])
        ws[j0:j1 + 1] = a_z[i] - (a_z[i] - a_z[i + 1]) * c / c[-1]
    covered = np.isfinite(ws)
    chain, ws, share = chain[covered], ws[covered], share[covered]
    extension = None
    if extend_to is not None and extend_to > chain[-1]:
        # No contour crossing lies downstream of the last anchor within the
        # captured sources. Continue at the last interval's mean gradient
        # (inferred, labelled), rather than inventing an anchor.
        gradient = (a_z[-2] - a_z[-1]) / (a_c[-1] - a_c[-2])
        tail = np.arange(chain[-1] + step, extend_to + step, step)
        chain = np.r_[chain, tail]
        ws = np.r_[ws, ws[-1] - gradient * (tail - tail[0] + step)]
        share = np.r_[share, np.zeros(len(tail))]
        extension = dict(from_osm_chain_m=float(a_c[-1]), to_osm_chain_m=float(chain[-1]), gradient=float(gradient),
                         method='extrapolated beyond the last contour crossing at the last interval mean gradient')
    result = dict(schema='raftsim.pacuare.full_run_ws_profile.v1',
                  method='Upstream-most contour-level crossings over all segment windows; each drop spread by '
                         'pool weight + orthophoto whitewater share over owned chainage (inferred between anchors)',
                  pool_weight=pool_weight, extrapolation=extension, anchors=[dict(osm_chain_m=float(c), elevation_m=float(z)) for c, z in kept],
                  owned_chain_m=[[float(lo), float(hi)] for lo, hi in zip(bounds, bounds[1:])],
                  osm_chain_m=chain.round(2).tolist(), ws_m=ws.round(4).tolist(), whitewater_share=share.round(4).tolist(),
                  segments={k: v for s in segs for k, v in s['files'].items()})
    out = Path(out)
    if out.exists():
        raise ValueError('Fresh profile output required')
    out.write_text(json.dumps(result) + '\n')
    print(json.dumps(dict(anchors=result['anchors'], chain_m=[float(chain[0]), float(chain[-1])],
                          ws_m=[float(ws[0]), float(ws[-1])]), indent=1))
    return result


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('segments', nargs='+', type=Path)
    p.add_argument('--out', required=True, type=Path)
    p.add_argument('--extend-to-chain-m', type=float,
                   help='continue past the last anchor to this OSM chainage at the last interval gradient (labelled)')
    a = p.parse_args()
    build(a.segments, a.out, extend_to=a.extend_to_chain_m)
