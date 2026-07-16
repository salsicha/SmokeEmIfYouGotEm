import json
from pathlib import Path

from raftsim.flexible_raft_d6 import (
    D6_BEHAVIORAL_SUITE_RELATIVE_PATH,
    D6_BEHAVIORAL_SUITE_SCHEMA,
    REQUIRED_D6_FIXTURE_IDS,
    build_d6_replay_channel_probe,
    build_flexible_raft_d6_behavioral_suite,
)


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_flexible_raft_d6_suite_is_reproducible_and_not_promoted():
    generated = build_flexible_raft_d6_behavioral_suite()
    committed = json.loads(
        (REPO_ROOT / D6_BEHAVIORAL_SUITE_RELATIVE_PATH).read_text(encoding="utf-8")
    )

    assert generated == committed
    assert committed["schema"] == D6_BEHAVIORAL_SUITE_SCHEMA
    assert committed["d6_complete"] is False
    assert committed["promotion_gate"]["may_mark_d6_complete"] is False
    assert committed["production_promoted"] is False


def test_flexible_raft_d6_suite_covers_all_required_behavioral_fixtures():
    suite = build_flexible_raft_d6_behavioral_suite()
    fixture_ids = [fixture["fixture_id"] for fixture in suite["fixtures"]]

    assert fixture_ids == list(REQUIRED_D6_FIXTURE_IDS)
    assert suite["fixture_count"] == 7
    assert set(suite["required_fixture_ids"]) == set(REQUIRED_D6_FIXTURE_IDS)


def test_flexible_raft_d6_requires_compliant_reference_and_chaos_baseline():
    suite = build_flexible_raft_d6_behavioral_suite()

    assert suite["reference_requirements"]["compliant_reference"]["status"] == "missing_measured_reference_results"
    assert suite["reference_requirements"]["chaos_rigid_baseline"]["status"] == "missing_measured_unreal_chaos_results"
    for fixture in suite["fixtures"]:
        targets = {target["target_id"]: target for target in fixture["comparison_targets"]}
        assert targets["project_chrono_or_reviewed_compliant_model"]["required"] is True
        assert targets["project_chrono_or_reviewed_compliant_model"]["status"] == "pending_measured_reference"
        assert targets["unreal_chaos_rigid_baseline"]["required"] is True
        assert targets["unreal_chaos_rigid_baseline"]["status"] == "pending_measured_chaos_baseline"
        assert fixture["can_promote"] is False


def test_flexible_raft_d6_suite_records_current_python_metrics():
    suite = build_flexible_raft_d6_behavioral_suite()
    by_id = {fixture["fixture_id"]: fixture for fixture in suite["fixtures"]}

    assert by_id["static_seat_load_sag"]["python_reference_metrics"]["max_seat_freeboard_loss_m"] > 0.0
    assert by_id["rock_pinch_wrap"]["python_reference_metrics"]["wrapping_contact_count"] >= 3
    assert by_id["upstream_tube_overwash_flip"]["python_reference_metrics"]["total_overtopping_flux_m3_s"] > 0.0
    assert by_id["post_contact_recovery"]["python_reference_metrics"]["recovering_contact_count"] > 0
    assert by_id["pressure_flow_sweeps"]["python_reference_metrics"]["sweep_case_count"] == 9


def test_flexible_raft_d6_replay_probe_exposes_d5_hashes():
    probe = build_d6_replay_channel_probe()

    assert probe["frame_count"] == 2
    assert len(probe["frame_hashes"]) == 2
    assert len(probe["replay_sha256"]) == 64
