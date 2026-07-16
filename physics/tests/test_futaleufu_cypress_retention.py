from pathlib import Path

from raftsim.futaleufu_cypress_review_metrics import ROI_XYXY, V32_NAMESPACE, V32_REPORT


PHYSICS_ROOT = Path(__file__).resolve().parents[1]
CURRENT_REVIEW_DRIVER = (
    PHYSICS_ROOT
    / "src/raftsim/examples/compare_futaleufu_cordillera_cypress_v43_merged_component_parity.py"
)


def test_locked_v43_review_has_no_historical_driver_import_chain():
    source = CURRENT_REVIEW_DRIVER.read_text(encoding="utf-8")

    assert "raftsim.futaleufu_cypress_review_metrics" in source
    assert "raftsim.examples.compare_futaleufu_cordillera_cypress_v" not in source
    assert ROI_XYXY == (280, 0, 1000, 540)
    assert V32_NAMESPACE.startswith("FutaleufuCordilleraCypressFrozenWpo")
    assert V32_REPORT.endswith("compound_branchlet_atlas_report.json")
