"""Retain every actual crest-update call, including repeated calls in one frame."""
import argparse
from collections import defaultdict
import hashlib
import json
import math
from pathlib import Path
import re
import statistics


def stats(values):
    values = sorted(values)
    return dict(count=len(values), mean=statistics.mean(values), median=statistics.median(values),
                p95=values[math.ceil(.95*len(values))-1], maximum=values[-1])


def analyze(text, first, last, require_hash=False):
    if 'CrestHistoryHashAudit mismatch' in text:
        raise ValueError('Actual vertex/history mismatch')
    calls = []
    tag = 'CrestHistoryHashAudit exact' if require_hash else 'WaterCrestPerf'
    for line in text.splitlines():
        if tag not in line: continue
        fields = dict(re.findall(r'(\w+)=([-+0-9.eE]+)', line.split(tag, 1)[1]))
        frame = int(fields['frame'])
        if not first <= frame <= last: continue
        row = {k: float(v) for k, v in fields.items()}
        if not all(math.isfinite(v) for v in row.values()): raise ValueError('Nonfinite field')
        if any(v < 0 for k,v in row.items() if k.endswith('_ms')): raise ValueError('Negative duration')
        row['frame'] = frame
        calls.append(row)
    frames = defaultdict(list)
    for row in calls: frames[row['frame']].append(row)
    if set(frames) != set(range(first,last+1)): raise ValueError('Missing requested frame')
    keys = set.intersection(*(set(row) for row in calls))
    keys = sorted(k for k in keys if k.endswith('_ms'))
    if not keys: raise ValueError('No timings')
    if require_hash:
        if not {'fast_ms','legacy_ms'} <= set(keys): raise ValueError('Missing paired timing')
        if any(row['fast_first'] != row['frame']%2 or row['vertices'] < 1 or row['dense'] not in (0,1) for row in calls):
            raise ValueError('Invalid actual-input comparison record')
    result = dict(frame_range=[first,last], distinct_frames=len(frames), total_calls=len(calls),
        repeated_call_frames={str(f):len(v) for f,v in frames.items() if len(v)>1},
        per_call={k:stats([row[k] for row in calls]) for k in keys},
        per_frame_sum={k:stats([sum(row[k] for row in rows) for rows in frames.values()]) for k in keys},
        all_logged_calls_retained=True, actual_hash_comparison=require_hash,
        performance_or_scene_accepted=False)
    if require_hash:
        result['paired_legacy_minus_fast_ms'] = stats([row['legacy_ms']-row['fast_ms'] for row in calls])
        result['by_order'] = {str(order):stats([row['legacy_ms']-row['fast_ms'] for row in calls if row['fast_first']==order]) for order in (0,1)}
        result['dense_calls'] = sum(int(row['dense']) for row in calls)
        result['verified_vertex_visits'] = sum(int(row['vertices']) for row in calls)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('log', type=Path)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--first', type=int, default=100)
    parser.add_argument('--last', type=int, default=250)
    parser.add_argument('--require-hash', action='store_true')
    args = parser.parse_args()
    assert not args.report.exists()
    raw = args.log.read_bytes()
    result = analyze(raw.decode('utf-8', errors='replace'),args.first,args.last,args.require_hash)
    result.update(log=str(args.log.resolve()), log_sha256=hashlib.sha256(raw).hexdigest(),
        limitations='Instrumented shared-load CPU timings. Sum calls only within the same scope/frame, never nested stages. '
        'Hash comparison alternates call order on the same inputs; it does not establish total frame-rate or physical acceptance.')
    with args.report.open('x') as stream: json.dump(result,stream,indent=2)
    print(json.dumps(result,indent=2))


if __name__ == '__main__': main()
