"""Generate Unreal live-water manifests from the current report-set lock."""

from __future__ import annotations

import copy
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True, slots=True)
class LiveWaterBridgeManifests:
    live_bridge: dict[str, Any]
    runtime_candidate: dict[str, Any]


def build_live_water_bridge_manifests(repo_root: Path) -> LiveWaterBridgeManifests:
    """Apply the current lock hash and approval state to Unreal bridge manifests."""

    root = repo_root.resolve()
    report_lock = _read_json(root / "physics/reports/milestone20/report_set_lock.json")
    live_bridge = copy.deepcopy(
        _read_json(root / "unreal/Content/RaftSim/Physics/live_water_bridge.json")
    )
    runtime_candidate = copy.deepcopy(
        _read_json(root / "unreal/Content/RaftSim/Physics/water_runtime_candidate.json")
    )
    lock_hash = str(report_lock["lock"]["lock_hash"])
    approved = bool(report_lock.get("passed")) and bool(
        report_lock.get("production_use", {}).get(
            "live_water_unreal_bridge_foundation_unblocked"
        )
    )

    live_bridge["status"] = (
        "authoritative_custom_cxx_water_path_integrated_text_first"
        if approved
        else "live_custom_water_blocked_frozen_playback_only"
    )
    live_bridge["accepted_report_set_lock"].update(
        {"lock_hash": lock_hash, "passed": approved}
    )
    live_bridge["water_runtime"].update(
        {
            "authority_status": "approved" if approved else "blocked",
            "live_stepping_enabled": approved,
        }
    )
    live_bridge["runtime_policy"].update(
        {
            "allowed_water_mode": (
                "live_custom_cxx_solver" if approved else "telemetry_and_frozen_playback_only"
            ),
            "blocked_lock_prevents_step_water": True,
        }
    )

    runtime_candidate["accepted_report_set_lock"].update(
        {"lock_hash": lock_hash, "passed": approved}
    )
    runtime_candidate["runtime_policy"].update(
        {
            "authority_status": "approved" if approved else "candidate_blocked",
            "live_stepping_enabled": approved,
            "allowed_water_mode": (
                "live_custom_cxx_solver" if approved else "telemetry_and_frozen_playback_only"
            ),
        }
    )
    runtime_candidate["status"] = (
        "authoritative_live_water_path_integrated_text_first_pending_editor_compile"
        if approved
        else "runtime_candidate_integrated_live_authority_blocked"
    )
    return LiveWaterBridgeManifests(
        live_bridge=live_bridge,
        runtime_candidate=runtime_candidate,
    )


def write_live_water_bridge_manifests(repo_root: Path) -> LiveWaterBridgeManifests:
    """Write both Unreal live-water manifests through their structured generator."""

    root = repo_root.resolve()
    generated = build_live_water_bridge_manifests(root)
    _write_json(
        root / "unreal/Content/RaftSim/Physics/live_water_bridge.json",
        generated.live_bridge,
    )
    _write_json(
        root / "unreal/Content/RaftSim/Physics/water_runtime_candidate.json",
        generated.runtime_candidate,
    )
    return generated


def _read_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object.")
    return data


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
