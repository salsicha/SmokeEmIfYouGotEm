"""Validate and record South Fork World Partition HLOD build evidence."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

BUILD_MANIFEST_RELATIVE_PATH = (
    "unreal/Content/RaftSim/Environment/SouthForkFullReach/"
    "full_reach_environment_build_manifest.json"
)
HLOD_EVIDENCE_RELATIVE_PATH = (
    "docs/environment-captures/south_fork_full_reach/hlod_build_evidence.json"
)
EXTERNAL_ACTOR_DIRECTORY_RELATIVE_PATH = (
    "unreal/Content/__ExternalActors__/RaftSim/Maps/L_SouthForkAmerican_FullReach"
)
MAP_PACKAGE = "/Game/RaftSim/Maps/L_SouthForkAmerican_FullReach"

_WORLD_COUNT_PATTERN = re.compile(r"World contains (\d+) HLOD actors")
_BUILT_COUNT_PATTERN = re.compile(r"Built (\d+) HLOD actors")
_SAVED_ACTOR_PATTERN = re.compile(r"HLOD Actor .+ was modified, saving")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _artifact(repo_root: Path, path: Path) -> dict[str, Any]:
    return {
        "path": str(path.relative_to(repo_root)),
        "sha256": _sha256(path),
        "byte_count": path.stat().st_size,
    }


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def parse_hlod_build_log(text: str) -> dict[str, int | bool]:
    """Parse acceptance signals from an Unreal HLOD builder commandlet log."""

    world_counts = [int(value) for value in _WORLD_COUNT_PATTERN.findall(text)]
    built_counts = [int(value) for value in _BUILT_COUNT_PATTERN.findall(text)]
    if not world_counts or not built_counts:
        raise ValueError("HLOD log does not contain world and built actor totals")

    world_count = world_counts[-1]
    built_count = built_counts[-1]
    if world_count <= 0 or built_count != world_count:
        raise ValueError(
            f"HLOD actor totals are incomplete: world={world_count}, built={built_count}"
        )
    if "invalid HLOD layer" in text:
        raise ValueError("HLOD log contains invalid layer assignments")
    if "Fatal error" in text or "LogInit: Error:" in text:
        raise ValueError("HLOD log contains a fatal or commandlet error")
    if "Success - 0 error(s)" not in text:
        raise ValueError("HLOD commandlet did not report zero-error success")
    if "WorldPartitionHLODsBuilder" not in text or MAP_PACKAGE not in text:
        raise ValueError("HLOD log does not identify the expected builder and map")

    return {
        "world_actor_count": world_count,
        "built_actor_count": built_count,
        "modified_and_saved_actor_count": len(_SAVED_ACTOR_PATTERN.findall(text)),
        "zero_error_success": True,
        "invalid_layer_assignments": False,
    }


def collect_hlod_actor_packages(repo_root: Path) -> list[dict[str, Any]]:
    """Return hashed external actor packages that contain built HLOD actors."""

    actor_root = repo_root / EXTERNAL_ACTOR_DIRECTORY_RELATIVE_PATH
    packages: list[dict[str, Any]] = []
    for path in sorted(actor_root.rglob("*.uasset")):
        payload = path.read_bytes()
        if b"WorldPartitionHLOD" not in payload:
            continue
        if b"HLODLayer_Instanced/" not in payload:
            continue
        packages.append(_artifact(repo_root, path))
    return packages


def finalize_south_fork_hlod_manifest(
    repo_root: Path, commandlet_log: Path
) -> dict[str, Any]:
    """Validate HLOD output, write durable evidence, and finalize the build manifest."""

    repo_root = repo_root.resolve()
    commandlet_log = commandlet_log.resolve()
    log_metrics = parse_hlod_build_log(commandlet_log.read_text(encoding="utf-8"))
    actor_packages = collect_hlod_actor_packages(repo_root)
    expected_count = int(log_metrics["world_actor_count"])
    if len(actor_packages) != expected_count:
        raise ValueError(
            "HLOD package count does not match commandlet evidence: "
            f"packages={len(actor_packages)}, expected={expected_count}"
        )

    evidence = {
        "schema": "raftsim.unreal.south_fork_hlod_evidence.v1",
        "generated_on": "2026-07-19",
        "map": MAP_PACKAGE,
        "strategy": (
            "terminal_instancing_with_nanite_source_geometry_and_no_merged_atlas_parent"
        ),
        "commandlet_log": {
            "filename": commandlet_log.name,
            "sha256": _sha256(commandlet_log),
            "byte_count": commandlet_log.stat().st_size,
        },
        "commandlet_result": log_metrics,
        "actor_packages": actor_packages,
        "acceptance": {
            "positive_actor_count": True,
            "every_actor_built": True,
            "every_actor_package_present_and_hashed": True,
            "invalid_layer_assignments_absent": True,
            "merged_atlas_parent_absent": "8192x8192"
            not in commandlet_log.read_text(encoding="utf-8"),
            "zero_error_success": True,
        },
    }
    if not all(evidence["acceptance"].values()):
        raise ValueError("HLOD acceptance evidence contains a failed gate")

    evidence_path = repo_root / HLOD_EVIDENCE_RELATIVE_PATH
    _write_json(evidence_path, evidence)

    manifest_path = repo_root / BUILD_MANIFEST_RELATIVE_PATH
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["hlod_generation_complete"] = True
    manifest["hlod_status"] = "built_and_validated_terminal_instancing"
    manifest["hlod_actor_count"] = expected_count
    manifest["hlod_evidence"] = _artifact(repo_root, evidence_path)
    _write_json(manifest_path, manifest)
    return evidence


def validate_south_fork_hlod_evidence(repo_root: Path) -> dict[str, Any]:
    """Validate checked-in evidence against every current HLOD actor package."""

    repo_root = repo_root.resolve()
    manifest = json.loads(
        (repo_root / BUILD_MANIFEST_RELATIVE_PATH).read_text(encoding="utf-8")
    )
    evidence_artifact = manifest["hlod_evidence"]
    evidence_path = repo_root / evidence_artifact["path"]
    if _sha256(evidence_path) != evidence_artifact["sha256"]:
        raise ValueError("HLOD evidence hash does not match the build manifest")
    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    current_packages = collect_hlod_actor_packages(repo_root)
    expected_packages = evidence["actor_packages"]
    if current_packages != expected_packages:
        raise ValueError("current HLOD actor packages do not match checked-in evidence")
    if len(current_packages) != manifest["hlod_actor_count"]:
        raise ValueError("HLOD actor count does not match the build manifest")
    if not manifest["hlod_generation_complete"]:
        raise ValueError("build manifest has not accepted HLOD generation")
    if not all(evidence["acceptance"].values()):
        raise ValueError("checked-in HLOD evidence contains a failed gate")
    return evidence
