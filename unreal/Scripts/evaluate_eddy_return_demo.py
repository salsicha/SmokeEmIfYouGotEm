"""Audit native boat motion, not an authored trajectory or tracer substitute."""
import argparse
import json
import math
from pathlib import Path


def audit(path):
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    rows = data["motion"]
    assert data["feature"] == "eddy" and not data["collision_control"]
    assert not data["failed"] and data["simulated_seconds"] >= 17.99
    assert data["blocked_tracer_steps"] == 0
    assert len(rows) >= 160 and rows[0]["seconds"] < .12
    fields = ("seconds", "x_m", "y_m", "z_m", "boat_u_mps", "boat_v_mps",
              "water_u_mps", "water_v_mps", "yaw_deg", "roll_deg", "pitch_deg")
    assert all(math.isfinite(r[k]) for r in rows for k in fields)
    assert all(0 < b["seconds"] - a["seconds"] <= .12 for a, b in zip(rows, rows[1:]))
    start = rows[0]
    assert start["x_m"] > 2 and abs(start["y_m"]) < 4
    assert start["water_u_mps"] < 0 and start["boat_u_mps"] < 0
    head_index = min(range(len(rows)), key=lambda i: rows[i]["x_m"])
    head = rows[head_index]
    assert start["x_m"] - head["x_m"] > 5
    assert min(r["boat_u_mps"] for r in rows[:head_index+1]) < -.5
    outer = next(r for r in rows[head_index:]
                 if abs(r["y_m"]) > 2.5 and r["x_m"] < 15
                 and r["boat_u_mps"] > 1 and r["water_u_mps"] > 1)
    exit_row = next(r for r in rows[head_index:]
                    if r["x_m"] > 26 and r["boat_u_mps"] > 1.5)
    assert min(r["z_m"] for r in rows) > -.5
    assert max(max(abs(r["roll_deg"]), abs(r["pitch_deg"])) for r in rows) < 30
    return {"source": str(path.resolve()), "passed": True,
            "mirrored_entry": data.get("mirrored_entry", False),
            "simulation_seconds": data["simulated_seconds"],
            "motion_samples": len(rows), "start_x_m": start["x_m"],
            "closest_x_m": head["x_m"], "head_seconds": head["seconds"],
            "upstream_distance_m": start["x_m"] - head["x_m"],
            "outer_branch_seconds": outer["seconds"],
            "outer_branch_y_m": outer["y_m"],
            "outer_branch_boat_u_mps": outer["boat_u_mps"],
            "downstream_exit_seconds": exit_row["seconds"],
            "maximum_upstream_speed_mps": -min(r["boat_u_mps"] for r in rows),
            "blocked_tracer_steps": data["blocked_tracer_steps"],
            "scope": "Actual empty production hull, zero paddle, shared authored current. "
                     "One initial pose; no scripted trajectory. Does not establish full-map "
                     "hydraulic accuracy, exact-centreline escape, loaded-crew behavior or FPS."}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("motion", type=Path, nargs="+")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = {"schema": "raftsim.native_eddy_return_audit.v1",
              "runs": [audit(path) for path in args.motion]}
    if args.output.exists():
        raise RuntimeError("Preserve prior receipt; use a fresh output")
    args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
