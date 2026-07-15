from __future__ import annotations

import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
PORTFOLIO_PATH = REPO_ROOT / "physics/data/real_world/river_portfolio_plan.json"
FLEXIBLE_TUBE_PATH = (
    REPO_ROOT / "unreal/Content/RaftSim/Raft/flexible_raft_tube_validation_plan.json"
)


def test_active_river_portfolio_prioritizes_zambezi_and_futaleufu() -> None:
    plan = json.loads(PORTFOLIO_PATH.read_text(encoding="utf-8"))
    active = plan["active_rivers"]
    active_ids = [river["river_id"] for river in active]

    assert [river["order"] for river in active] == [1, 2, 3, 4, 5]
    assert active_ids == [
        "american_south_fork",
        "colorado_river_grand_canyon_rowing",
        "pacuare_river_costa_rica",
        "futaleufu_river_chile",
        "chilko_river_lava_canyon",
    ]
    assert "zambezi_batoka_gorge" not in active_ids
    chilko = active[-1]
    assert chilko["put_in"] == "Chilko River Lodge"
    assert chilko["take_out"] == "Chilko-Taseko Junction"
    assert plan["portfolio_rules"]["active_river_count"] == len(active)

    priority = plan["photoreal_priority_goal"]
    assert priority["priority_river_ids"] == [
        "zambezi_batoka_gorge",
        "futaleufu_river_chile",
    ]
    assert priority["no_photoreal_claim_before_all_gates_pass"] is True

    additional = {
        river["river_id"]: river
        for river in plan["additional_active_environment_targets"]
    }
    zambezi = additional["zambezi_batoka_gorge"]
    assert zambezi["environment_status"] == (
        "active_photoreal_production_source_blocked"
    )
    assert zambezi["runnable_status"].startswith("blocked_pending_")
    assert plan["backlog_rivers"] == []
    assert plan["portfolio_rules"]["active_environment_target_count"] == (
        len(active) + len(additional)
    )


def test_colorado_rowing_disables_voice_while_paddle_runs_enable_it() -> None:
    plan = json.loads(PORTFOLIO_PATH.read_text(encoding="utf-8"))
    for river in plan["active_rivers"]:
        if river["crew_mode"] == "oar_rig_rowing":
            assert river["voice_commands"] is False
        else:
            assert river["crew_mode"] == "guided_paddle_raft"
            assert river["voice_commands"] is True


def test_flexible_tube_contract_covers_load_overwash_contact_and_recovery() -> None:
    plan = json.loads(FLEXIBLE_TUBE_PATH.read_text(encoding="utf-8"))
    mechanics = set(plan["state"]["required_mechanics"])
    channels = set(plan["state"]["required_channels"])
    fixture_ids = {fixture["fixture_id"] for fixture in plan["fixtures"]}

    assert plan["authority"]["scoring_authority_allowed"] is False
    assert {
        "seat_and_high_side_load_depress_local_tube",
        "overwash_accumulation_drainage_and_weight_transfer",
        "rock_indentation_wrap_pinch_friction_and_release",
        "perimeter_segment_compression_and_shape_recovery",
    } <= mechanics
    assert {
        "tube_segment_compression",
        "tube_pressure",
        "local_freeboard",
        "entrained_water_mass",
        "overwash_flux_and_side",
        "rock_contact_patch",
        "water_and_contact_roll_moment",
    } <= channels
    assert {
        "static_seat_load_sag",
        "rock_pinch_and_wrap",
        "upstream_tube_overwash_flip",
        "timed_high_side_save",
        "post_contact_shape_recovery",
        "pressure_and_flow_sweep",
    } <= fixture_ids


def test_flexible_tube_scalability_preserves_gameplay_authority() -> None:
    plan = json.loads(FLEXIBLE_TUBE_PATH.read_text(encoding="utf-8"))
    fixed = set(plan["scalability"]["must_remain_identical"])
    scalable = set(plan["scalability"]["may_scale"])

    assert {
        "authoritative_tube_state",
        "local_freeboard",
        "overwash_water_mass",
        "crew_weight_transfer",
        "pin_release_flip_and_rescue_outcomes",
    } <= fixed
    assert fixed.isdisjoint(scalable)
