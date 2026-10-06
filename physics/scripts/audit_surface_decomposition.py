"""Read actual engine target-height components; never photographic acceptance.

Flow-aligned profiles use only four-wet-corner interpolation, without filling
dry or missing data. Component curvature is measured against each valid
profile's endpoint line, not interpreted as a calibrated hydraulic wave.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import numpy as np


COMPONENTS = ("raw_eta_m", "filtered_eta_m", "presented_base_eta_m", "hydraulic_relief_m",
              "shared_crest_m", "other_relief_m", "target_z_m")


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv", type=Path)
    parser.add_argument("crests", type=Path)
    parser.add_argument("--render-lift-m", type=float, required=True,
                        help="Actual value recorded by the same engine decomposition log, not an assumed legacy lift")
    parser.add_argument("--require-native-stage", action="store_true")
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    assert not args.report.exists(), "Preserve previous evidence"
    with args.csv.open(encoding="utf-8-sig", newline="") as stream:
        rows = [{key: float(value) for key, value in row.items()} for row in csv.DictReader(stream)]
    assert rows and all(np.isfinite(list(row.values())).all() for row in rows)
    for row in rows:
        row.setdefault("presented_base_eta_m", row["filtered_eta_m"])
    native_stage_error = max(abs(r["presented_base_eta_m"]-r["raw_eta_m"]) for r in rows)
    if args.require_native_stage:
        assert native_stage_error == 0, "Native stage was changed in the base geometry"
    points = {(row["field_x_m"], row["field_y_m"]): row for row in rows}
    assert len(points) == len(rows), "Duplicate source coordinate"
    xs = sorted({p[0] for p in points})
    ys = sorted({p[1] for p in points})
    assert np.allclose(np.diff(xs), 1, atol=1.e-8) and np.allclose(np.diff(ys), 1, atol=1.e-8)
    # Use the actual logged configuration: the normal single carrier can
    # have zero lift even though legacy two-surface paths used 2 cm.
    assert np.isfinite(args.render_lift_m)
    residual = [r["target_z_m"]-r["presented_base_eta_m"]-r["hydraulic_relief_m"]-
                r["shared_crest_m"]-r["other_relief_m"] for r in rows]
    assert np.max(np.abs(np.asarray(residual)-args.render_lift_m)) < 2.e-6

    def sample(p):
        gx, gy = np.floor(p-[xs[0], ys[0]])
        x, y = gx+xs[0], gy+ys[0]
        corners = [points.get((x+dx, y+dy)) for dy in (0, 1) for dx in (0, 1)]
        if any(c is None for c in corners):
            return None
        fx, fy = p-[x, y]
        weights = [(1-fx)*(1-fy), fx*(1-fy), (1-fx)*fy, fx*fy]
        return {key: sum(w*c[key] for w, c in zip(weights, corners)) for key in COMPONENTS}

    sites = json.loads(args.crests.read_text(encoding="utf-8-sig"))["sites"]
    profiles = []
    for site in sites:
        center = np.asarray([site["station_m"], site["lateral_m"]])
        if not (-5460 <= center[0] <= -5400 and 3575 <= center[1] <= 3640):
            continue
        direction = np.asarray([site["flow_direction_x"], site["flow_direction_y"]], dtype=float)
        direction /= np.linalg.norm(direction)
        sampled = []
        for distance in np.arange(-12, 12.001, .5):
            p = center+direction*distance
            values = sample(p)
            if values is not None:
                sampled.append(dict(distance_m=float(distance), field_xy_m=p.tolist(), **values))
        if len(sampled) < 3:
            continue
        distances = np.asarray([r["distance_m"] for r in sampled])
        stats = {}
        for key in COMPONENTS:
            values = np.asarray([r[key] for r in sampled])
            trend = values[0]+(values[-1]-values[0])*(distances-distances[0])/(distances[-1]-distances[0])
            curvature = values-trend
            stats[key] = dict(minimum_m=float(values.min()), maximum_m=float(values.max()),
                              endpoint_detrended_peak_m=float(curvature.max()),
                              endpoint_detrended_trough_m=float(curvature.min()))
        profiles.append(dict(site=site, components=stats, samples=sampled,
                             missing_samples=49-len(sampled)))
    result = dict(schema="raftsim.surface_decomposition.v1", source_csv_sha256=sha(args.csv),
                  crest_report_sha256=sha(args.crests), wet_source_targets=len(rows),
                  render_lift_m=args.render_lift_m,
                  maximum_base_native_stage_error_m=native_stage_error,
                  maximum_sum_residual_m=float(np.max(np.abs(np.asarray(residual)-args.render_lift_m))),
                  profiles=profiles, visual_accepted=False,
                  limitations="Source targets before temporal/clipping/GPU; endpoint trends are descriptive, not measured wave heights. Missing/dry samples omitted, never extrapolated.")
    args.report.write_text(json.dumps(result, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(dict(wet_source_targets=len(rows), profiles=len(profiles),
                         maximum_sum_residual_m=result["maximum_sum_residual_m"])))


if __name__ == "__main__":
    main()
