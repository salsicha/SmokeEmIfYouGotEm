import json
from pathlib import Path

import numpy as np
from PIL import Image

from raftsim.south_fork_live_oak_leaf_clusters_v3 import (
    ALBEDO_OPACITY_PATH,
    ALPHA_SOURCE_PATH,
    CHROMA_SOURCE_PATH,
    IMAGEGEN_PROMPT,
    MANIFEST_PATH,
    NORMAL_PATH,
    OUTPUT_SIZE,
    PACKED_PATH,
    generate_south_fork_live_oak_leaf_clusters_v3,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_dense_live_oak_leaf_clusters_v3_are_deterministic_and_isolated(tmp_path):
    # Regenerate into tmp so the committed atlases are never rewritten
    # mid-suite; two independent output roots prove determinism.
    first = generate_south_fork_live_oak_leaf_clusters_v3(
        REPO_ROOT, output_dir=tmp_path / "first"
    )
    first_hashes = {
        name: record["sha256"] for name, record in first["maps"].items()
    }
    second = generate_south_fork_live_oak_leaf_clusters_v3(
        REPO_ROOT, output_dir=tmp_path / "second"
    )

    assert first_hashes == {
        name: record["sha256"] for name, record in second["maps"].items()
    }
    assert first["production_promoted"] is False
    assert first["integration"]["active_candidate"] is False
    assert first["integration"]["photoreal_accepted"] is False
    assert first["source"]["referenced_images"] == []
    assert first["source"]["prompt"] == IMAGEGEN_PROMPT
    assert first["atlas"]["occupied_tiles"] == list(range(4))
    assert first["atlas"]["reserved_transparent_tiles"] == list(range(4, 16))
    assert first["atlas"]["occupied_band_opaque_pixel_count"] > 250_000
    assert first["atlas"]["reserved_band_opaque_pixel_count"] == 0
    assert all(value is False for value in first["authority"].values())


def test_dense_live_oak_leaf_clusters_v3_maps_preserve_alpha_and_pbr_contract():
    manifest = json.loads((REPO_ROOT / MANIFEST_PATH).read_text(encoding="utf-8"))
    albedo = Image.open(REPO_ROOT / ALBEDO_OPACITY_PATH)
    normal = Image.open(REPO_ROOT / NORMAL_PATH)
    packed = Image.open(REPO_ROOT / PACKED_PATH)

    assert (REPO_ROOT / CHROMA_SOURCE_PATH).is_file()
    assert (REPO_ROOT / ALPHA_SOURCE_PATH).is_file()
    assert albedo.size == (OUTPUT_SIZE, OUTPUT_SIZE)
    assert normal.size == (OUTPUT_SIZE, OUTPUT_SIZE)
    assert packed.size == (OUTPUT_SIZE, OUTPUT_SIZE)
    assert albedo.mode == "RGBA"
    assert normal.mode == "RGB"
    assert packed.mode == "RGB"
    alpha = np.asarray(albedo, dtype=np.uint8)[..., 3]
    assert np.count_nonzero(alpha > 8) == (
        manifest["atlas"]["occupied_band_opaque_pixel_count"]
    )
    assert np.count_nonzero(alpha[OUTPUT_SIZE // 4 :] > 8) == 0
