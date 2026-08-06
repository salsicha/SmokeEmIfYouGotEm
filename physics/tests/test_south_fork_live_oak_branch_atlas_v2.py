import json
from pathlib import Path

import numpy as np
from PIL import Image

from raftsim.south_fork_live_oak_branch_atlas_v2 import (
    ALBEDO_OPACITY_PATH,
    ALPHA_SOURCE_PATH,
    ATLAS_COLUMNS,
    ATLAS_ROWS,
    CHROMA_SOURCE_PATH,
    IMAGEGEN_PROMPT,
    MANIFEST_PATH,
    NORMAL_PATH,
    OUTPUT_SIZE,
    PACKED_PATH,
    SOURCE_ROWS,
    generate_south_fork_live_oak_branch_atlas_v2,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_live_oak_branch_atlas_v2_generation_is_deterministic_and_fail_closed(tmp_path):
    # Regenerate into tmp so the committed atlases are never rewritten
    # mid-suite; two independent output roots prove determinism.
    first = generate_south_fork_live_oak_branch_atlas_v2(
        REPO_ROOT, output_dir=tmp_path / "first"
    )
    first_hashes = {name: record["sha256"] for name, record in first["maps"].items()}
    second = generate_south_fork_live_oak_branch_atlas_v2(
        REPO_ROOT, output_dir=tmp_path / "second"
    )

    assert first_hashes == {
        name: record["sha256"] for name, record in second["maps"].items()
    }
    assert first["production_promoted"] is False
    assert first["status"] == "m9_review_only_visual_promotion_rejected"
    assert first["source"]["referenced_images"] == []
    assert first["source"]["prompt"] == IMAGEGEN_PROMPT
    assert first["integration"]["active_candidate"] is False
    assert first["integration"]["photoreal_accepted"] is False
    assert first["integration"]["release_promoted"] is False
    assert first["authority"] == {
        "affects_ecology_classification": False,
        "affects_instance_placement": False,
        "affects_collision": False,
        "affects_hydraulics": False,
    }


def test_live_oak_branch_atlas_v2_has_alpha_reserved_tiles_and_maps():
    manifest = json.loads((REPO_ROOT / MANIFEST_PATH).read_text(encoding="utf-8"))
    albedo = Image.open(REPO_ROOT / ALBEDO_OPACITY_PATH)
    normal = Image.open(REPO_ROOT / NORMAL_PATH)
    packed = Image.open(REPO_ROOT / PACKED_PATH)
    alpha = np.asarray(albedo, dtype=np.uint8)[..., 3]
    occupied_height = OUTPUT_SIZE * SOURCE_ROWS // ATLAS_ROWS

    assert (REPO_ROOT / CHROMA_SOURCE_PATH).is_file()
    assert (REPO_ROOT / ALPHA_SOURCE_PATH).is_file()
    assert albedo.mode == "RGBA"
    assert albedo.size == (OUTPUT_SIZE, OUTPUT_SIZE)
    assert normal.mode == "RGB" and normal.size == albedo.size
    assert packed.mode == "RGB" and packed.size == albedo.size
    assert np.count_nonzero(alpha[:occupied_height] > 8) > 250_000
    assert np.count_nonzero(alpha[:occupied_height] < 2) > 1_000_000
    assert np.count_nonzero(alpha[occupied_height:] > 8) == 0
    assert manifest["atlas"]["columns"] == ATLAS_COLUMNS
    assert manifest["atlas"]["rows"] == ATLAS_ROWS
    assert manifest["atlas"]["occupied_tiles"] == list(range(12))
    assert manifest["atlas"]["reserved_transparent_tiles"] == list(range(12, 16))
    assert manifest["derivation"]["mip_padding"]["alpha_preserved_byte_for_byte"]
