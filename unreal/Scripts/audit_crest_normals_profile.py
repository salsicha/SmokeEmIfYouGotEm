"""Audit paired, same-input crest normal timings without claiming overall FPS."""
import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import re
from audit_crest_history_profile import stats


def analyze(text, first=120, last=250):
    if first < 0 or last < first:
        raise ValueError('Invalid frame interval')
    if 'CrestNormalsAudit mismatch' in text:
        raise ValueError('Actual attribute mismatch')
    rows = []
    for line in text.splitlines():
        if 'CrestNormalsAudit exact' not in line:
            continue
        fields = dict(re.findall(r'(\w+)=([-+0-9.eE]+)', line.split('CrestNormalsAudit exact', 1)[1]))
        row = {key: float(value) for key, value in fields.items()}
        required = {'frame', 'vertices', 'triangles', 'rebuilt', 'serial_ms', 'parallel_ms', 'parallel_first'}
        if not required <= row.keys() or not all(math.isfinite(value) and value >= 0 for value in row.values()):
            raise ValueError('Invalid timing record')
        if any(row[key] != int(row[key]) for key in required-{'serial_ms', 'parallel_ms'}):
            raise ValueError('Noninteger counter')
        if row['parallel_first'] != int(row['frame']) % 2 or row['rebuilt'] not in (0, 1):
            raise ValueError('Wrong call order or rebuild flag')
        if row['vertices'] == 0 or row['triangles'] == 0 or min(row['serial_ms'], row['parallel_ms']) <= 0:
            raise ValueError('Empty mesh or unavailable timing')
        if first <= row['frame'] <= last:
            rows.append(row)
    counts = Counter(int(row['frame']) for row in rows)
    if set(counts) != set(range(first, last+1)):
        raise ValueError('Missing requested frame')
    def summarize(group):
        return dict(calls=len(group), serial_ms=stats([row['serial_ms'] for row in group]),
            parallel_ms=stats([row['parallel_ms'] for row in group]),
            serial_minus_parallel_ms=stats([row['serial_ms']-row['parallel_ms'] for row in group])) if group else None
    return dict(schema='raftsim.crest_normals_paired_profile.v1', scene_or_fps_accepted=False,
        frames=[first, last], paired_calls=len(rows),
        repeated_frame_calls={str(key): count for key, count in counts.items() if count > 1},
        vertex_attribute_comparisons=sum(int(row['vertices']) for row in rows),
        all_calls=summarize(rows),
        by_parallel_call_order={str(order): summarize([row for row in rows if row['parallel_first'] == order]) for order in (0, 1)},
        by_topology_rebuilt={str(rebuilt): summarize([row for row in rows if row['rebuilt'] == rebuilt]) for rebuilt in (0, 1)},
        scope='Same live input; every vertex attribute compared exactly. Repeated calls retained. Alternating call order includes cache rebuild cost. Diagnostic runs execute both paths and cannot establish ordinary FPS, sustained speed, water realism, physical or release acceptance.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('log', type=Path)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    raw = args.log.read_bytes()
    result = analyze(raw.decode('utf-8', errors='replace'))
    result.update(log=str(args.log.resolve()), log_sha256=hashlib.sha256(raw).hexdigest())
    with args.report.open('x', encoding='utf-8') as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
