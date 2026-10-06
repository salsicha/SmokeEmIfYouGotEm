"""Audit native camera-route CSVs, not startup samples or boat trajectories.

The runtime emits route coordinates into the same per-frame engine CSV as the
actual elapsed FrameTime. No percentile trimming or interpolated frame times.
Camera coverage is separate from active hydraulic/boat coverage.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path


MAPS = (
    "L_SouthForkAmerican_FullReach", "L_SouthFork_Troublemaker", "L_Hance",
    "L_LavaCanyon", "L_Terminator", "L_UpperHuacas", "L_Zambezi",
    "L_ZambeziUpperGorge",
)
REQUIRED = (
    "FrameTime", "GameThreadTime", "GPUTime", "RaftSimRoute/Active",
    "RaftSimRoute/StationM", "RaftSimRoute/StartM", "RaftSimRoute/EndM",
    "RaftSimRoute/WetBaseline", "RaftSimRoute/LiveWaterAtCamera",
    "RaftSimRoute/BoatDistanceM", "RaftSimRoute/Sequence",
)


def read_frames(path: Path) -> list[dict[str, float]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.reader(stream))
    # UE appends the authoritative header after late-registered stat columns.
    footers = [i for i, row in enumerate(rows) if row and row[0] == "EVENTS" and i > 0]
    if len(footers) != 1:
        raise ValueError("Exactly one native CSV footer header required")
    footer = footers[0]
    header = rows[footer]
    for name in REQUIRED:
        if header.count(name) != 1:
            raise ValueError(f"Exactly one {name} column required")
    indexes = {name: header.index(name) for name in REQUIRED}
    result = []
    for row in rows[1:footer]:
        if not row:
            raise ValueError("Empty native timing row")
        frame = {}
        for name, index in indexes.items():
            if index >= len(row) or not row[index].strip():
                raise ValueError(f"Missing native {name} sample")
            value = float(row[index])
            if not math.isfinite(value):
                raise ValueError(f"Nonfinite native {name} sample")
            frame[name] = value
        if frame["FrameTime"] <= 0:
            raise ValueError("Actual elapsed frame time must be positive")
        if frame["GameThreadTime"] < 0 or frame["GPUTime"] < 0:
            raise ValueError("Negative engine timing")
        for name in ("Active", "WetBaseline", "LiveWaterAtCamera"):
            if frame[f"RaftSimRoute/{name}"] not in (0, 1):
                raise ValueError(f"Native {name} must be binary")
        result.append(frame)
    if not result:
        raise ValueError("No native frame samples")
    return result


def audit(frames: list[dict[str, float]], receipt: dict) -> dict:
    if receipt.get("schema") != "raftsim.native_map_flythrough.v1":
        raise ValueError("Native route receipt required")
    if receipt.get("map") not in MAPS:
        raise ValueError("A requested production map is required")
    if receipt.get("mode") != "camera_only_no_boat_guidance":
        raise ValueError("Do not present forced boat motion as a native flight")
    if not receipt.get("complete") or receipt.get("failure"):
        raise ValueError("Native route did not finish cleanly")
    start, end = float(receipt["start_m"]), float(receipt["end_m"])
    if not math.isfinite(start) or not math.isfinite(end) or end <= start:
        raise ValueError("Finite positive whole authored route required")
    if receipt.get("whole_authored_axis") is not True:
        raise ValueError("Partial route cannot be promoted to whole map")
    selected = [i for i, f in enumerate(frames) if f["RaftSimRoute/Active"] == 1]
    if len(selected) < 3 or selected != list(range(selected[0], selected[-1] + 1)):
        raise ValueError("Contiguous native route frame coverage required")
    active = [frames[i] for i in selected]
    if receipt.get("native_route_ticks") != len(active):
        raise ValueError("CSV did not retain every native camera-route tick")
    if [f["RaftSimRoute/Sequence"] for f in active] != list(range(1, len(active) + 1)):
        raise ValueError("Native route frame sequence is incomplete or duplicated")
    stations = [f["RaftSimRoute/StationM"] for f in active]
    if abs(stations[0] - start) > .05 or abs(stations[-1] - end) > .05:
        raise ValueError("Native flight must render both authored endpoints")
    for f in active:
        if not start - .001 <= f["RaftSimRoute/StationM"] <= end + .001:
            raise ValueError("Native camera left the authored route bounds")
        if abs(f["RaftSimRoute/StartM"] - start) > .05 or abs(f["RaftSimRoute/EndM"] - end) > .05:
            raise ValueError("Native per-frame route bounds disagree with receipt")
        if f["RaftSimRoute/BoatDistanceM"] < 0:
            raise ValueError("Invalid actual boat distance")
    gaps = [b - a for a, b in zip(stations, stations[1:])]
    if min(gaps) < -.001 or max(gaps) > 5.001:
        raise ValueError("Flight backtracks or skips more than five route meters per frame")
    times = [f["FrameTime"] for f in active]
    slow = [i for i, t in enumerate(times) if t > 50.0]
    bins = {}
    for station, f in zip(stations, active):
        key = min(int((station - start) // 100), int(math.ceil((end - start) / 100)) - 1)
        group = bins.setdefault(key, [])
        group.append(f)
    segments = []
    for key, group in sorted(bins.items()):
        segment_times = [f["FrameTime"] for f in group]
        segments.append({
            "start_m": start + key * 100, "end_m": min(end, start + (key + 1) * 100),
            "frames": len(group), "worst_ms": max(segment_times),
            "minimum_fps": 1000 / max(segment_times),
            "frames_below_20fps": sum(t > 50 for t in segment_times),
            "game_thread_mean_ms": sum(f["GameThreadTime"] for f in group) / len(group),
            "gpu_mean_ms": sum(f["GPUTime"] for f in group) / len(group),
        })
    expected_bins = int(math.ceil((end - start) / 100))
    if len(segments) != expected_bins:
        raise ValueError("Spatial segment coverage missing")
    wet = sum(f["RaftSimRoute/WetBaseline"] == 1 for f in active)
    live = sum(f["RaftSimRoute/LiveWaterAtCamera"] == 1 for f in active)
    return {
        "schema": "raftsim.native_map_flythrough_audit.v1", "map": receipt["map"],
        "camera_whole_route_complete": True, "start_m": start, "end_m": end,
        "audited_frames": len(active), "maximum_station_gap_m": max(gaps),
        "actual_elapsed_seconds": sum(times) / 1000, "worst_ms": max(times),
        "minimum_fps": 1000 / max(times), "frames_below_20fps": len(slow),
        "first_slow_station_m": stations[slow[0]] if slow else None,
        "passes_every_route_frame_20fps": not slow,
        "wet_baseline_frames": wet, "live_water_at_camera_frames": live,
        "maximum_camera_boat_distance_m": max(f["RaftSimRoute/BoatDistanceM"] for f in active),
        "all_map_water_and_boat_validation_accepted": False,
        "scope": "Actual camera render route; boat is freely simulated, not guided. Far-field render baseline is not live water/boat acceptance. No frame trimming, synthetic times, or recording in timing run.",
        "segments": segments,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("Preserve prior audit; use a fresh output")
    receipt = json.loads(args.receipt.read_text(encoding="utf-8-sig"))
    result = audit(read_frames(args.csv), receipt)
    result["csv"] = str(args.csv.resolve())
    result["csv_sha256"] = hashlib.sha256(args.csv.read_bytes()).hexdigest()
    result["native_receipt"] = str(args.receipt.resolve())
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in result.items() if key != "segments"}, indent=2))


if __name__ == "__main__":
    main()
