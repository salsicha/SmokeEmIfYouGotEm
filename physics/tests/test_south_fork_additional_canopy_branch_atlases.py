import json
from pathlib import Path

import numpy as np
from PIL import Image

from raftsim.south_fork_additional_canopy_branch_atlases import (
    MANIFEST_PATH,
    PROFILES,
    generate_south_fork_additional_canopy_branch_atlases,
)
from raftsim.south_fork_live_oak_branch_atlas import OUTPUT_SIZE

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_additional_canopy_branch_atlases_are_deterministic_and_fail_closed():
    first = generate_south_fork_additional_canopy_branch_atlases(REPO_ROOT)
    first_hashes = {
        key: {name: record["sha256"] for name, record in profile["maps"].items()}
        for key, profile in first["profiles"].items()
    }
    second = generate_south_fork_additional_canopy_branch_atlases(REPO_ROOT)

    assert first_hashes == {
        key: {name: record["sha256"] for name, record in profile["maps"].items()}
        for key, profile in second["profiles"].items()
    }
    assert set(first["profiles"]) == {
        "ponderosa_pine",
        "white_alder",
        "deerbrush",
    }
    assert first["production_promoted"] is False
    assert first["authority"] == {
        "affects_ecology_classification": False,
        "affects_instance_placement": False,
        "affects_collision": False,
        "affects_hydraulics": False,
    }


def test_additional_canopy_branch_atlases_have_real_alpha_and_reserved_tiles():
    manifest = json.loads((REPO_ROOT / MANIFEST_PATH).read_text(encoding="utf-8"))
    for profile in PROFILES:
        albedo = Image.open(REPO_ROOT / profile.albedo_opacity_path)
        alpha = np.asarray(albedo, dtype=np.uint8)[..., 3]
        source_height = OUTPUT_SIZE * 3 // 4
        assert (REPO_ROOT / profile.source_path).is_file()
        assert albedo.mode == "RGBA"
        assert albedo.size == (OUTPUT_SIZE, OUTPUT_SIZE)
        assert np.count_nonzero(alpha[:source_height] > 8) > 80_000
        assert np.count_nonzero(alpha[:source_height] < 2) > 500_000
        assert np.count_nonzero(alpha[source_height:] > 8) == 0
        profile_manifest = manifest["profiles"][profile.key]
        assert profile_manifest["atlas"]["occupied_tiles"] == list(range(12))
        assert profile_manifest["atlas"]["reserved_transparent_tiles"] == list(
            range(12, 16)
        )
        assert profile_manifest["derivation"]["mip_padding"][
            "alpha_preserved_byte_for_byte"
        ]


def test_additional_canopy_branch_surface_maps_match_unreal_contract():
    for profile in PROFILES:
        normal = Image.open(REPO_ROOT / profile.normal_path)
        packed = Image.open(REPO_ROOT / profile.packed_path)
        assert normal.mode == "RGB"
        assert packed.mode == "RGB"
        assert normal.size == (OUTPUT_SIZE, OUTPUT_SIZE)
        assert packed.size == (OUTPUT_SIZE, OUTPUT_SIZE)
