"""Audit native game flip receipts; this does not simulate boat motion."""
import argparse
import json
import math
from pathlib import Path


def evaluate(path):
    report = json.loads(path.read_text(encoding="utf-8-sig"))
    rows = report["motion"]
    if report["failed"] or report["simulated_seconds"] < 11.99 or len(rows) < 100:
        raise ValueError(f"Incomplete live run: {path}")
    numeric = ("seconds", "x_m", "y_m", "z_m", "roll_deg", "pitch_deg", "up_z", "omega_rad_s",
               "surface_offset_m", "quat_x", "quat_y", "quat_z", "quat_w")
    if any(key not in row for row in rows for key in numeric):
        raise ValueError(f"Receipt lacks surface-relative depth or quaternion evidence: {path}")
    if any(not math.isfinite(row[key]) for row in rows for key in numeric):
        raise ValueError(f"Non-finite state: {path}")
    gaps = [b["seconds"] - a["seconds"] for a, b in zip(rows, rows[1:])]
    if rows[0]["seconds"] > .11 or report["simulated_seconds"] - rows[-1]["seconds"] > .11:
        raise ValueError(f"Missing opening/terminal motion receipt: {path}")
    if any(g <= 0 or g > .11 for g in gaps):
        raise ValueError(f"Fixed-step receipt gap: {path}")
    first_mode = next((row for row in rows if row["mode"] == 1), None)
    inverted = [row for row in rows if row["up_z"] < 0]
    norms = [sum(row[f"quat_{axis}"] ** 2 for axis in "xyzw") for row in rows]
    if max(abs(norm - 1.) for norm in norms) > 1e-6:
        raise ValueError(f"Non-unit orientation: {path}")
    minimum_offset = report["minimum_surface_offset_m"]
    if not math.isfinite(minimum_offset) or minimum_offset < -2.:
        raise ValueError(f"Raft fell more than 2 m below the local surface: {path}")
    # A motion receipt can be finite while the boat has sunk permanently.
    # This lab guard is not an empirical safety limit: an inflated free raft
    # must return toward flotation after its finite-depth forcing subsides.
    if rows[-1]["surface_offset_m"] < -1.:
        raise ValueError(f"Run ended with a submerged/stalled raft: {path}")
    return {
        "source": str(path), "scene": report["scene"], "motion_rows": len(rows),
        "maximum_receipt_gap_s": max(gaps),
        "maximum_tilt_degrees": math.degrees(math.acos(max(-1., min(1., report["minimum_up_z"])))),
        "first_capsize_seconds": report["first_capsize_seconds"],
        "tilt_at_first_capsize_degrees": None if first_mode is None else math.degrees(math.acos(max(-1., min(1., first_mode["up_z"])))),
        "capsize_mode_before_actual_inversion": first_mode is not None and first_mode["up_z"] > 0,
        "first_inverted_receipt_s": None if not inverted else inverted[0]["seconds"],
        "last_up_z": rows[-1]["up_z"], "last_omega_rad_s": rows[-1]["omega_rad_s"],
        "maximum_omega_rad_s": report["maximum_omega_rad_s"],
        "final_swimmer_count": rows[-1]["swimmers"],
        "minimum_surface_offset_m": minimum_offset,
        "final_surface_offset_m": rows[-1]["surface_offset_m"],
        "maximum_pose_step_rad": report["maximum_pose_step_rad"],
        "maximum_omega_step_rad_s": report["maximum_omega_step_rad_s"],
        "rendered_fps_mean": report["rendered_fps_mean"],
        "initial_roll_degrees": report.get("initial_roll_degrees", 0.),
        "initial_roll_rate_rad_s": report.get("initial_roll_rate_rad_s", 0.),
        "geometry_path": report.get("geometry_path", "legacy lab full-hull export"),
        "minimum_swimmer_surface_offset_m": report.get("minimum_swimmer_surface_offset_m"),
        "maximum_submerged_crew": report.get("maximum_submerged_crew"),
        "final_crew_motion": rows[-1].get("crew_motion", []),
        "scope": "Actual integrated engine states; authored laboratory field, not a measured real-raft threshold or safety certification.",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("receipts", nargs="+", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--require-physical-capsize", action="store_true")
    parser.add_argument("--minimum-fps", type=float, default=20.)
    parser.add_argument("--require-submerged-crew", action="store_true")
    args = parser.parse_args()
    results = [evaluate(path) for path in args.receipts]
    if args.require_physical_capsize:
        if not math.isfinite(args.minimum_fps) or args.minimum_fps < 0:
            raise ValueError("Invalid FPS acceptance floor")
        if any(not math.isfinite(r["rendered_fps_mean"]) or r["rendered_fps_mean"] < args.minimum_fps for r in results):
            raise ValueError(f"Native recording misses the {args.minimum_fps:g} FPS acceptance floor")
        if any(r["capsize_mode_before_actual_inversion"] for r in results):
            raise ValueError("Capsize lifecycle declared before actual inversion")
        for result in results:
            if result["scene"] in ("calm", "small_broadside", "eddy_line", "rolling_entry_control") and result["first_capsize_seconds"] >= 0:
                raise ValueError(f"Ordinary control unexpectedly capsized: {result['scene']}")
        if not any(r["first_capsize_seconds"] >= 0 and r["final_swimmer_count"] > 0 and r["last_up_z"] < 0 for r in results):
            raise ValueError("No demonstrated physical capsize with real crew ejection")
    if args.require_submerged_crew:
        flips = [r for r in results if r["first_capsize_seconds"] >= 0]
        if not flips or any(not r["maximum_submerged_crew"] or r["minimum_swimmer_surface_offset_m"] is None or r["minimum_swimmer_surface_offset_m"] > -.2 for r in flips):
            raise ValueError("No measured submerged passenger release")
        for result in flips:
            crew = result["final_crew_motion"]
            if len(crew) != result["final_swimmer_count"] or any(not math.isfinite(c["surface_offset_m"]) or abs(c["surface_offset_m"]) > .03 for c in crew):
                raise ValueError(f"Crew did not resurface at the local datum: {result['scene']}")
    if args.output.exists():
        raise ValueError("Preserve previous audit; choose a fresh output")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps({"scenes": results}, indent=2), encoding="utf-8")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
