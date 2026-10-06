from __future__ import annotations

from pathlib import Path

from PIL import Image

from raftsim.chilko_lava_canyon_visual_water import (
    FLOW_BAND,
    PACKED_TEXTURE_RELATIVE,
    SCHEMA,
    build_chilko_lava_canyon_visual_water,
)


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_build_chilko_lava_canyon_visual_water(tmp_path: Path) -> None:
    # Regenerate into tmp so the committed texture/manifest are never
    # rewritten mid-suite (divergent bytes off macOS would cascade into
    # downstream hash-lock tests).
    manifest = build_chilko_lava_canyon_visual_water(REPO_ROOT, output_dir=tmp_path)

    assert manifest["schema"] == SCHEMA
    assert manifest["flow_band"] == FLOW_BAND
    assert manifest["solver_evidence"]["solver"] == "raftsim_water_cpp_v1"
    assert manifest["solver_evidence"]["feature_strength_scale"] == 0.0
    assert manifest["solver_evidence"]["converged"] is False
    assert manifest["hydraulic_visualization_evidence"]["wet_cell_count"] > 5000
    assert manifest["hydraulic_visualization_evidence"][
        "supercritical_cell_count"
    ] > 0
    assert manifest["hydraulic_visualization_evidence"][
        "foam_eligible_cell_count"
    ] > 0
    assert manifest["render_binding"]["map"] == "/Game/RaftSim/Maps/L_LavaCanyon"
    assert manifest["render_binding"]["capture_only"] is True
    assert manifest["authority_policy"]["changes_solver_state"] is False

    image = Image.open(tmp_path / PACKED_TEXTURE_RELATIVE.name)
    assert image.mode == "RGBA"
    assert image.size == (1024, 256)
