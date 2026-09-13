"""Check whether a completed flow snapshot wets artificial tile-union banks.

Read-only with respect to the running cook. This is an export-domain diagnostic,
not a settling or visual acceptance test. Never count shared tile faces as banks.
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
    assert not args.report.exists()
    root = args.cook.resolve()
    original = Path((root / "input_manifest_path.txt").read_text().strip())
    if not original.is_absolute():
        original = Path(__file__).resolve().parents[2] / original
    assert digest(original) == digest(root / "input_manifest.json")
    manifest = json.loads(original.read_text())
    inputs = {entry["name"]: entry for entry in manifest["inputs"]}
    scenarios = []
    for package in manifest["packages"]:
        path = original.parent / package / "scenario.json"
        assert digest(path) == inputs[package]["files"]["scenario.json"]
        scenarios.append(json.loads(path.read_text()))
    grids = [scenario["grid"] for scenario in scenarios]
    shapes = {(g["ny"], g["nx"], g["dx"], g["dy"]) for g in grids}
    assert len(shapes) == 1
    ny, nx, dx, dy = shapes.pop()
    origins = np.array([(g["origin_x"], g["origin_y"]) for g in grids])
    indexes = (origins - origins.min(axis=0)) / np.array([nx*dx, ny*dy])
    assert np.max(np.abs(indexes - np.rint(indexes))) < 1.e-9
    indexes = np.rint(indexes).astype(int)
    occupied = {tuple(index) for index in indexes}
    assert len(occupied) == len(grids)
    frame = root / f"frame_{args.step:06d}"
    complete = json.loads((frame / "complete.json").read_text())
    assert complete["step"] == args.step and complete["snapshot"]
    h_path = frame / "h.npy"
    h = np.load(h_path, mmap_mode="r", allow_pickle=False)
    initial = np.load(root / "frame_000000/h.npy", mmap_mode="r", allow_pickle=False)
    assert h.shape == initial.shape == (len(grids)*ny, nx)
    assert h.dtype == initial.dtype == np.dtype("<f8")
    assert np.isfinite(h).all() and h.min() >= 0
    directions = {"west": (-1, 0), "east": (1, 0), "south": (0, -1), "north": (0, 1)}
    bank_edges, physical_edges, shared_faces = [], [], 0
    depths, initial_depths = [], []
    for owner, (scenario, index) in enumerate(zip(scenarios, indexes)):
        tile = h[owner*ny:(owner+1)*ny]
        start = initial[owner*ny:(owner+1)*ny]
        for edge, delta in directions.items():
            if tuple(index + delta) in occupied:
                shared_faces += 1
                continue
            boundary = next(b for b in scenario["boundaries"] if b["edge"] == edge)
            if boundary["kind"] != "bank":
                physical_edges.append(dict(package=manifest["packages"][owner], edge=edge, kind=boundary["kind"]))
                continue
            selector = {"west": (slice(None), 0), "east": (slice(None), -1),
                        "south": (0, slice(None)), "north": (-1, slice(None))}[edge]
            values, before = tile[selector], start[selector]
            depths.extend(values.tolist())
            initial_depths.extend(before.tolist())
            bank_edges.append(dict(package=manifest["packages"][owner], edge=edge,
                                   maximum_depth_m=float(values.max()), initial_maximum_depth_m=float(before.max()),
                                   wet_face_cells=int(np.count_nonzero(values > 0.))))
    depths, initial_depths = np.asarray(depths), np.asarray(initial_depths)
    result = dict(schema="raftsim.cartesian_exterior_bank_audit.v1", step=args.step,
                  time_seconds=complete["time_seconds"], input_manifest_sha256=digest(original),
                  h_sha256=digest(h_path), shared_directed_tile_faces=shared_faces,
                  physical_exterior_faces=physical_edges, bank_tile_faces=len(bank_edges),
                  bank_face_cells=len(depths), maximum_bank_depth_m=float(depths.max()),
                  initial_maximum_bank_depth_m=float(initial_depths.max()),
                  counts_above_depth_m={str(t): int(np.count_nonzero(depths > t)) for t in (0., 1.e-6, .001, .01)},
                  all_artificial_banks_exactly_dry=bool(np.all(depths == 0.)),
                  settling_accepted=False, normal_map_integrated=False,
                  wet_bank_edges=[edge for edge in bank_edges if edge["wet_face_cells"]])
    args.report.write_text(json.dumps(result, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k != "wet_bank_edges"}, indent=2))


if __name__ == "__main__":
    main()
