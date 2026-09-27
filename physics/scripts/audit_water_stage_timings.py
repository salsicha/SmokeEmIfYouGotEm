"""Summarize opt-in actual-game WaterPerf logs; never a release acceptance gate."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import statistics
from pathlib import Path

ROW = re.compile(r"WaterPerf scope=(\w+) frame=(\d+) (.*)")
VALUE = re.compile(r"(\w+_ms)=([^\s]+)")


def summarize(path: Path, first: int, last: int) -> dict:
    if first < 0 or last < first:
        raise ValueError('invalid frame interval')
    raw = path.read_bytes()
    scopes: dict[str, dict[str, list[float]]] = {}
    frames: dict[str, set[int]] = {}
    keys_by_scope: dict[str, set[str]] = {}
    for line in raw.decode("utf-8", errors="replace").splitlines():
        row = ROW.search(line)
        if not row or not first <= int(row[2]) <= last:
            continue
        scope, frame = row[1], int(row[2])
        if frame in frames.setdefault(scope, set()):
            raise ValueError(f"duplicate {scope} frame {frame}: select a post-startup interval")
        frames[scope].add(frame)
        values = VALUE.findall(row[3])
        keys = {key for key, _ in values}
        if len(keys) != len(values) or 'total_ms' not in keys:
            raise ValueError(f'duplicate metric or missing total in {scope} frame {frame}')
        if keys != keys_by_scope.setdefault(scope, keys):
            raise ValueError(f'changed metrics in {scope} frame {frame}')
        for key, value in values:
            value = float(value)
            if not math.isfinite(value) or value < 0:
                raise ValueError(f'nonfinite or negative {key} in {scope} frame {frame}')
            scopes.setdefault(scope, {}).setdefault(key, []).append(value)
    if not scopes.get("tick") or not scopes.get("refresh"):
        raise ValueError(f"no tick/refresh data in selected interval: {path}")
    if frames['tick'] != set(range(first, last+1)):
        raise ValueError('incomplete tick frame coverage')
    result = {}
    for scope, values in scopes.items():
        result[scope] = {}
        for key, samples in values.items():
            samples.sort()
            result[scope][key] = {
                "count": len(samples),
                "median": statistics.median(samples),
                "mean": statistics.mean(samples),
                "p95_nearest_rank": samples[math.ceil(.95 * len(samples)) - 1],
                "maximum": samples[-1],
            }
    return {"log": str(path.resolve()), "sha256": hashlib.sha256(raw).hexdigest(),
            "frame_range_inclusive": [first, last],
            "scope_frames": {scope: sorted(ids) for scope, ids in frames.items()},
            "complete_tick_coverage": True, "stages": result}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("logs", type=Path, nargs="+")
    parser.add_argument("--first-frame", type=int, default=30)
    parser.add_argument("--last-frame", type=int, default=130)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    if args.first_frame < 0 or args.last_frame < args.first_frame:
        parser.error("invalid frame interval")
    report = {
        "schema": "raftsim.water_stage_timings.v1",
        "scope": "Actual-game instrumented CPU stages only, not total frame time, GPU cost, visual fidelity or release acceptance. Runs may follow different time-step trajectories and share machine load. Nested stages must not be summed across scopes.",
        "runs": [summarize(path, args.first_frame, args.last_frame) for path in args.logs],
    }
    with args.report.open("x", encoding="utf-8") as target:
        json.dump(report, target, indent=2)
        target.write("\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
