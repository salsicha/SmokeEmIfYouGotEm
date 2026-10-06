"""Diagnose actual complete route CSV costs, never a replacement FPS gate.

Run after the native timing collection is terminal. Nested stage timings must
not be summed; the camera's route station is not the freely simulated boat's
physical station. Missing optional observations are never invented as zero.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path

from audit_map_flythrough import MAPS, audit, read_frames


def rest_key_observation(header: list[str], rows: list[list[str]], required: bool = False) -> dict | None:
    """Actual native counters on ALL active rows, never inferred from source.

    Legacy binaries have neither counter. Half-present, ambiguous or malformed
    observations cannot prove a current optimized mode. No frame/FPS filtering.
    """
    names = ("RaftSimHull/RestKeySealedChecks", "RaftSimHull/RestKeyReferenceChecks")
    if not any(name in header for name in names):
        if required:
            raise ValueError("Actual sealed-rest counters required; legacy/missing data is not proof")
        return None
    if not rows or any(header.count(name) != 1 for name in names):
        raise ValueError("Complete unambiguous native rest-key columns required")
    columns = [header.index(name) for name in names]
    totals = [0, 0]
    sealed_frames = reference_frames = empty_frames = 0
    for row in rows:
        values = []
        for column in columns:
            if column >= len(row) or not row[column].strip():
                raise ValueError("Missing active-frame native rest-key observation")
            value = float(row[column])
            if not math.isfinite(value) or value < 0 or not value.is_integer():
                raise ValueError("Invalid active-frame native rest-key observation")
            values.append(int(value))
        totals = [a + b for a, b in zip(totals, values)]
        sealed_frames += values[0] > 0
        reference_frames += values[1] > 0
        empty_frames += sum(values) == 0
    if required and totals[0] == 0:
        raise ValueError("No actual sealed-rest checks on this map; source/default label is not proof")
    return {
        "active_frames_observed": len(rows),
        "sealed_checks_sum": totals[0], "reference_checks_sum": totals[1],
        "active_frames_with_sealed_checks": sealed_frames,
        "active_frames_with_reference_checks": reference_frames,
        "active_frames_without_key_checks": empty_frames,
        "every_active_frame_used_sealed_key": sealed_frames == len(rows),
        "mean_sealed_checks_per_active_frame": totals[0] / len(rows),
        "scope": "Complete actual native counter observations, not a geometry, physical-feature or FPS acceptance gate.",
    }


def analyze(index_path: Path, require_sealed_rest: bool = False) -> dict:
    index = json.loads(index_path.read_text(encoding="utf-8-sig"))
    if index.get("all_eight_routes_complete") is not True or index.get("all_eight_native_routes_complete") is not True:
        raise ValueError("Eight healthy same-build terminal routes required")
    runs = index["runs"]
    if len(runs) != 8 or {run["map"] for run in runs} != set(MAPS):
        raise ValueError("Every requested map exactly once required")
    results = []
    binary_hashes = None
    for run in runs:
        if not run.get("complete") or not run.get("native_route_complete") or not run.get("same_native_binaries_as_collection"):
            raise ValueError("Individual native route is not qualified")
        saved_path = Path(run["audit"])
        saved = json.loads(saved_path.read_text(encoding="utf-8-sig"))
        csv_path = Path(saved["csv"])
        digest = hashlib.sha256(csv_path.read_bytes()).hexdigest()
        if digest != saved["csv_sha256"]:
            raise ValueError("Retained native CSV changed")
        launch = json.loads((saved_path.parent / "launch.json").read_text(encoding="utf-8-sig"))
        if launch.get("schema") != "raftsim.map_flythrough_launch.v1" or launch.get("map") != run["map"]:
            raise ValueError("Requested actual native launch required")
        if any(launch.get(name) is not False for name in ("recording", "screenshots", "boat_guidance")):
            raise ValueError("Timing run must not record, capture screenshots or guide the boat")
        if binary_hashes is None:
            binary_hashes = launch["binary_sha256"]
        if launch["binary_sha256"] != binary_hashes or launch.get("exit_code") != 0:
            raise ValueError("Actual game binary/exit differs across routes")
        receipt = json.loads(Path(saved["native_receipt"]).read_text(encoding="utf-8-sig"))
        frames = read_frames(csv_path)
        verified = audit(frames, receipt)
        if verified["map"] != run["map"]:
            raise ValueError("Actual route map differs from requested map")
        for key in ("audited_frames", "frames_below_20fps", "worst_ms", "start_m", "end_m"):
            if verified[key] != saved[key]:
                raise ValueError(f"Retained route audit disagrees: {key}")
        selected = [i for i, frame in enumerate(frames) if frame["RaftSimRoute/Active"] == 1]
        active_frames = [frames[i] for i in selected]
        with csv_path.open(encoding="utf-8-sig", newline="") as stream:
            rows = list(csv.reader(stream))
        footers = [i for i, row in enumerate(rows) if i and row and row[0] == "EVENTS"]
        if len(footers) != 1:
            raise ValueError("One actual footer required")
        header = rows[footers[0]]
        active_rows = [rows[i + 1] for i in selected]
        native_rest_key = rest_key_observation(header, active_rows, require_sealed_rest)
        names = [name for name in header if name in ("FrameTime", "GameThreadTime", "GPUTime") or
                 (name.startswith("RaftSim") and "/GameThread/" in name)]
        means, incomplete, worst_values = {}, {}, {}
        worst_index = max(range(len(active_frames)), key=lambda i: active_frames[i]["FrameTime"])
        for name in names:
            if header.count(name) != 1:
                raise ValueError(f"Ambiguous stage column: {name}")
            column = header.index(name)
            samples = []
            for row in active_rows:
                if column < len(row) and row[column].strip():
                    value = float(row[column])
                    if math.isfinite(value) and value >= 0:
                        samples.append(value)
            if len(samples) == len(active_rows):
                means[name] = sum(samples) / len(samples)
            else:
                incomplete[name] = {"qualified_samples": len(samples), "required_samples": len(active_rows)}
            row = active_rows[worst_index]
            if column < len(row) and row[column].strip():
                value = float(row[column])
                if math.isfinite(value) and value >= 0:
                    worst_values[name] = value
        slow_segments = [segment for segment in verified["segments"] if segment["frames_below_20fps"] > 0]
        results.append({
            "map": run["map"], "native_audit": str(saved_path), "csv_sha256": digest,
            "whole_axis_m": [verified["start_m"], verified["end_m"]],
            "active_frames": len(active_rows), "frames_below_20fps": verified["frames_below_20fps"],
            "passes_every_route_frame_20fps": verified["passes_every_route_frame_20fps"],
            "minimum_fps": verified["minimum_fps"],
            "native_rest_key_observation": native_rest_key,
            "whole_route_mean_stage_ms": dict(sorted(means.items(), key=lambda item: -item[1])),
            "unqualified_optional_mean_stages": incomplete,
            "actual_worst_frame": {
                "native_sequence": active_frames[worst_index]["RaftSimRoute/Sequence"],
                "camera_station_m": active_frames[worst_index]["RaftSimRoute/StationM"],
                "camera_boat_distance_m": active_frames[worst_index]["RaftSimRoute/BoatDistanceM"],
                "available_native_stage_ms": dict(sorted(worst_values.items(), key=lambda item: -item[1])),
            },
            "slow_segment_count": len(slow_segments),
            "worst_slow_segments": sorted(slow_segments, key=lambda segment: -segment["worst_ms"])[:5],
        })
    return {
        "schema": "raftsim.all_map_native_route_cost_diagnosis.v1", "source_collection": str(index_path),
        "binary_sha256": binary_hashes, "maps": results,
        "all_eight_every_frame_20fps": all(result["passes_every_route_frame_20fps"] for result in results),
        "all_map_physical_feature_acceptance": False,
        "sealed_rest_counters_required": require_sealed_rest,
        "scope": "Strict coverage, same-build receipts and CSV SHA revalidated. Complete native mean stages and actual worst frames, not summed nested costs, percentiles, synthetic times or boat-route activation proof. Missing optional data is explicitly unqualified.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--index", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--require-sealed-rest", action="store_true",
                        help="Require actual native optimized-key observations in every requested map")
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("Preserve prior diagnosis; fresh output required")
    result = analyze(args.index, args.require_sealed_rest)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(args.output), "maps": [
        {"map": item["map"], "frames": item["active_frames"], "slow_frames": item["frames_below_20fps"],
         "minimum_fps": item["minimum_fps"], "worst_frame": item["actual_worst_frame"]}
        for item in result["maps"]]}, indent=2))


if __name__ == "__main__":
    main()
