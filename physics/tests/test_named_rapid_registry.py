import json
from pathlib import Path

from PIL import Image

from raftsim.named_rapid_registry import (
    EDITOR_GEOMETRY_RELATIVE_PATH,
    EDITOR_MARKERS_RELATIVE_PATH,
    SIMULATOR_RUNS_RELATIVE_PATH,
    SOURCE_CATALOG_RELATIVE_PATH,
    build_editor_markers,
    build_editor_geometry_geojson,
    build_simulator_review_runs,
    validate_source_catalog,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
EDITOR_SHELL_HEADER = (
    REPO_ROOT
    / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Public/RaftSimRapidRiverEditorShell.h"
)
EDITOR_MODULE = (
    REPO_ROOT
    / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/RaftSimEditorModule.cpp"
)
VALIDATION_ACTIONS = (
    REPO_ROOT
    / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/RaftSimToolValidationActions.cpp"
)
EDITOR_SHELL_MANIFEST = REPO_ROOT / "unreal/Content/RaftSim/Tools/rapid_river_editor_shell.json"
EDITOR_BROWSER_CAPTURE = REPO_ROOT / "docs/tool-captures/milestone25a/RapidRiverEditor.png"


def _load(relative_path: str) -> dict:
    return json.loads((REPO_ROOT / relative_path).read_text(encoding="utf-8"))


def test_named_rapid_catalog_covers_all_five_runs_with_rights_gated_sources():
    catalog = _load(SOURCE_CATALOG_RELATIVE_PATH)
    validate_source_catalog(catalog)

    expected_counts = {
        "south_fork_american_chili_bar": 20,
        "colorado_river_grand_canyon_rowing": 15,
        "pacuare_river_costa_rica": 15,
        "zambezi_batoka_gorge": 25,
        "futaleufu_river_chile": 5,
    }
    assert {river["river_id"]: len(river["rapids"]) for river in catalog["rivers"]} == expected_counts
    assert all(source["url"].startswith("https://") for source in catalog["sources"])
    assert all(
        source["rights_status"].startswith(("link_only", "government_source"))
        for source in catalog["sources"]
    )
    assert catalog["status"] == "review_baseline_not_guide_approved"


def test_editor_markers_preserve_published_stationing_and_flag_interpolation():
    catalog = _load(SOURCE_CATALOG_RELATIVE_PATH)
    generated = build_editor_markers(catalog, REPO_ROOT)
    committed = _load(EDITOR_MARKERS_RELATIVE_PATH)
    assert generated == committed
    assert committed["production_promoted"] is False
    assert sum(river["marker_count"] for river in committed["rivers"]) == 80

    rivers = {river["river_id"]: river for river in committed["rivers"]}
    south_fork = {marker["display_name"]: marker for marker in rivers["south_fork_american_chili_bar"]["markers"]}
    assert south_fork["Meat Grinder"]["stationing"]["station_m"] == 965.606
    assert south_fork["Meat Grinder"]["stationing"]["production_authoritative"] is True

    colorado = {marker["display_name"]: marker for marker in rivers["colorado_river_grand_canyon_rowing"]["markers"]}
    assert colorado["House Rock"]["stationing"]["station_kind"] == "published_river_mile_converted"
    assert colorado["House Rock"]["stationing"]["production_authoritative"] is False

    pacuare = rivers["pacuare_river_costa_rica"]["markers"]
    assert all(
        marker["stationing"]["station_kind"] == "provisional_downstream_order_interpolation"
        and marker["stationing"]["production_authoritative"] is False
        for marker in pacuare
    )
    assert [marker["display_name"] for marker in pacuare][3:6] == [
        "Upper Huacas",
        "Bobo Falls",
        "Lower Huacas",
    ]


def test_editor_geometry_is_candidate_only_and_blocks_misaligned_south_fork():
    markers = _load(EDITOR_MARKERS_RELATIVE_PATH)
    generated = build_editor_geometry_geojson(markers)
    committed = _load(EDITOR_GEOMETRY_RELATIVE_PATH)
    assert generated == committed
    assert committed["feature_count"] == 45
    assert committed["production_promoted"] is False
    assert {feature["properties"]["river_id"] for feature in committed["features"]} == {
        "pacuare_river_costa_rica",
        "zambezi_batoka_gorge",
        "futaleufu_river_chile",
    }
    assert all(
        feature["properties"]["production_authoritative"] is False
        and feature["properties"]["geometry_status"]
        == "candidate_centerline_projection_not_exact"
        for feature in committed["features"]
    )
    south_fork = next(
        river for river in markers["rivers"]
        if river["river_id"] == "south_fork_american_chili_bar"
    )
    assert all(marker["editor_map_geometry"] is None for marker in south_fork["markers"])
    alignment_review = _load(
        "physics/data/real_world/south_fork_american_chili_bar/review/"
        "named_rapid_station_alignment_review.json"
    )
    assert alignment_review["status"] == "failed_alignment_binding_disabled"
    assert alignment_review["access_seed_comparison"]["absolute_station_delta_m"] > 3800.0


def test_named_rapid_review_runs_cover_flow_lines_controls_and_safety_policy():
    markers = _load(EDITOR_MARKERS_RELATIVE_PATH)
    generated = build_simulator_review_runs(markers)
    committed = _load(SIMULATOR_RUNS_RELATIVE_PATH)
    assert generated == committed
    assert committed["run_count"] == len(committed["runs"])
    assert committed["run_count"] > 400
    assert {run["flow_band"] for run in committed["runs"]} == {
        "low_review",
        "reference_review",
        "high_review",
    }
    assert all(run["crew_weight_distribution_enabled"] for run in committed["runs"])
    assert all(run["swimmer_and_rescue_enabled"] for run in committed["runs"])
    assert all(len(run["platform_profiles"]) == 5 for run in committed["runs"])

    colorado = [
        run for run in committed["runs"]
        if run["river_id"] == "colorado_river_grand_canyon_rowing"
    ]
    assert all(run["control_mode"] == "manual_oar_rig" for run in colorado)
    assert all(run["voice_paddle_commands_enabled"] is False for run in colorado)

    commercial_suicide = [
        run for run in committed["runs"]
        if run["feature_id"].endswith("commercial_suicide")
    ]
    assert len(commercial_suicide) == 3
    assert {run["line_id"] for run in commercial_suicide} == {"mandatory_portage_control"}
    assert {run["expected_outcome"] for run in commercial_suicide} == {"portage"}
    assert all(
        run["execution_status"]
        == "blocked_until_exact_geometry_validated_cpp_window_and_guide_line"
        for run in committed["runs"]
    )


def test_unreal_rapid_editor_exposes_named_markers_and_review_run_queue():
    header = EDITOR_SHELL_HEADER.read_text(encoding="utf-8")
    module = EDITOR_MODULE.read_text(encoding="utf-8")
    actions = VALIDATION_ACTIONS.read_text(encoding="utf-8")
    shell = json.loads(EDITOR_SHELL_MANIFEST.read_text(encoding="utf-8"))

    assert "NamedRapidEditorMarkersManifest" in header
    assert "NamedRapidSimulatorReviewRunsManifest" in header
    for relative_path in (
        EDITOR_MARKERS_RELATIVE_PATH,
        EDITOR_GEOMETRY_RELATIVE_PATH,
        SIMULATOR_RUNS_RELATIVE_PATH,
    ):
        assert relative_path in module
        assert relative_path in actions
        assert relative_path in shell["source_manifests"].values()
    assert shell["named_rapid_review"]["river_count"] == 5
    assert shell["named_rapid_review"]["marker_count"] == 80
    assert shell["named_rapid_review"]["candidate_geometry_count"] == 45
    assert "execution_evidence_pending" in shell["named_rapid_review"]["status"]
    assert "BuildNamedRapidReviewPanel" in module
    assert "PROVISIONAL STATION" in module
    assert "All flow bands" in module
    assert "All station authority" in module
    assert "All geometry status" in module
    assert "Candidate map projection" in module
    assert "Map geometry unavailable" in module
    assert "All guide status" in module
    assert "All execution status" in module
    assert EDITOR_BROWSER_CAPTURE.is_file()
    capture = Image.open(EDITOR_BROWSER_CAPTURE).convert("RGB")
    assert capture.width >= 1600
    assert capture.height >= 900
    top = capture.crop((0, 0, capture.width, min(360, capture.height)))
    assert sum(1 for pixel in top.get_flattened_data() if max(pixel) > 45) > 10000
