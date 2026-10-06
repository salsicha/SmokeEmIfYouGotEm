"""Summarize an actual Unreal CSV capture without claiming release acceptance."""
import argparse
import csv
import hashlib
import json
import math
import statistics
from collections import Counter
from pathlib import Path

METRICS = ("FrameTime", "GameThreadTime", "RenderThreadTime", "RHIThreadTime", "GPUTime")
WATER_SCOPES = ("RaftSimSurface/GameThread/Tick", "RaftSimSurface/GameThread/Refresh",
                "RaftSimSurface/GameThread/SourceSamples", "RaftSimSurface/GameThread/SourceHandover",
                "RaftSimSurface/GameThread/CartesianPublish", "RaftSimCrests/GameThread/Update",
                "RaftSimCrests/GameThread/Selection", "RaftSimSolver/GameThread/StepWater")
PUBLISH_SCOPES = ("RaftSimSurface/GameThread/PackSource", "RaftSimShoreline/GameThread/SetMesh",
                  "RaftSimShoreline/GameThread/Topology", "RaftSimShoreline/GameThread/CrestInput",
                  "RaftSimCrests/GameThread/Normals", "RaftSimShoreline/GameThread/RenderPacket",
                  "RaftSimShoreline/GameThread/CrestSourceGather",
                  "RaftSimShoreline/GameThread/OutputStorage",
                  "RaftSimShoreline/GameThread/BoundsAndNotify")
SMOOTHING_SCOPES = ("RaftSimSurface/GameThread/OpticalFilter",)
# Optional in historical captures; absence must not be reported as zero cost.
BREAKING_SCOPES = ("RaftSimSurface/GameThread/BreakingVertices",)
FOAM_SCOPES = ("RaftSimSurface/GameThread/FoamTransport",)
GROUND_SCOPES = ("RaftSimGround/GameThread/Sample", "RaftSimGround/GameThread/SurfaceSweep",
                 "RaftSimHull/GameThread/Prepare", "RaftSimHull/GameThread/Render")
RELIEF_SCOPES = ("RaftSimSurface/GameThread/HydraulicRelief",)
CLOCK_COUNTERS = tuple('RaftSimClock/' + name for name in (
    'RequestedSeconds', 'CommittedSeconds', 'BacklogSeconds', 'FixedTicks',
    'Failed', 'NativeFieldSeconds', 'WaterCommittedSeconds'))
METADATA = {"config", "engineversion", "deviceprofile", "rhiname", "raytracing",
            "systemresolution.resx", "systemresolution.resy", "targetframerate"}


def parse_capture(stream, require_water_scopes=False, ignore_duplicate_unmeasured_headers=()):
    measured = METRICS + WATER_SCOPES + PUBLISH_SCOPES + SMOOTHING_SCOPES + BREAKING_SCOPES + FOAM_SCOPES + GROUND_SCOPES + RELIEF_SCOPES + CLOCK_COUNTERS
    ignored = set(ignore_duplicate_unmeasured_headers)
    if ignored.intersection(measured) or any(not name or name.startswith('[') or name == 'EVENTS' for name in ignored):
        raise ValueError('only explicitly named unmeasured counters may be ignored')

    def validate_header(names):
        counts = Counter(names or ())
        duplicates = {name for name, count in counts.items() if count > 1}
        if not names or duplicates - ignored:
            raise ValueError('missing or duplicate CSV headers')
        return duplicates

    reader = csv.reader(stream)
    header = next(reader, None)
    validate_header(header)
    missing = set(METRICS) - set(header)
    if missing:
        raise ValueError(f"missing actual frame metrics: {sorted(missing)}")
    if require_water_scopes and set(WATER_SCOPES) - set(header):
        raise ValueError("capture is missing required water scope columns")
    columns = {name: header.index(name) for name in measured if name in header}
    samples, metadata = [], {}
    footer = False
    completed_metadata = False
    width = len(header)
    for row in reader:
        if not row:
            continue
        if row[:len(header)] == header:
            # Unreal FCsvStreamWriter appends series during continuous output, then
            # writes their complete header. Original metric positions cannot
            # change. Missing metrics are never filled with invented zeroes.
            if footer or not samples or len(row) != width:
                raise ValueError("unexpected repeated header")
            duplicates = validate_header(row)
            if ignored - duplicates:
                raise ValueError('explicitly ignored duplicate is absent from completed header')
            if duplicates:
                # Keep every original column and row in place. Never select,
                # combine, rename or report the ambiguous counters as metrics.
                metadata['ignored_duplicate_unmeasured_headers'] = {
                    name: [i for i, value in enumerate(row) if value == name]
                    for name in sorted(duplicates)}
            footer = True  # Unreal's explicit trailing header, not another run.
            continue
        if row[0] == "[HasHeaderRowAtEnd]":
            if not footer or completed_metadata or len(row) < 2 or row[1] != "1":
                raise ValueError("invalid or incomplete capture footer")
            completed_metadata = True
            for i in range(0, len(row) - 1, 2):
                key = row[i].strip("[]").lower()
                if key in METADATA:
                    metadata[key] = row[i + 1]
            footer = True
            continue
        if footer or len(row) < width:
            raise ValueError("unexpected row or truncated CSV capture")
        width = len(row)
        values = {name: float(row[index]) for name, index in columns.items()}
        if any(not math.isfinite(v) or v < 0 for v in values.values()):
            raise ValueError("invalid frame metric")
        samples.append(values)
    if not samples or not footer or not completed_metadata:
        raise ValueError("capture has no samples or no completed footer")
    return samples, metadata


