from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
from PIL import Image


EXPECTED_CAPTURE_NAMES = (
    "chili_bar_launch_downstream.png",
    "meat_grinder_guide_eye.png",
    "troublemaker_approach.png",
    "coloma_bridge_context.png",
    "salmon_falls_takeout.png",
)


@dataclass(frozen=True)
class CaptureRepeatThresholds:
    maximum_changed_pixels: int = 32
    maximum_changed_fraction: float = 0.00005
    maximum_mean_absolute_channel_error: float = 0.0001
    maximum_channel_delta: int = 8


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compare_capture_sets(
    baseline_dir: Path,
    repeat_dir: Path,
    thresholds: CaptureRepeatThresholds = CaptureRepeatThresholds(),
) -> dict[str, object]:
    results: list[dict[str, object]] = []
    for name in EXPECTED_CAPTURE_NAMES:
        baseline_path = baseline_dir / name
        repeat_path = repeat_dir / name
        if not baseline_path.is_file() or not repeat_path.is_file():
            raise FileNotFoundError(f"missing capture pair for {name}")

        with Image.open(baseline_path) as baseline_image:
            baseline = np.asarray(baseline_image.convert("RGB"), dtype=np.int16)
        with Image.open(repeat_path) as repeat_image:
            repeat = np.asarray(repeat_image.convert("RGB"), dtype=np.int16)
        if baseline.shape != repeat.shape:
            raise ValueError(
                f"capture dimensions differ for {name}: "
                f"{baseline.shape} != {repeat.shape}"
            )

        delta = np.abs(baseline - repeat)
        changed_pixels = int(np.count_nonzero(np.any(delta != 0, axis=2)))
        pixel_count = int(baseline.shape[0] * baseline.shape[1])
        changed_fraction = changed_pixels / pixel_count
        mean_absolute_channel_error = float(np.mean(delta))
        maximum_channel_delta = int(np.max(delta))
        byte_identical = baseline_path.read_bytes() == repeat_path.read_bytes()
        passed = (
            changed_pixels <= thresholds.maximum_changed_pixels
            and changed_fraction <= thresholds.maximum_changed_fraction
            and mean_absolute_channel_error
            <= thresholds.maximum_mean_absolute_channel_error
            and maximum_channel_delta <= thresholds.maximum_channel_delta
        )
        results.append(
            {
                "capture": name,
                "baseline_sha256": _sha256(baseline_path),
                "repeat_sha256": _sha256(repeat_path),
                "byte_identical": byte_identical,
                "width": int(baseline.shape[1]),
                "height": int(baseline.shape[0]),
                "changed_pixels": changed_pixels,
                "changed_fraction": changed_fraction,
                "mean_absolute_channel_error": mean_absolute_channel_error,
                "maximum_channel_delta": maximum_channel_delta,
                "passed": passed,
            }
        )

    return {
        "schema": "raftsim.south_fork.capture_repeat.v1",
        "contract": (
            "Independent renderer processes must load the same settled saved map "
            "without regeneration. Sparse platform floating-point raster differences "
            "may not exceed the locked per-image pixel and channel thresholds."
        ),
        "baseline_directory": str(baseline_dir),
        "repeat_directory": str(repeat_dir),
        "thresholds": asdict(thresholds),
        "captures": results,
        "all_byte_identical": all(row["byte_identical"] for row in results),
        "passed": all(row["passed"] for row in results),
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate two independent South Fork fixed-camera capture sets."
    )
    parser.add_argument("--baseline-dir", type=Path, required=True)
    parser.add_argument("--repeat-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    report = compare_capture_sets(args.baseline_dir, args.repeat_dir)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    raise SystemExit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()
