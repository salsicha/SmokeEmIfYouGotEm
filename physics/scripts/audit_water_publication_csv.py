"""Attribute water publication CPU work by counted caller, not timing correlation."""
import argparse
import csv
import hashlib
import io
import json
import math
from pathlib import Path

from audit_unreal_frame_csv import parse_capture

PREFIX = 'RaftSimSurface/'
REASONS = ('PublishInterpolation', 'PublishRecenter', 'PublishCreate', 'PublishHardSwap')
COUNTERS = ('PublishCalls',) + REASONS + ('RecenterWorkCalls',
             'CarryRenderedHistoryCalls', 'PlanarGeometryCalls')
PAIRED = dict(zip(REASONS, ('InterpolationPublication', 'RecenterPublication',
                          'CreatePublication', 'HardSwapPublication')))
PAIRED.update(RecenterWorkCalls='RecenterWork',
              CarryRenderedHistoryCalls='CarryRenderedHistory',
              PlanarGeometryCalls='PlanarGeometry')
SCOPES = tuple(PREFIX+'GameThread/'+n for n in PAIRED.values()) + (
    PREFIX+'GameThread/RecenterStateHistory', PREFIX+'GameThread/Tick',
    PREFIX+'GameThread/Refresh', 'RaftSimCrests/GameThread/Update')


def read_capture(raw, ignored=()):
    text = raw.decode('utf-8-sig')
    validated, metadata = parse_capture(io.StringIO(text), False, ignored)
    # The validated final header names appended series. An absent early cell
    # remains absent, never zero. The requested interval is checked below.
    records = list(csv.reader(io.StringIO(text)))
    end = next(i for i in range(1, len(records)) if records[i] and records[i][0] == 'EVENTS')
    header = records[end]
    names = tuple(PREFIX+n for n in COUNTERS) + SCOPES
    if any(header.count(n) > 1 for n in names):
        raise ValueError('Ambiguous publication series')
    indices = {n: header.index(n) for n in names if n in header}
    rows = [{n: float(row[i]) for n,i in indices.items() if i < len(row)}
            for row in records[1:end] if row]
    if len(rows) != len(validated):
        raise ValueError('Publication sample identity mismatch')
    return rows, metadata


def summarize(rows, first, last):
    if not 0 <= first <= last < len(rows):
        raise ValueError('Requested publication interval is absent')
    selected = rows[first:last+1]
    for row in selected:
        for name in COUNTERS:
            value = row.get(PREFIX+name)
            if type(value) not in (int, float) or not math.isfinite(value) or value < 0 or int(value) != value:
                raise ValueError('Missing/invalid publication count: '+name)
        if row[PREFIX+'PublishCalls'] != sum(row[PREFIX+n] for n in REASONS):
            raise ValueError('Caller reasons do not partition publication attempts')
        for name in SCOPES:
            if name in row and (type(row[name]) not in (int, float) or not math.isfinite(row[name]) or row[name] < 0):
                raise ValueError('Invalid publication CPU scope')
        for count, scope in PAIRED.items():
            if row[PREFIX+count] > 0 and PREFIX+'GameThread/'+scope not in row:
                raise ValueError('Active publication/recenter call has no measured scope')

    def aggregate(group):
        timings = {}
        for name in SCOPES:
            values = [r[name] for r in group if name in r]
            timings[name] = dict(available_rows=len(values),
                total_ms=sum(values) if values else None,
                mean_available_ms=sum(values)/len(values) if values else None)
        return dict(frames=len(group), counts={n:int(sum(r[PREFIX+n] for r in group))
                    for n in COUNTERS}, cpu=timings)

    groups = {}
    events = []
    for i,row in enumerate(selected, first):
        signature = '+'.join(n for n in REASONS if row[PREFIX+n]) or 'no_publication'
        groups.setdefault(signature, []).append(row)
        if row[PREFIX+'PublishCalls'] > 1 or row[PREFIX+'RecenterWorkCalls'] > 0:
            events.append(dict(sample_index=i, counts={n:int(row[PREFIX+n]) for n in COUNTERS},
                               cpu_ms={n:row[n] for n in SCOPES if n in row}))
    return dict(sample_indices_inclusive=[first,last], aggregate=aggregate(selected),
                caller_groups={n:aggregate(v) for n,v in sorted(groups.items())}, events=events)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('capture', type=Path)
    p.add_argument('--first-sample', type=int, default=30)
    p.add_argument('--last-sample', type=int, default=1169)
    p.add_argument('--ignore-duplicate-unmeasured-header', action='append', default=[])
    p.add_argument('--report', required=True, type=Path)
    a = p.parse_args()
    raw = a.capture.read_bytes()
    rows, metadata = read_capture(raw, a.ignore_duplicate_unmeasured_header)
    result = summarize(rows, a.first_sample, a.last_sample)
    report = dict(schema='raftsim.water_publication_cpu.v1', source=str(a.capture.resolve()),
        source_sha256=hashlib.sha256(raw).hexdigest(), metadata=metadata,
        performance_accepted=False, result=result,
        scope='Same-row counted publication attempts and inclusive CPU scopes, not successful GPU submissions. '
              'RecenterWork includes planar mapping and state history; caller publication scopes include CartesianPublish/crest work. '
              'Never add nested scopes. Absent scope rows are unavailable, not zero. '
              'No FrameTime phase attribution, removed frames, causal speedup or visual acceptance.')
    with a.report.open('x', encoding='utf-8') as out:
        json.dump(report,out,indent=2)
        out.write('\n')
    print(f"Audited {result['aggregate']['frames']} CPU rows and {len(result['events'])} publication/recenter events; no acceptance")


if __name__ == '__main__':
    main()