def summarize(samples, first, last, target_fps=20.0):
    if not math.isfinite(target_fps) or target_fps <= 0:
        raise ValueError("target FPS must be finite and positive")
    if first < 0 or last < first or last >= len(samples):
        raise ValueError("requested sample interval is absent")
    selected = samples[first:last + 1]
    if any(s["FrameTime"] <= 0 for s in selected):
        raise ValueError("selected frames have no measured elapsed time")
    result = {}
    for name in METRICS + WATER_SCOPES + PUBLISH_SCOPES + SMOOTHING_SCOPES + BREAKING_SCOPES + FOAM_SCOPES + GROUND_SCOPES + RELIEF_SCOPES:
        if name not in selected[0]:
            continue  # Absent scope is unavailable, never inferred to be zero.
        values = [s[name] for s in selected]
        ordered = sorted(values)
        active = [v for v in values if v > 0]
        result[name] = {"count": len(values), "positive_sample_count": len(active),
                        "mean_ms": statistics.mean(values),
                        "mean_positive_ms": statistics.mean(active) if active else None,
                        "median_ms": statistics.median(values),
                        "p95_ms_nearest_rank": ordered[math.ceil(.95 * len(values)) - 1],
                        "maximum_ms": max(values), "all_positive": min(values) > 0,
                        "variable": min(values) != max(values)}
    result["elapsed_frame_fps"] = 1000. / result["FrameTime"]["mean_ms"]
    result["target_fps"] = target_fps
    result["frame_budget_ms"] = 1000. / target_fps
    result["frame_p95_within_target_budget"] = result["FrameTime"]["p95_ms_nearest_rank"] <= result["frame_budget_ms"]
    return result


