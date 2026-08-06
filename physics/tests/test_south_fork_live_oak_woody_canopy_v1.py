import json
from pathlib import Path

import numpy as np
from PIL import Image

from raftsim.south_fork_live_oak_woody_canopy_v1 import (
    BARK_ALBEDO_PATH,
    BARK_NORMAL_PATH,
    BARK_PACKED_PATH,
    BARK_SOURCE_PATH,
    IMAGEGEN_PROMPT,
    MANIFEST_PATH,
    OUTPUT_SIZE,
    generate_south_fork_live_oak_woody_canopy_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_live_oak_woody_canopy_bark_generation_is_deterministic_and_isolated(tmp_path):
    # Regenerate into tmp so the committed atlases are never rewritten
    # mid-suite; two independent output roots prove determinism.
    first = generate_south_fork_live_oak_woody_canopy_v1(
        REPO_ROOT, output_dir=tmp_path / "first"
    )
    first_hashes = {
        name: record["sha256"] for name, record in first["maps"].items()
    }
    second = generate_south_fork_live_oak_woody_canopy_v1(
        REPO_ROOT, output_dir=tmp_path / "second"
    )

    assert first_hashes == {
        name: record["sha256"] for name, record in second["maps"].items()
    }
    assert first["production_promoted"] is False
    assert first["source"]["referenced_images"] == []
    assert first["source"]["prompt"] == IMAGEGEN_PROMPT
    assert first["geometry_contract"]["true_woody_topology"] is True
    assert first["geometry_contract"]["billboard_core"] is False
    assert first["authority"] == {
        "affects_ecology_classification": False,
        "affects_instance_placement": False,
        "affects_collision": False,
        "affects_hydraulics": False,
        "affects_navigation": False,
    }


def test_live_oak_woody_canopy_bark_maps_are_periodic_power_of_two_pbr_maps():
    manifest = json.loads((REPO_ROOT / MANIFEST_PATH).read_text(encoding="utf-8"))
    images = {
        "albedo": Image.open(REPO_ROOT / BARK_ALBEDO_PATH),
        "normal": Image.open(REPO_ROOT / BARK_NORMAL_PATH),
        "packed": Image.open(REPO_ROOT / BARK_PACKED_PATH),
    }

    assert (REPO_ROOT / BARK_SOURCE_PATH).is_file()
    assert images["albedo"].mode == "RGB"
    assert images["normal"].mode == "RGB"
    assert images["packed"].mode == "RGB"
    for image in images.values():
        assert image.size == (OUTPUT_SIZE, OUTPUT_SIZE)
        pixels = np.asarray(image, dtype=np.uint8)
        assert np.array_equal(pixels[:, 0], pixels[:, -1])
        assert np.array_equal(pixels[0], pixels[-1])
    assert all(
        value is True
        for key, value in manifest["periodic_edge_contract"].items()
        if key.endswith("_exact")
    )
