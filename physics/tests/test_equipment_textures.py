from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image

from raftsim.equipment_textures import TEXTILES, generate_equipment_textures


def _write_sources(root: Path) -> None:
    y, x = np.mgrid[0:257, 0:257]
    pattern = 0.55 + 0.08 * np.sin(x * 0.29) * np.cos(y * 0.23)
    rgb = np.repeat(np.clip(pattern, 0.0, 1.0)[..., None], 3, axis=2)
    pixels = np.round(rgb * 255.0).astype(np.uint8)
    for spec in TEXTILES:
        Image.fromarray(pixels, "RGB").save(root / spec.raw_filename)


def _hashes(root: Path) -> dict[str, str]:
    return {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(root.glob("*"))
        if path.is_file()
    }


def test_equipment_texture_generation_is_deterministic_and_tile_safe(tmp_path: Path) -> None:
    source = tmp_path / "raw"
    first = tmp_path / "first"
    second = tmp_path / "second"
    source.mkdir()
    _write_sources(source)

    manifest = generate_equipment_textures(source, first)
    generate_equipment_textures(source, second)

    assert manifest["schema"] == "raftsim.equipment.generated_textile_pbr.v1"
    assert len(manifest["assets"]) == 3
    assert _hashes(first) == _hashes(second)
    for spec in TEXTILES:
        for suffix in ("Albedo", "Normal", "AORoughnessHeight"):
            path = first / f"{spec.unreal_stem}_{suffix}.png"
            image = np.asarray(Image.open(path).convert("RGB"), dtype=np.int16)
            assert image.shape == (1024, 1024, 3)
            horizontal_seam = np.abs(image[:, 0] - image[:, -1]).mean()
            vertical_seam = np.abs(image[0] - image[-1]).mean()
            assert horizontal_seam < 18.0
            assert vertical_seam < 18.0

    stored = json.loads((first / "generated_textile_pbr_manifest.json").read_text())
    assert stored["status"].endswith("render_reviewed_not_photoreal")
    assert stored["render_review"].endswith("m9_equipment_textile_fallback_v280_review.json")