def summarize_water_clock(samples, first, last):
    """Audit clock capacity separately from ms timings and visual acceptance.

    These are same-row cumulative counters, not elapsed FrameTime scopes. No
    temporal offset is selected by correlation. Native time may have an origin
    offset after initialization/handoff; report it rather than demanding zero.
    """
    if not (0 <= first <= last < len(samples)):
        raise ValueError('Clock interval is outside captured samples')
    selected = samples[first:last + 1]
    present = [set(row).intersection(CLOCK_COUNTERS) for row in selected]
    if not any(present):
        return dict(available=False, simulation_capacity_accepted=False,
                    reason='Clock counters absent; frame timing cannot establish simulation capacity')
    if any(keys != set(CLOCK_COUNTERS) for keys in present):
        raise ValueError('Partial clock counters; missing values are not zero')
    values = {name.rsplit('/', 1)[-1]: [row[name] for row in selected] for name in CLOCK_COUNTERS}
    if any(not math.isfinite(v) or v < 0 for series in values.values() for v in series):
        raise ValueError('Invalid clock counter')
    if any(v != int(v) for v in values['FixedTicks']) or any(v not in (0, 1) for v in values['Failed']):
        raise ValueError('Invalid fixed-tick count or failure flag')
    for name in ('RequestedSeconds', 'CommittedSeconds', 'WaterCommittedSeconds'):
        if any(b < a for a, b in zip(values[name], values[name][1:])):
            raise ValueError('Committed/requested clock went backwards')
    # Each CSV column is independently rounded. Preserve residuals rather than
    # claiming exact double-precision native equivalence from printed counters.
    residual = [r - c - b for r, c, b in zip(values['RequestedSeconds'],
                values['CommittedSeconds'], values['BacklogSeconds'])]
    native_offsets = [w - n for w, n in zip(values['WaterCommittedSeconds'], values['NativeFieldSeconds'])]
    adapter_errors = [w - c for w, c in zip(values['WaterCommittedSeconds'], values['CommittedSeconds'])]
    counts = Counter(int(v) for v in values['FixedTicks'])
    return dict(available=True, sample_indices_inclusive=[first, last],
        requested_seconds_first=values['RequestedSeconds'][0], requested_seconds_last=values['RequestedSeconds'][-1],
        committed_seconds_first=values['CommittedSeconds'][0], committed_seconds_last=values['CommittedSeconds'][-1],
        backlog_seconds_first=values['BacklogSeconds'][0], backlog_seconds_last=values['BacklogSeconds'][-1],
        backlog_seconds_max=max(values['BacklogSeconds']),
        backlog_seconds_growth=values['BacklogSeconds'][-1] - values['BacklogSeconds'][0],
        fixed_ticks_total=sum(count * number for number, count in counts.items()),
        fixed_ticks_histogram=dict(sorted(counts.items())), failed_frames=sum(values['Failed']),
        maximum_printed_queue_residual_seconds=max(abs(v) for v in residual),
        maximum_adapter_commit_difference_seconds=max(abs(v) for v in adapter_errors),
        native_origin_offset_seconds_first=native_offsets[0],
        native_origin_offset_seconds_last=native_offsets[-1],
        native_origin_offset_range_seconds=max(native_offsets) - min(native_offsets),
        simulation_capacity_accepted=False,
        scope='Counter evidence only, not a new lag tolerance or acceptance. A zero detail-water backlog '
              'does not clear bridge debt. Do not discard elapsed time or increase the fixed step to hide lag.')


