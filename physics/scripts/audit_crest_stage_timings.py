"""Locate current crest CPU costs; instrumentation is not FPS or scene acceptance."""
import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import re
import statistics


STAGES = ('total_ms', 'selection_ms', 'targets_ms', 'vertices_ms', 'topology_ms',
          'normals_ms', 'sample_ms', 'assembly_ms', 'refine_input_ms')
COUNTS = ('rebuild', 'fine_vertices', 'xy_changed', 'indices_changed',
          'profile_changed', 'coarse_changed', 'shore_changed', 'detail_changed')
VERTEX_STAGES = ('copy_ms', 'midpoints_ms', 'history_ms')
ROW = re.compile(r'WaterCrest(Perf|Vertices) frame=(\d+) (.*)$')


def summarize(text, first=60, last=240, require_vertices=False):
    if first < 0 or last < first:
        raise ValueError('Invalid inclusive frame interval')
    rows, vertices = [], []
    for line in text.splitlines():
        if not any(marker in line for marker in ('WaterCrestPerf frame=', 'WaterCrestVertices frame=')):
            continue
        match = ROW.search(line)
        if not match:
            raise ValueError('Malformed crest timing record')
        kind, frame, fields = match.groups()
        frame = int(frame)
        if not first <= frame <= last:
            continue
        pairs = [field.split('=') for field in fields.split()]
        if any(len(pair) != 2 for pair in pairs) or len({p[0] for p in pairs}) != len(pairs):
            raise ValueError('Malformed or duplicate field')
        values = dict(pairs)
        timing = STAGES if kind == 'Perf' else VERTEX_STAGES
        counts = COUNTS if kind == 'Perf' else ('dense', 'source_vertices', 'fine_vertices')
        if set(values) != set(timing + counts):
            raise ValueError('Missing or unknown timing fields')
        row = dict(frame=frame)
        for name in timing:
            value = float(values[name])
            if not math.isfinite(value) or value < 0:
                raise ValueError('Nonfinite or negative timing')
            row[name] = value
        for name in counts:
            value = int(values[name])
            if value < 0 or (not name.endswith('_vertices') and value not in (0, 1)):
                raise ValueError('Invalid native count or Boolean')
            row[name] = value
        (rows if kind == 'Perf' else vertices).append(row)
    frames = [r['frame'] for r in rows]
    if sorted(set(frames)) != list(range(first, last + 1)) or frames != sorted(frames):
        raise ValueError('Complete ordered frame coverage required')
    # Multiple calls within a frame remain real work: preserve and aggregate,
    # never silently retain only the final call or match by frame alone.
    if require_vertices or vertices:
        if [(r['frame'], r['fine_vertices']) for r in vertices] != [(r['frame'], r['fine_vertices']) for r in rows]:
            raise ValueError('Every crest call needs its corresponding vertex subdivision')
    def means(group, keys):
        return {key: statistics.mean(row[key] for row in group) for key in keys} if group else None
    result = dict(frame_range_inclusive=[first, last], frames=last-first+1, calls=len(rows),
                  calls_per_frame=dict(sorted(Counter(frames).items())),
                  per_call_mean_ms=means(rows, STAGES),
                  rebuilt=dict(calls=sum(r['rebuild'] for r in rows),
                               mean_ms=means([r for r in rows if r['rebuild']], STAGES)),
                  retained=dict(calls=sum(not r['rebuild'] for r in rows),
                                mean_ms=means([r for r in rows if not r['rebuild']], STAGES)),
                  changed_xy_without_profile=sum(r['xy_changed'] and not r['profile_changed'] for r in rows),
                  vertex_subdivision=None, release_accepted=False, visual_accepted=False,
                  scope='Instrumented current CPU work only. Nested stages overlap. No speedup, ordinary FPS or scene acceptance.')
    if vertices:
        result['vertex_subdivision'] = dict(per_call_mean_ms=means(vertices, VERTEX_STAGES),
            dense=dict(calls=sum(r['dense'] for r in vertices),
                       mean_ms=means([r for r in vertices if r['dense']], VERTEX_STAGES)),
            mapped=dict(calls=sum(not r['dense'] for r in vertices),
                        mean_ms=means([r for r in vertices if not r['dense']], VERTEX_STAGES)))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('log', type=Path)
    parser.add_argument('--first-frame', type=int, default=60)
    parser.add_argument('--last-frame', type=int, default=240)
    parser.add_argument('--require-vertices', action='store_true')
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    raw = args.log.read_bytes()
    report = summarize(raw.decode('utf-8-sig'), args.first_frame, args.last_frame, args.require_vertices)
    report.update(schema='raftsim.crest_stage_timings.v1', log=str(args.log.resolve()),
                  sha256=hashlib.sha256(raw).hexdigest())
    with args.report.open('x', encoding='utf-8') as output:
        json.dump(report, output, indent=2, allow_nan=False)
    print(json.dumps({k: v for k, v in report.items() if k != 'calls_per_frame'}, indent=2))


if __name__ == '__main__':
    main()
