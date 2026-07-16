from pathlib import Path

from raftsim.futaleufu_cypress_review_metrics import ROI_XYXY, V32_NAMESPACE, V32_REPORT


PHYSICS_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = PHYSICS_ROOT / "src/raftsim"
EXAMPLES_ROOT = PACKAGE_ROOT / "examples"
EVIDENCE_ROOT = (
    PHYSICS_ROOT.parent
    / "docs/environment-captures/photoreal_river_previews/landscape_candidates"
)
CURRENT_REVIEW_DRIVER = (
    EXAMPLES_ROOT
    / "compare_futaleufu_cordillera_cypress_v43_merged_component_parity.py"
)


def test_locked_v43_review_has_no_historical_driver_import_chain():
    source = CURRENT_REVIEW_DRIVER.read_text(encoding="utf-8")

    assert "raftsim.futaleufu_cypress_review_metrics" in source
    assert "raftsim.examples.compare_futaleufu_cordillera_cypress_v" not in source
    assert ROI_XYXY == (280, 0, 1000, 540)
    assert V32_NAMESPACE.startswith("FutaleufuCordilleraCypressFrozenWpo")
    assert V32_REPORT.endswith("compound_branchlet_atlas_report.json")


def test_only_current_cypress_review_driver_remains_executable():
    compare_drivers = sorted(
        EXAMPLES_ROOT.glob("compare_futaleufu_cordillera_cypress_v*.py")
    )

    assert compare_drivers == [CURRENT_REVIEW_DRIVER]
    assert not list(EXAMPLES_ROOT.glob("review_futaleufu_cordillera_cypress_v*.py"))
    assert not list(PACKAGE_ROOT.glob("futaleufu_cordillera_cypress_v*_assets.py"))


def test_locked_cypress_review_evidence_is_retained():
    reviews = sorted(EVIDENCE_ROOT.glob("futaleufu_cordillera_cypress_v*review.json"))

    assert len(reviews) == 47
    assert all(review.stat().st_size > 0 for review in reviews)


def test_photoreal_test_suite_stays_split_by_concern():
    tests_root = PHYSICS_ROOT / "tests"
    split_tests = sorted(tests_root.glob("test_photoreal_*.py"))

    assert not (tests_root / "test_photoreal_environment_assets.py").exists()
    assert len(split_tests) == 16
    assert tests_root / "test_photoreal_asset_intake_b1.py" in split_tests
    assert tests_root / "test_photoreal_asset_set_intake_b1.py" in split_tests
    assert tests_root / "test_photoreal_colorado_asset_selection_b2.py" in split_tests
    assert tests_root / "test_photoreal_futaleufu_asset_selection_b2.py" in split_tests
    assert tests_root / "test_photoreal_pacuare_asset_selection_b2.py" in split_tests
    assert tests_root / "test_photoreal_south_fork_asset_selection_b2.py" in split_tests
    assert all(len(path.read_text(encoding="utf-8").splitlines()) < 2_000 for path in split_tests)