def summarize_water_workload(samples, first, last, scope_offset, target_fps=20.0):
    """Associate elapsed intervals with explicitly phase-selected water scopes.

    Default UE5.8 FrameTime is emitted near BeginFrame, after the limiter wait,
    and describes the preceding logical frame: scope_offset=1. Legacy EndFrame
    timing uses offset=0. CSV metadata does not identify this mode, so callers
    MUST establish it independently. Never infer phase from best correlation.
    These groups diagnose workload association, not causal cost or acceptance.
    """
    if type(scope_offset) is not int or scope_offset not in (0, 1):
        raise ValueError('Explicit verified FrameTime scope offset 0 or 1 required')
    overall = summarize([{k: v for k, v in row.items() if k in METRICS}
                         for row in samples], first, last, target_fps)
    if first < scope_offset:
        raise ValueError('Preceding scope row is absent; do not trim the requested interval')
    required = (WATER_SCOPES[1], WATER_SCOPES[6])  # Refresh, crest Selection.
    scope_names = WATER_SCOPES + PUBLISH_SCOPES + SMOOTHING_SCOPES + BREAKING_SCOPES + FOAM_SCOPES + GROUND_SCOPES + RELIEF_SCOPES
    available = [name for name in scope_names if name in samples[first-scope_offset]]
    rows = range(first-scope_offset, last-scope_offset+1)
    for row in rows:
        if any(name not in samples[row] for name in required):
            raise ValueError('Refresh and crest-selection timing columns are required')
        if any((name in samples[row]) != (name in available) for name in scope_names):
            raise ValueError('Water scope availability changes inside the selected interval')
        if any(not math.isfinite(samples[row][name]) or samples[row][name] < 0 for name in available):
            raise ValueError('Invalid associated water scope time')
    groups = []
    for refresh in (False, True):
        for selection in (False, True):
            indices = [i for i in range(first, last+1)
                       if (samples[i-scope_offset][required[0]] > 0) == refresh
                       and (samples[i-scope_offset][required[1]] > 0) == selection]
            durations = [samples[i]['FrameTime'] for i in indices]
            groups.append(dict(refresh_positive_timing=refresh,
                crest_selection_positive_timing=selection, count=len(indices),
                frame_time_sample_indices=indices,
                water_scope_sample_indices=[i-scope_offset for i in indices],
                mean_frame_ms=statistics.mean(durations) if durations else None,
                p95_frame_ms_nearest_rank=sorted(durations)[math.ceil(.95*len(durations))-1] if durations else None,
                frames_over_budget=sum(t > overall['frame_budget_ms'] for t in durations),
                scope_mean_ms={name: statistics.mean(samples[i-scope_offset][name] for i in indices)
                               if indices else None for name in available}))
    return dict(scope_offset=scope_offset,
        alignment_source='Explicit caller argument; external mode confirmation required, not verified from CSV',
        sample_indices_inclusive=[first, last], frame_budget_ms=overall['frame_budget_ms'],
        frame_p95_within_target_budget=overall['frame_p95_within_target_budget'],
        scope='Workload association only; no causal attribution. Zero timing does not prove no call. '
              'Nested scopes must not be added. All requested elapsed samples are retained exactly once; '
              'grouping does not change the overall performance gate. CSV alone does not establish timing mode.',
        groups=groups)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("captures", nargs="+", type=Path)
    parser.add_argument("--first-sample", type=int, default=30)
    parser.add_argument("--last-sample", type=int, default=90)
    parser.add_argument("--target-fps", type=float, default=20.0,
                        help="Acceptance target, independent of recorded engine metadata (default: 20)")
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--require-water-scopes", action="store_true")
    parser.add_argument("--ignore-duplicate-unmeasured-header", action="append", default=[],
                        help="Explicit engine counter exception; never permits duplicate measured timings. Recorded with original column indices.")
    parser.add_argument("--frame-time-scope-offset", type=int, choices=(0, 1),
                        help="Optional workload grouping: caller-verified FrameTime mode, 1 for UE5.8 default, 0 for legacy EndFrame")
    args = parser.parse_args()
    if args.report.exists():
        raise FileExistsError(args.report)
    runs = []
    for path in args.captures:
        with path.open(newline="", encoding="utf-8-sig") as stream:
            samples, metadata = parse_capture(stream, args.require_water_scopes, args.ignore_duplicate_unmeasured_header)
        runs.append({"csv": str(path.resolve()), "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                     "total_samples": len(samples), "metadata": metadata,
                     "sample_indices_inclusive": [args.first_sample, args.last_sample],
                     "metrics": summarize(samples, args.first_sample, args.last_sample, args.target_fps)})
        runs[-1]['water_clock'] = summarize_water_clock(samples, args.first_sample, args.last_sample)
        if args.frame_time_scope_offset is not None:
            runs[-1]['water_workload'] = summarize_water_workload(samples, args.first_sample,
                args.last_sample, args.frame_time_scope_offset, args.target_fps)
    report = {"schema": "raftsim.unreal_frame_csv_audit.v2", "release_accepted": False,
              "scope": "Actual Unreal frame/CPU-thread/GPU CSV metrics, not water-actor time. "
              "Sample indices are zero-based CSV rows, not engine frame IDs. Threads overlap; "
              "UE5.8 default FrameTime is emitted near frame start and describes the preceding logical frame; "
              "legacy EndFrame timing has a different phase. CSV metadata does not establish this mode. "
              "Same-row elapsed time and water scopes must not be assumed phase-aligned. "
              "Water scopes are inclusive and nested (Tick contains Refresh/CartesianPublish; "
              "Refresh contains source samples/handover/optical filter/hydraulic relief/breaking vertices/foam transport "
              "and can also contain CartesianPublish when creating, recentering or hard-publishing the carrier; "
              "on the combined source path SourceSamples includes sampling and handover, while SourceHandover measures only its completed guard; "
              "CartesianPublish contains packing/SetMesh; "
              "SetMesh contains topology/crest input/source gather/output storage/bounds and notification/crest update, "
              "which contains selection and normals). "
              "RenderPacket is separate deferred render-data preparation, not a child of SetMesh. "
              "Do not sum nested or thread times. Present zero scope "
              "rows record zero time (not proof of no call); absent columns are unavailable. "
              "Append-only timing columns require a matching final header and "
              "unchanged initial metric positions. "
              "Short warmed intervals, variable trajectories and shared "
              "machine load are not packaged, sustained, visual or traversal acceptance.", "runs": runs}
    with args.report.open("x", encoding="utf-8") as output:
        json.dump(report, output, indent=2)
        output.write("\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
