import json
from pathlib import Path

import numpy as np
from PIL import Image

from raftsim.south_fork_live_oak_branch_atlas import (
    ALBEDO_OPACITY_PATH,
    ATLAS_COLUMNS,
    ATLAS_ROWS,
    MANIFEST_PATH,
    NORMAL_PATH,
    OUTPUT_SIZE,
    PACKED_PATH,
    SOURCE_PATH,
    SOURCE_ROWS,
    generate_south_fork_live_oak_branch_atlas,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_live_oak_branch_atlas_generation_is_deterministic_and_fail_closed(tmp_path):
    # Regenerate into tmp so the committed atlases are never rewritten
    # mid-suite; two independent output roots prove determinism.
    first = generate_south_fork_live_oak_branch_atlas(
        REPO_ROOT, output_dir=tmp_path / "first"
    )
    first_hashes = {name: record["sha256"] for name, record in first["maps"].items()}
    second = generate_south_fork_live_oak_branch_atlas(
        REPO_ROOT, output_dir=tmp_path / "second"
    )

    assert first_hashes == {
        name: record["sha256"] for name, record in second["maps"].items()
    }
    assert first["production_promoted"] is False
    assert first["status"] == (
        "active_m9_technical_fallback_photoreal_and_release_promotion_rejected"
    )
    assert first["authority"] == {
        "affects_ecology_classification": False,
        "affects_instance_placement": False,
        "affects_collision": False,
        "affects_hydraulics": False,
    }
    assert first["integration"] == {
        "milestone": "M9",
        "active_candidate": True,
        "unreal_mesh": "/Game/RaftSim/Environment/SouthForkFullReach/Canopy/Meshes/SM_RaftSim_SouthForkInteriorLiveOak_ConnectedCrownV2",
        "unreal_material": "/Game/RaftSim/Environment/SouthForkFullReach/Canopy/Materials/M_RaftSim_SouthForkInteriorLiveOak_BranchAtlasV1",
        "core_triangles": 2,
        "branch_cards": 36,
        "branch_triangles": 72,
        "total_triangles": 74,
        "collision": "disabled",
        "photoreal_accepted": False,
        "release_promoted": False,
    }


def test_live_oak_branch_atlas_has_real_alpha_and_reserved_tiles():
    manifest = json.loads((REPO_ROOT / MANIFEST_PATH).read_text(encoding="utf-8"))
    albedo = Image.open(REPO_ROOT / ALBEDO_OPACITY_PATH)
    alpha = np.asarray(albedo, dtype=np.uint8)[..., 3]
    source_height = OUTPUT_SIZE * SOURCE_ROWS // ATLAS_ROWS

    assert (REPO_ROOT / SOURCE_PATH).is_file()
    assert albedo.mode == "RGBA"
    assert albedo.size == (OUTPUT_SIZE, OUTPUT_SIZE)
    assert np.count_nonzero(alpha[:source_height] > 8) > 100_000
    assert np.count_nonzero(alpha[:source_height] < 2) > 500_000
    assert np.count_nonzero(alpha[source_height:] > 8) == 0
    partial_edges = np.asarray(albedo, dtype=np.uint8)[(alpha > 8) & (alpha < 64), :3]
    assert partial_edges.mean(axis=0).max() < 130.0
    assert manifest["atlas"]["columns"] == ATLAS_COLUMNS
    assert manifest["atlas"]["rows"] == ATLAS_ROWS
    assert manifest["atlas"]["occupied_tiles"] == list(range(12))
    assert manifest["atlas"]["reserved_transparent_tiles"] == list(range(12, 16))
    assert manifest["derivation"]["mip_padding"]["alpha_preserved_byte_for_byte"]


def test_live_oak_branch_surface_maps_match_unreal_contract():
    normal = Image.open(REPO_ROOT / NORMAL_PATH)
    packed = Image.open(REPO_ROOT / PACKED_PATH)

    assert normal.mode == "RGB"
    assert packed.mode == "RGB"
    assert normal.size == (OUTPUT_SIZE, OUTPUT_SIZE)
    assert packed.size == (OUTPUT_SIZE, OUTPUT_SIZE)
