"""Strict paired exact-coordinate memo audit; diagnostic timing, never FPS."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re
from audit_crest_midpoint_profile import summary

ROW = re.compile(r'FlatMemoAudit exact frame=(\d+) vertices=(\d+) triangles=(\d+) '
                 r'map_ms=(\S+) flat_ms=(\S+) flat_first=(\d+) map_bytes=(\d+) flat_bytes=(\d+)')
UNCHANGED = re.compile(r'FlatMemoAudit unchanged frame=(\d+)')


def audit(log, first=120, last=250):
    if first < 0 or last < first:
        raise ValueError('Invalid interval')
    if 'FlatMemoAudit mismatch' in log:
        raise ValueError('Reconstruction mismatch')
    rows, unchanged = [], []
    for line in log.splitlines():
        if 'FlatMemoAudit exact' in line:
            m = ROW.search(line)
            if not m:
                raise ValueError('Malformed exact record')
            f, v, t, a, b, o, am, bm = m.groups()
            row = dict(frame=int(f), vertices=int(v), triangles=int(t), map_ms=float(a),
                       flat_ms=float(b), flat_first=int(o), map_bytes=int(am), flat_bytes=int(bm))
            if (row['flat_first'] != row['frame'] % 2 or min(row['vertices'], row['triangles'],
                    row['map_bytes'], row['flat_bytes']) <= 0 or
                    any(not math.isfinite(row[k]) or row[k] < 0 for k in ('map_ms', 'flat_ms'))):
                raise ValueError('Invalid counts, timing or order')
            if first <= row['frame'] <= last:
                rows.append(row)
        elif 'FlatMemoAudit unchanged' in line:
            m = UNCHANGED.search(line)
            if not m:
                raise ValueError('Malformed unchanged record')
            if first <= int(m[1]) <= last:
                unchanged.append(int(m[1]))
    if {r['frame'] for r in rows} | set(unchanged) != set(range(first, last + 1)):
        raise ValueError('Missing frame; unchanged calls must be explicit')
    if {r['flat_first'] for r in rows} != {0, 1}:
        raise ValueError('Actual builds in both call orders required')
    return dict(first_frame=first, last_frame=last, build_calls=len(rows), unchanged_calls=len(unchanged),
                exact_vertices=sum(r['vertices'] for r in rows), exact_triangles=sum(r['triangles'] for r in rows),
                per_call={k: summary([r[k] for r in rows]) for k in ('map_ms', 'flat_ms', 'map_bytes', 'flat_bytes')},
                benefit_ms=summary([r['map_ms']-r['flat_ms'] for r in rows]),
                call_order_benefit_ms={str(o): summary([r['map_ms']-r['flat_ms'] for r in rows
                                                       if r['flat_first'] == o]) for o in (0, 1)},
                ordinary_fps_accepted=False, visual_or_physics_accepted=False,
                scope='Independent warm maps, every actual build including duplicate calls; exact topology/XY. '
                      'Includes growth/reset costs. Memory is retained memo allocation, not whole-process memory.')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('log', type=Path)
    p.add_argument('--report', required=True, type=Path)
    a = p.parse_args()
    raw = a.log.read_bytes()
    result = audit(raw.decode('utf-8', errors='replace'))
    result.update(log=str(a.log.resolve()), log_sha256=hashlib.sha256(raw).hexdigest())
    with a.report.open('x') as f:
        json.dump(result, f, indent=2, allow_nan=False)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
