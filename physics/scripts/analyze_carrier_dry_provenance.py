"""Localize submitted-water/raw-dry discrepancies without altering wet gates.

This compares an observer's same-call coarse lattice to its point sample. It
does not infer the native solver's cell data from that presentation lattice.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path


def analyze(probe: dict, world_y_sign: float = -1.0) -> dict:
    if world_y_sign not in (-1.0, 1.0):
        raise ValueError("world_y_sign must be -1 or 1")
    if not (probe["raw_available"] and not probe["raw_wet"]
            and probe["ground_hit"] and probe["water_z_cm"] > probe["ground_z_cm"]):
        raise ValueError("expected available, raw-dry, non-ground-occluded probe")
    triangle = probe["triangle_vertices"]
    if len(triangle) != 3:
        raise ValueError("three submitted triangle vertices required")
    query_error = math.hypot(*(math.fsum(w*v[k] for w, v in zip((.2, .3, .5), triangle))
                              - probe[k] for k in ("x_cm", "y_cm")))
    if not math.isfinite(query_error) or query_error > 1.e-6:
        raise ValueError("triangle does not reconstruct the observer query")
    cells = probe["source_cell"]
    if len(cells) != 4 or not all(c["current_available"] for c in cells):
        raise ValueError("four available source samples required")
    x, y = probe["x_cm"] * .01, probe["y_cm"] * .01 * world_y_sign
    x0, y0 = cells[0]["field_x_m"], cells[0]["field_y_m"]
    x1, y1 = cells[3]["field_x_m"], cells[3]["field_y_m"]
    if x1 <= x0 or y1 <= y0:
        raise ValueError("source cell must have positive extent")
    if [(c["field_x_m"], c["field_y_m"]) for c in cells] != [
            (x0, y0), (x1, y0), (x0, y1), (x1, y1)]:
        raise ValueError("source cell must be ordered 00, 10, 01, 11")
    fx, fy = (x - x0) / (x1 - x0), (y - y0) / (y1 - y0)
    if not (0 <= fx <= 1 and 0 <= fy <= 1):
        raise ValueError("probe outside source cell")
    weights = [(1-fx)*(1-fy), fx*(1-fy), (1-fx)*fy, fx*fy]
    fields = ("cached_bed_m", "cached_depth_m", "current_bed_m", "current_depth_m")
    if not all(math.isfinite(c[k]) for c in cells for k in fields):
        raise ValueError("nonfinite cell data")
    if any(c[k] < 0 for c in cells for k in ("cached_depth_m", "current_depth_m")):
        raise ValueError("negative source depth")
    averages = {k: math.fsum(w*c[k] for w, c in zip(weights, cells)) for k in fields}
    wet_weight = math.fsum(w for w, c in zip(weights, cells) if c['current_depth_m'] > 0)
    wet_stage = (math.fsum(w*(c['current_bed_m']+c['current_depth_m'])
                          for w, c in zip(weights, cells) if c['current_depth_m'] > 0)
                 / wet_weight if wet_weight else None)
    return {
        "x_cm": probe["x_cm"], "y_cm": probe["y_cm"],
        "source_cell_size_m": [x1-x0, y1-y0], "source_fraction": [fx, fy],
        "raw_depth_m": probe["raw_depth_m"],
        "triangle_query_error_cm": query_error,
        "raw_bed_m": probe["raw_bed_m"],
        "triangle_above_ground_cm": probe["water_z_cm"]-probe["ground_z_cm"],
        "triangle_above_raw_bed_cm": probe["water_z_cm"]-100*probe["raw_bed_m"],
        "bilinear_coarse_lattice": averages,
        "coarse_positive_donor_stage_m": wet_stage,
        "coarse_positive_donor_stage_minus_bed_m": None if wet_stage is None else wet_stage-averages['current_bed_m'],
        "raw_bed_minus_coarse_current_bed_m": probe["raw_bed_m"]-averages["current_bed_m"],
        "maximum_corner_depth_change_m": max(abs(c["current_depth_m"]-c["cached_depth_m"]) for c in cells),
        "maximum_corner_bed_change_m": max(abs(c["current_bed_m"]-c["cached_bed_m"]) for c in cells),
        "clipping_wet": [c["clipping_wet"] for c in cells],
        "current_wet": [c["current_wet"] for c in cells],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("contact", type=Path)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--world-y-sign", type=float, choices=(-1., 1.), default=-1.)
    args = parser.parse_args()
    raw = args.contact.read_bytes()
    contact = json.loads(raw.decode("utf-8-sig"))
    probes = [p for p in contact["ground_contact_probes"] if p["raw_available"]
              and not p["raw_wet"] and p["ground_hit"] and p["water_z_cm"] > p["ground_z_cm"]]
    report = {
        "scope": "Same-call coarse-lattice versus raw point evidence; bilinear depth is NOT the mixed wet/dry sampler. No visual, physical or timing acceptance.",
        "input_sha256": hashlib.sha256(raw).hexdigest(),
        "world_seconds": contact["world_seconds"],
        "non_occluded_raw_dry_probes": [analyze(p, args.world_y_sign) for p in probes],
    }
    if args.report.exists():
        raise FileExistsError(args.report)
    args.report.write_text(json.dumps(report, indent=2, allow_nan=False)+"\n", encoding="utf-8")
    print(json.dumps(report, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
