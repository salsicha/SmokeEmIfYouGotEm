import hashlib
import json
from pathlib import Path

import numpy as np

from raftsim.south_fork_full_hydraulics import (
    FLOW_BAND_IDS,
    FULL_HYDRAULICS_MANIFEST_RELATIVE_PATH,
    build_south_fork_full_hydraulics_manifest,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def _load(relative_path: str) -> dict:
    return json.loads((REPO_ROOT / relative_path).read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_full_hydraulic_matrix_and_hash_locks_are_accepted():
    manifest = build_south_fork_full_hydraulics_manifest(REPO_ROOT)

    assert manifest == _load(FULL_HYDRAULICS_MANIFEST_RELATIVE_PATH)
    assert manifest["schema"] == "raftsim.south_fork.full_hydraulics.v1"
    assert manifest["status"] == "all_named_rapid_hydraulics_cooked_and_validated"
    assert manifest["matrix"] == {
        "all_combinations_passed": True,
        "catalog_subfeature_count": 105,
        "combination_count": 60,
        "flow_band_count": 3,
        "flows_cfs": [900.0, 1600.0, 3000.0],
        "passed_combination_count": 60,
        "rapid_count": 20,
    }
    assert all(manifest["acceptance"].values())
    assert manifest["authority"]["not_for_navigation"] is True


def test_all_named_rapid_fields_are_finite_hash_locked_and_feature_complete():
    root = _load(FULL_HYDRAULICS_MANIFEST_RELATIVE_PATH)
    feature_count = 0
    combination_count = 0
    for rapid_entry in root["rapids"]:
        rapid = _load(rapid_entry["cooked_fields_manifest"])
        assert rapid["schema"] == "raftsim.cooked_flow_fields.v1"
        assert rapid["all_bands_passed"] is True
        assert rapid["authority"]["not_surveyed"] is True
        assert rapid["authority"]["not_for_navigation"] is True
        assert [band["band_id"] for band in rapid["bands"]] == list(FLOW_BAND_IDS)
        feature_count += rapid_entry["catalog_feature_count"]
        for band in rapid["bands"]:
            combination_count += 1
            assert band["validation"]["passed"] is True
            assert all(band["validation"]["checks"].values())
            assert (
                len(band["validation"]["feature_envelopes"])
                == rapid_entry["catalog_feature_count"]
            )
            assert all(
                envelope["passed"]
                for envelope in band["validation"]["feature_envelopes"]
            )
            for name, record in band["arrays"].items():
                path = (
                    REPO_ROOT
                    / Path(rapid_entry["cooked_fields_manifest"]).parent
                    / record["file"]
                )
                assert _sha256(path) == record["sha256"]
                array = np.load(path, allow_pickle=False)
                assert list(array.shape) == record["shape"] == [21, 101]
                assert np.isfinite(array).all()
                if name == "h":
                    assert float(np.min(array)) >= 0.0
    assert combination_count == 60
    assert feature_count == 105


def test_every_rapid_has_guide_lines_hazards_checkpoints_and_rescue():
    root = _load(FULL_HYDRAULICS_MANIFEST_RELATIVE_PATH)
    for entry in root["rapids"]:
        rapid = _load(entry["cooked_fields_manifest"])
        gameplay = rapid["gameplay_binding"]
        assert (
            gameplay["entry_checkpoint_station_m"]
            < gameplay["exit_checkpoint_station_m"]
        )
        assert len(gameplay["preferred_lines"]) == 3
        assert {line["flow_band"] for line in gameplay["preferred_lines"]} == set(
            FLOW_BAND_IDS
        )
        assert gameplay["scout_eddy"]["station_m"] >= rapid["station_range_m"][0]
        assert (
            gameplay["rescue_zone"]["station_range_m"][1] <= rapid["station_range_m"][1]
        )
        assert gameplay["outcome_envelope"]["requires_finite_live_water"] is True
        assert (
            gameplay["outcome_envelope"]["requires_every_catalog_subfeature_signal"]
            is True
        )


def test_full_reach_streaming_coverage_has_no_gaps_and_uses_transit_seed():
    root = _load(FULL_HYDRAULICS_MANIFEST_RELATIVE_PATH)
    streaming = _load(root["moving_window_streaming"]["manifest"])

    assert streaming["status"] == "full_reach_moving_water_streaming_ready"
    assert streaming["rapid_window_count"] == 20
    assert streaming["coverage"]["continuous"] is True
    assert streaming["coverage"]["no_station_gaps"] is True
    assert streaming["handoff_contract"]["overlap_state_transferred"] is True
    assert streaming["handoff_contract"]["raft_and_gameplay_state_reset"] is False
    cursor = 0.0
    for segment in streaming["coverage_segments"]:
        start, end = segment["station_range_m"]
        assert start <= cursor + 0.001
        assert end >= start
        cursor = max(cursor, end)
        if segment["segment_kind"] == "procedural_transit_live_window":
            assert (
                segment["cooked_fields_manifest"]
                == streaming["full_reach_transit_seed"]["cooked_fields_manifest"]
            )
    assert np.isclose(cursor, streaming["coverage"]["reach_end_m"], atol=0.001)


def test_full_reach_transit_seed_is_finite_continuous_and_explicitly_procedural():
    root = _load(FULL_HYDRAULICS_MANIFEST_RELATIVE_PATH)
    streaming = _load(root["moving_window_streaming"]["manifest"])
    transit_record = streaming["full_reach_transit_seed"]
    transit = _load(transit_record["cooked_fields_manifest"])

    assert (
        _sha256(REPO_ROOT / transit_record["cooked_fields_manifest"])
        == transit_record["sha256"]
    )
    assert (
        transit["status"] == "procedural_transit_seed_ready_for_genuine_runtime_solver"
    )
    assert transit["grid"]["nx"] == 12271
    assert transit["grid"]["ny"] == 21
    assert np.isclose(transit["station_range_m"][1], 49077.732, atol=0.001)
    assert transit["all_bands_passed"] is True
    assert transit["authority"]["seed_kind"] == "procedural_transit_initial_condition"
    assert transit["authority"]["genuine_solver_begins_at_runtime"] is True
    assert transit["authority"]["not_solver_cooked_named_rapid_evidence"] is True
    assert transit["authority"]["not_for_navigation"] is True
    for band in transit["bands"]:
        assert band["validation"]["passed"] is True
        assert all(band["validation"]["checks"].values())
        for record in band["arrays"].values():
            path = (
                REPO_ROOT
                / Path(transit_record["cooked_fields_manifest"]).parent
                / record["file"]
            )
            assert _sha256(path) == record["sha256"]
            array = np.load(path, allow_pickle=False)
            assert list(array.shape) == record["shape"] == [21, 12271]
            assert np.isfinite(array).all()
