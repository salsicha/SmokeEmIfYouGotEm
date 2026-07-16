import copy
import json
from pathlib import Path

import pytest

from raftsim.flexible_raft_d5 import (
    D5_TELEMETRY_REPLAY_FIXTURE_RELATIVE_PATH,
    D5_TELEMETRY_REPLAY_SCHEMA,
    build_flexible_raft_d5_fixture,
    stable_json_sha256,
)


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_flexible_raft_d5_fixture_is_reproducible():
    generated = build_flexible_raft_d5_fixture()
    committed = json.loads(
        (REPO_ROOT / D5_TELEMETRY_REPLAY_FIXTURE_RELATIVE_PATH).read_text(encoding="utf-8")
    )

    assert generated == committed
    assert committed["schema"] == D5_TELEMETRY_REPLAY_SCHEMA
    assert committed["scoring_authority_enabled"] is False
    assert committed["frame_count"] == 2
    assert committed["replay_sha256"] == stable_json_sha256(committed)


def test_flexible_raft_d5_records_required_per_segment_channels():
    fixture = build_flexible_raft_d5_fixture()
    frame = fixture["frames"][0]
    segment = next(
        item
        for item in frame["segments"]
        if item["segment_id"].startswith("starboard_") and item["contact"]["active"]
    )

    assert segment["tube"]["pressure_pa"] > 0.0
    assert segment["tube"]["volume_m3"] > 0.0
    assert "freeboard_loss_m" in segment["tube"]
    assert "floor_load_n" in segment["tube"]
    assert "lacing_load_n" in segment["tube"]
    assert "overtopping_flux_m3_s" in segment["overwash"]
    assert "entrained_water_side" in segment["overwash"]
    assert "max_indentation_m" in segment["contact"]
    assert "min_release_margin_n" in segment["contact"]
    assert "contact_roll_moment_nm" in segment["contact"]
    assert "combined_roll_moment_nm" in segment


def test_flexible_raft_d5_frame_and_replay_hashes_are_stable_and_sensitive():
    fixture = build_flexible_raft_d5_fixture()

    for frame in fixture["frames"]:
        assert len(frame["frame_sha256"]) == 64
        assert frame["frame_sha256"] == stable_json_sha256(frame)
    assert fixture["frame_hashes"] == [frame["frame_sha256"] for frame in fixture["frames"]]
    assert len(fixture["replay_sha256"]) == 64

    mutated = copy.deepcopy(fixture)
    mutated["frames"][1]["time_s"] += 1.0 / 30.0
    assert stable_json_sha256(mutated) != fixture["replay_sha256"]


def test_flexible_raft_d5_replay_tracks_high_side_change():
    fixture = build_flexible_raft_d5_fixture()
    neutral, high_side = fixture["frames"]

    assert neutral["crew_summary"]["high_side_count"] == 0
    assert high_side["crew_summary"]["high_side_count"] > 0
    assert high_side["totals"]["contact_min_release_margin_n"] != pytest.approx(
        neutral["totals"]["contact_min_release_margin_n"]
    )
    assert high_side["totals"]["overwash_retained_water_mass_kg"] >= neutral["totals"]["overwash_retained_water_mass_kg"]
