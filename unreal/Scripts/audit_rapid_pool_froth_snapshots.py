"""Read actual native GPU readbacks; no simulation, images, or FPS fabrication.

These statistics do not replace native pixel review or prove every map's
rapid/pool placement. Source-edge bubbles can exist briefly after aeration.
"""
import argparse
import json
import math
from pathlib import Path

import numpy as np


def within_source_distance(active: np.ndarray, cell_m: float, radius_m: float) -> np.ndarray:
    """Exact regular-grid cell-centre distance mask using NumPy only."""
    if not math.isfinite(cell_m) or cell_m <= 0:
        raise ValueError("Invalid native grid spacing")
    near = np.zeros_like(active)
    height, width = active.shape
    reach = math.ceil(radius_m / cell_m)
    for dy in range(-min(height - 1, reach), min(height - 1, reach) + 1):
        for dx in range(-min(width - 1, reach), min(width - 1, reach) + 1):
            if (dx * dx + dy * dy) * cell_m * cell_m > radius_m * radius_m:
                continue
            y0, y1 = max(0, dy), min(height, height + dy)
            x0, x1 = max(0, dx), min(width, width + dx)
            near[y0:y1, x0:x1] |= active[y0-dy:y1-dy, x0-dx:x1-dx]
    return near


def audit(directory: Path) -> dict:
    files = sorted(directory.glob("detail_*.json"))
    if len(files) < 2:
        raise ValueError("Two actual native snapshots required")
    snapshots = []
    for metadata_file in files:
        metadata = json.loads(metadata_file.read_text(encoding="utf-8-sig"))
        if metadata["schema"] != "raftsim.detail.snapshot.v2" or not metadata["arrays_complete"]:
            raise ValueError("Missing actual same-upload source geometry")
        if metadata["performance_qualification"] or metadata["shape"][2] != 4:
            raise ValueError("Snapshot provenance or shape mismatch")
        arrays = {}
        for field in ("flow", "state", "surface", "mean_geometry"):
            data = np.fromfile(metadata_file.with_suffix(f".{field}.f32"), dtype="<f4")
            if data.size != np.prod(metadata["shape"]) or not np.isfinite(data).all():
                raise ValueError(f"Nonfinite/incomplete actual {field} readback")
            arrays[field] = data.reshape(metadata["shape"])
        source = arrays["flow"][..., 3]
        density = arrays["state"][..., 3]
        wet = arrays["mean_geometry"][..., 3] > 0.5
        wet &= arrays["mean_geometry"][..., 2] > 0.01
        if not wet.any() or (density < 0).any():
            raise ValueError("No wet observations or negative froth")
        active = wet & (source > 0.01)
        quiet = wet & ~active
        # This is a diagnostic distance, NOT a rendering/simulation cutoff.
        remote = wet & ~within_source_distance(active, metadata["cell_m"], 4.0)
        snapshots.append({
            "metadata": str(metadata_file.resolve()),
            "elapsed_wall_s": metadata["elapsed_s"],
            "committed_simulation_s": metadata["simulation_s"],
            "wet_cells": int(wet.sum()),
            "active_aeration_cells": int(active.sum()),
            "maximum_active_density": float(density[active].max()) if active.any() else None,
            "no_local_source_cells": int(quiet.sum()),
            "no_local_source_density_median": float(np.median(density[quiet])) if quiet.any() else None,
            "no_local_source_density_p99": float(np.percentile(density[quiet], 99)) if quiet.any() else None,
            "wet_cells_more_than_4m_from_sources": int(remote.sum()),
            "maximum_density_more_than_4m_from_sources": float(density[remote].max()) if remote.any() else None,
            "all_four_arrays_finite": True,
            "density_nonnegative": True,
        })
    times = [snapshot["committed_simulation_s"] for snapshot in snapshots]
    if not all(np.isfinite(times)) or times[-1] <= times[0]:
        raise ValueError("Native water clock did not advance across snapshots")
    return {
        "schema": "raftsim.native_rapid_pool_froth_observation.v1",
        "directory": str(directory.resolve()),
        "snapshots": snapshots,
        "actual_gpu_readback_and_clock_health_verified": True,
        "visual_review_or_20fps_accepted": False,
        "scope": "Actual cooked/editor GPU observations only; no-source edges can retain brief fresh bubbles. Distance statistics are diagnostic, not a clipping rule. No solved bubble-rise CFD, full-map trajectory, or performance claim.",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    arguments = parser.parse_args()
    print(json.dumps(audit(arguments.directory), indent=2, allow_nan=False))
