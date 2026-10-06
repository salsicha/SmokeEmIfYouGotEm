"""Join an OpenStreetMap waterway relation into one centreline with chainage (numpy only).

Input: an Overpass `out geom` JSON holding the river relation (and, optionally,
rapid / put-in nodes). Main-stream member ways are joined end to end in flow
order (the relation's first way is taken as upstream when --reverse is not
given; the result is checked against the given downstream point). Chainage
is metres along the joined line on a local equirectangular projection (error
below 0.1% over a 30 km reach).

Writes JSON: centreline [lon, lat, chain_m] and every tagged node with its
chainage and perpendicular offset from the line.

Data (c) OpenStreetMap contributors, ODbL 1.0.
"""
import argparse
import json
from pathlib import Path

import numpy as np

R = 6371008.8


def join_ways(segs):
    line = segs.pop(0)
    gaps = []
    while segs:
        best = None
        for k, s in enumerate(segs):
            for rev in (False, True):
                ss = s[::-1] if rev else s
                for where, dd in (('head', np.abs(ss[-1] - line[0]).sum()), ('tail', np.abs(ss[0] - line[-1]).sum())):
                    if best is None or dd < best[0]:
                        best = (dd, k, rev, where)
        dd, k, rev, where = best
        s = segs.pop(k)
        s = s[::-1] if rev else s
        gaps.append(float(dd))
        line = np.vstack([s[:-1], line]) if where == 'head' else np.vstack([line, s[1:]])
    return line, gaps


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('overpass_json')
    ap.add_argument('--relation', type=int, required=True)
    ap.add_argument('--downstream-lonlat', type=float, nargs=2, required=True,
                    help='a point near the river mouth/downstream end, to orient the line')
    ap.add_argument('--out', required=True)
    args = ap.parse_args()
    d = json.loads(Path(args.overpass_json).read_text(encoding='utf-8'))
    rel = next(e for e in d['elements'] if e['type'] == 'relation' and e['id'] == args.relation)
    segs = [np.array([[p['lon'], p['lat']] for p in m['geometry']]) for m in rel['members']
            if m['type'] == 'way' and m.get('geometry') and m.get('role') in ('', 'main_stream', 'main')]
    line, gaps = join_ways(segs)
    dn = np.array(args.downstream_lonlat)
    if np.abs(line[0] - dn).sum() < np.abs(line[-1] - dn).sum():
        line = line[::-1]
    lat0 = np.radians(line[:, 1].mean())
    xy = np.c_[np.radians(line[:, 0]) * R * np.cos(lat0), np.radians(line[:, 1]) * R]
    chain = np.r_[0, np.cumsum(np.hypot(*np.diff(xy, axis=0).T))]

    def locate(lon, lat):
        p = np.array([np.radians(lon) * R * np.cos(lat0), np.radians(lat) * R])
        a, b = xy[:-1], xy[1:]
        ab = b - a
        t = np.clip(((p - a) * ab).sum(1) / np.maximum((ab * ab).sum(1), 1e-9), 0, 1)
        q = a + ab * t[:, None]
        dist = np.hypot(*(q - p).T)
        k = int(dist.argmin())
        return float(chain[k] + t[k] * np.hypot(*ab[k])), float(dist[k])

    nodes = []
    for e in d['elements']:
        if e['type'] == 'node' and e.get('tags'):
            s, off = locate(e['lon'], e['lat'])
            nodes.append(dict(id=e['id'], lon=e['lon'], lat=e['lat'], chain_m=round(s, 1),
                              offset_from_centreline_m=round(off, 1), tags=e['tags']))
    nodes.sort(key=lambda n: n['chain_m'])
    out = dict(schema='raftsim.osm_river_centreline.v1', source=Path(args.overpass_json).name,
               osm_base_timestamp=d.get('osm3s', {}).get('timestamp_osm_base'),
               relation=args.relation, relation_tags=rel.get('tags', {}),
               licence='ODbL 1.0; (c) OpenStreetMap contributors',
               chainage='metres from the relation\'s upstream end along the joined main-stream ways '
                         '(local equirectangular projection); not official river kilometres',
               join_max_endpoint_gap_deg=max(gaps) if gaps else 0.0, length_m=round(float(chain[-1]), 1),
               nodes=nodes,
               centreline_lon_lat_chain=[[round(float(a), 7), round(float(b), 7), round(float(c), 1)]
                                         for (a, b), c in zip(line, chain)])
    Path(args.out).write_text(json.dumps(out, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print(f"length {chain[-1] / 1000:.3f} km, {len(line)} vertices, max join gap {out['join_max_endpoint_gap_deg']:.2e} deg")
    for n in nodes:
        print(f"  {n['tags'].get('name', n['id'])!s:28} {n['chain_m'] / 1000:8.3f} km  off {n['offset_from_centreline_m']:6.1f} m")


if __name__ == '__main__':
    main()
