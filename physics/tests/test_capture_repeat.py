from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image

from raftsim.capture_repeat import (
    EXPECTED_CAPTURE_NAMES,
    CaptureRepeatThresholds,
    compare_capture_sets,
)


def _write_capture_set(root: Path, pixels: np.ndarray) -> None:
    root.mkdir(parents=True, exist_ok=True)
    for name in EXPECTED_CAPTURE_NAMES:
        Image.fromarray(pixels, mode="RGB").save(root / name)


def test_capture_repeat_accepts_sparse_bounded_renderer_drift(tmp_path: Path) -> None:
    baseline = np.full((32, 64, 3), 96, dtype=np.uint8)
    repeated = baseline.copy()
    repeated[4, 7, 1] += 1
    repeated[11, 29, 2] += 6
    _write_capture_set(tmp_path / "baseline", baseline)
    _write_capture_set(tmp_path / "repeat", repeated)

    report = compare_capture_sets(
        tmp_path / "baseline",
        tmp_path / "repeat",
        CaptureRepeatThresholds(
            maximum_changed_pixels=2,
            maximum_changed_fraction=0.001,
            maximum_mean_absolute_channel_error=0.002,
            maximum_channel_delta=6,
        ),
    )

    assert report["passed"] is True
    assert report["all_byte_identical"] is False
    assert all(row["passed"] for row in report["captures"])


def test_capture_repeat_rejects_material_scene_change(tmp_path: Path) -> None:
    baseline = np.full((32, 64, 3), 96, dtype=np.uint8)
    repeated = baseline.copy()
    repeated[0:8, 0:8, :] = 160
    _write_capture_set(tmp_path / "baseline", baseline)
    _write_capture_set(tmp_path / "repeat", repeated)

    report = compare_capture_sets(tmp_path / "baseline", tmp_path / "repeat")

    assert report["passed"] is False
    assert any(not row["passed"] for row in report["captures"])
