import json
from pathlib import Path

import pytest

from raftsim.canopy_review_mining import (
    build_canopy_review_report,
    discover_review_paths,
    render_canopy_review_markdown,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
REPORT_ROOT = REPO_ROOT / "physics" / "reports" / "canopy_strategy"


def test_futaleufu_canopy_review_history_is_complete_and_ordered():
    paths = discover_review_paths(REPO_ROOT)

    assert len(paths) == 47
    assert paths[0].name.startswith("futaleufu_cordillera_cypress_v1_")
    assert paths[-1].name.startswith("futaleufu_cordillera_cypress_v43_")
    assert [path.name for path in paths if "_v20" in path.name][:2] == [
        "futaleufu_cordillera_cypress_v20_botanical_spray_visual_review.json",
        "futaleufu_cordillera_cypress_v20_1_dense_botanical_spray_visual_review.json",
    ]


def test_futaleufu_canopy_review_report_preserves_the_failed_upper_bound():
    report = build_canopy_review_report(REPO_ROOT)
    v42 = next(row for row in report["rows"] if row["version"] == "v42")
    v43 = next(row for row in report["rows"] if row["version"] == "v43")

    assert report["schema"] == "raftsim.futaleufu.canopy_review_history.v1"
    assert report["review_count"] == 47
    assert report["production_promotion_count"] == 0
    assert report["iterations_per_gate_class"] == {
        "hlod_projection_transition": 9,
        "lit_shape_material_shadow": 8,
        "morphology_visibility": 28,
        "temporal_handoff": 2,
    }
    assert v42["metrics"]["frontlit_silhouette_iou"] == pytest.approx(0.9005226040)
    assert v42["metrics"]["backlit_silhouette_iou"] == pytest.approx(0.7171796003)
    assert v43["metrics"]["frontlit_silhouette_iou"] is None
    assert v43["metrics"]["backlit_silhouette_iou"] is None
    assert report["late_backlit_silhouette"]["trajectory"] == "not_converged"


def test_futaleufu_canopy_review_report_matches_generator():
    expected = build_canopy_review_report(REPO_ROOT)

    assert json.loads((REPORT_ROOT / "futaleufu_review_history.json").read_text(encoding="utf-8")) == expected
    assert (REPORT_ROOT / "futaleufu_review_history.md").read_text(encoding="utf-8") == (
        render_canopy_review_markdown(expected)
    )
