"""Separate counted crest-update cadence from inclusive CPU cost, not FPS causality."""
import argparse
import csv
import hashlib
import io
import json
import math
from pathlib import Path

from audit_unreal_frame_csv import parse_capture

PREFIX = 'RaftSimCrests/'
COUNTERS = ('UpdateCalls', 'XYChanged', 'IndicesChanged', 'ProfileChanged',
            'DetailWindowChanged', 'CoarseChanged', 'ShoreChanged', 'DenseHistoryUpdates')
GEOMETRY = ('XYChanged', 'IndicesChanged', 'ProfileChanged', 'DetailWindowChanged')
SCOPES = ('RaftSimCrests/GameThread/Update', 'RaftSimSurface/GameThread/Tick',
          'RaftSimSurface/GameThread/Refresh', 'RaftSimCrests/GameThread/Selection')


def check(value, message):
    if not value:
        raise ValueError(message)


def read_capture(raw, ignored=()):
    text = raw.decode('utf-8-sig')
    validated, metadata = parse_capture(io.StringIO(text), True, ignored)
    rows = list(csv.reader(io.StringIO(text)))
    end = next(i for i in range(1, len(rows)) if rows[i] and rows[i][0] == 'EVENTS')
    header = rows[end]
    fields = tuple(PREFIX + n for n in COUNTERS) + SCOPES
    check(all(header.count(n) == 1 for n in fields), 'Missing/ambiguous crest counters or scopes')
    indices = {n: header.index(n) for n in fields}
    result = []
    for row in rows[1:end]:
        if not row:
            continue
        # A late-added counter missing in an early row is unavailable, not zero.
        check(all(i < len(row) for i in indices.values()), 'Counter absent in an early row')
        result.append({n: float(row[i]) for n, i in indices.items()})
    check(len(result) == len(validated), 'CSV sample identity mismatch')
    return result, metadata


def classify(row):
    for name in SCOPES:
        value = row.get(name)
        check(type(value) in (int, float) and math.isfinite(value) and value >= 0,
              'Invalid CPU scope')
    for name in COUNTERS:
        value = row.get(PREFIX + name)
        check(type(value) in (int, float) and math.isfinite(value) and value >= 0
              and int(value) == value, 'Invalid count')
    calls = row[PREFIX + 'UpdateCalls']
    check(all(row[PREFIX + n] <= calls for n in COUNTERS[1:]), 'Change count exceeds calls')
    if calls == 0:
        return 'no_counted_update'
    if calls > 1:
        return 'multiple_updates_unresolved'
    if any(row[PREFIX + n] for n in GEOMETRY):
        return 'single_geometry_changed'
    if any(row[PREFIX + n] for n in ('CoarseChanged', 'ShoreChanged')):
        return 'single_targets_changed'
    return 'single_targets_unchanged'


def summarize(rows, first, last):
    check(0 <= first <= last < len(rows), 'Absent sample interval')
    selected = rows[first:last + 1]
    groups = {}
    joint = {}
    for row in selected:
        category = classify(row)
        groups.setdefault(category, []).append(row)
        refresh = 'refresh_measured' if row[SCOPES[2]] > 0 else 'no_refresh_measured'
        joint.setdefault(category + '__' + refresh, []).append(row)

    def aggregate(samples):
        calls = sum(r[PREFIX + 'UpdateCalls'] for r in samples)
        return dict(frames=len(samples), update_calls=int(calls),
            calls_per_frame=calls / len(samples),
            counters={n: int(sum(r[PREFIX + n] for r in samples)) for n in COUNTERS},
            cpu={n: dict(total_ms=sum(r[n] for r in samples),
                         mean_ms_per_frame=sum(r[n] for r in samples) / len(samples),
                         aggregate_ms_per_crest_call=(sum(r[n] for r in samples) / calls
                                                     if calls and n == SCOPES[0] else None))
                 for n in SCOPES})
    return dict(sample_indices_inclusive=[first, last], aggregate=aggregate(selected),
                categories={n: aggregate(v) for n, v in sorted(groups.items())},
                joint_refresh_categories={n: aggregate(v) for n, v in sorted(joint.items())})


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('capture', type=Path)
    p.add_argument('--interval', nargs=2, type=int, action='append', required=True)
    p.add_argument('--ignore-duplicate-unmeasured-header', action='append', default=[])
    p.add_argument('--report', type=Path, required=True)
    a = p.parse_args()
    raw = a.capture.read_bytes()
    rows, metadata = read_capture(raw, a.ignore_duplicate_unmeasured_header)
    report = dict(schema='raftsim.crest_update_cadence.v2', source=str(a.capture.resolve()),
        source_sha256=hashlib.sha256(raw).hexdigest(), metadata=metadata,
        scope='Same-row counted calls/change flags and inclusive CPU scopes. Positive Refresh scope means measured refresh work, not a refresh-call count. Multiple crest calls cannot be individually classified. Parent surface Tick includes crest and refresh work; never sum them. No frame-time causal attribution, geometry-size normalization, speedup or acceptance.',
        performance_accepted=False, intervals=[summarize(rows, *v) for v in a.interval])
    with a.report.open('x', encoding='utf-8') as output:
        json.dump(report, output, indent=2)
        output.write('\n')
    print(f'Classified {len(a.interval)} retained CPU/cadence intervals; no acceptance inferred')


if __name__ == '__main__':
    main()
