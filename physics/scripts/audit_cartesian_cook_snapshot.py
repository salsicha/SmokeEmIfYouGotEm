"""Independently check a completed native Cartesian snapshot, never settling.

The running cook is read-only. The report is a separate, fresh JSON artifact.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np


def digest(path):
    with path.open("rb") as source:
        return hashlib.file_digest(source, "sha256").hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("cook", type=Path)
    parser.add_argument("step", type=int)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    if args.report.exists():
        raise FileExistsError(args.report)
    root = args.cook.resolve()
    original = Path((root / "input_manifest_path.txt").read_text().strip())
    if not original.is_absolute():
        original = Path(__file__).resolve().parents[2] / original
    copied = root / "input_manifest.json"
    assert digest(copied) == digest(original), "input manifest changed since cook launch"
    manifest = json.loads(copied.read_text())
    grids = [json.loads((original.parent / package / "scenario.json").read_text())["grid"]
             for package in manifest["packages"]]
    shapes = {(g["ny"], g["nx"], g["dx"], g["dy"]) for g in grids}
    assert len(shapes) == 1, "native stacked snapshot requires equal grids"
    ny, nx, dx, dy = shapes.pop()
    frame = root / f"frame_{args.step:06d}"
    record = json.loads((frame / "complete.json").read_text())
    assert record["step"] == args.step and record["snapshot"]
    arrays = {name: np.load(frame / f"{name}.npy", mmap_mode="r", allow_pickle=False)
              for name in ("h", "u", "v")}
    for name, array in arrays.items():
        assert array.shape == (len(grids)*ny, nx), (name, array.shape)
        assert array.dtype == np.dtype("<f8") and np.isfinite(array).all(), name
    h, u, v = (arrays[name] for name in ("h", "u", "v"))
    maximum_depth = float(h.max())
    maximum_speed = float(np.hypot(u, v).max())
    volume = float(h.sum(dtype=np.float64) * dx * dy)
    assert float(h.min()) >= 0 and maximum_depth <= 10 and maximum_speed <= 20
    assert abs(volume-record["volume_m3"]) < 1.e-6, "snapshot/driver volume mismatch"
    assert abs(maximum_depth-record["maximum_depth_m"]) < 1.e-12
    assert abs(maximum_speed-record["maximum_speed_mps"]) < 1.e-12
    assert record["maximum_step_residual_m3"] <= .001*manifest["dt_seconds"]
    initial_h = np.load(root / "frame_000000/h.npy", mmap_mode="r", allow_pickle=False)
    result = dict(schema="raftsim.cartesian_snapshot_audit.v1", passed=True,
                  settling_accepted=False, normal_map_integrated=False,
                  input_manifest_sha256=digest(copied), step=args.step,
                  time_seconds=record["time_seconds"], cells=int(h.size),
                  shape=list(h.shape), maximum_depth_m=maximum_depth,
                  maximum_speed_mps=maximum_speed, volume_m3=volume,
                  volume_change_from_initial_m3=volume-float(initial_h.sum()*dx*dy),
                  snapshot_driver_volume_error_m3=volume-record["volume_m3"],
                  maximum_depth_change_from_initial_m=float(np.max(np.abs(h-initial_h))),
                  maximum_step_conservation_residual_m3=record["maximum_step_residual_m3"],
                  exterior_fluxes_m3s=record["exterior_fluxes"],
                  arrays={name: dict(file=str(frame/f"{name}.npy"), sha256=digest(frame/f"{name}.npy"))
                          for name in arrays})
    args.report.write_text(json.dumps(result, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
