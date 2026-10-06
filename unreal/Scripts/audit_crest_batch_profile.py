"""Compare scheduling variants on identical live profile builds, retaining all calls."""
import argparse
from collections import defaultdict
import hashlib
import json
import math
from pathlib import Path
import re
from audit_crest_history_profile import stats

SIZES = (128, 32, 64, 256, 512)


def analyze(text, first=120, last=250):
    if first < 0 or last < first:
        raise ValueError('Invalid frame interval')
    if 'CrestBatchAudit mismatch' in text:
        raise ValueError('Actual topology mismatch')
    groups = []
    pending = []
    unchanged = defaultdict(int)
    for line in text.splitlines():
        if 'CrestBatchAudit unchanged' in line:
            if pending:
                raise ValueError('Incomplete group before unchanged record')
            match = re.search(r'CrestBatchAudit unchanged frame=(\d+)', line)
            if not match:
                raise ValueError('Invalid unchanged record')
            frame = int(match[1])
            if first <= frame <= last:
                unchanged[frame] += 1
            continue
        if 'CrestBatchAudit exact' not in line:
            continue
        fields = dict(re.findall(r'(\w+)=([-+0-9.eE]+)', line.split('CrestBatchAudit exact', 1)[1]))
        row = {k: float(v) for k, v in fields.items()}
        required = {'frame', 'batch', 'order', 'total_ms', 'selection_ms', 'vertices', 'triangles', 'memo_bytes'}
        if not required <= row.keys() or not all(math.isfinite(v) and v >= 0 for v in row.values()):
            raise ValueError('Invalid timing record')
        if any(row[k] != int(row[k]) for k in ('frame', 'batch', 'order', 'vertices', 'triangles', 'memo_bytes')):
            raise ValueError('Noninteger counter')
        index = len(pending)
        if row['batch'] != SIZES[index] or row['order'] != (index + 5 - int(row['frame']) % 5) % 5:
            raise ValueError('Wrong variant/order')
        if pending and any(row[k] != pending[0][k] for k in ('frame', 'vertices', 'triangles')):
            raise ValueError('Mismatched input group')
        pending.append(row)
        if len(pending) == 5:
            if first <= row['frame'] <= last:
                groups.append(pending)
            pending = []
    if pending:
        raise ValueError('Incomplete group')
    counts = defaultdict(int)
    for group in groups:
        counts[int(group[0]['frame'])] += 1
    if set(counts) | set(unchanged) != set(range(first, last + 1)):
        raise ValueError('Missing requested frame')
    if not groups:
        raise ValueError('No actual selection builds')
    variants = {}
    for i, size in enumerate(SIZES):
        rows = [group[i] for group in groups]
        orders = {}
        for position in range(5):
            differences = [g[0]['total_ms'] - g[i]['total_ms'] for g in groups if g[i]['order'] == position]
            orders[str(position)] = stats(differences) if differences else None
        variants[str(size)] = dict(
            total_ms=stats([r['total_ms'] for r in rows]),
            selection_ms=stats([r['selection_ms'] for r in rows]),
            memo_bytes=stats([r['memo_bytes'] for r in rows]),
            baseline_minus_variant_ms=stats([g[0]['total_ms'] - g[i]['total_ms'] for g in groups]),
            difference_by_variant_order=orders)
    return dict(frame_range=[first, last], frames=len(set(counts) | set(unchanged)), input_groups=len(groups),
                unchanged_geometry_calls={str(k): v for k, v in unchanged.items()},
                repeated_frame_groups={str(k): v for k, v in counts.items() if v > 1},
                expanded_vertex_visits=sum(int(g[0]['vertices']) for g in groups),
                variants=variants, performance_or_scene_accepted=False,
                limitations='Exact per-build topology and XY, not physical-wave validation. All variants run in one shared-load frame. '
                'Rotating call order, independently retained memo state. Total timings include selection; do not sum them. '
                'These diagnostic frame times are not ordinary-game FPS. Memory reports memo allocation only.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('log', type=Path)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    raw = args.log.read_bytes()
    result = analyze(raw.decode('utf-8', errors='replace'))
    result.update(log=str(args.log.resolve()), log_sha256=hashlib.sha256(raw).hexdigest())
    with args.report.open('x') as stream:
        json.dump(result, stream, indent=2)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
