from __future__ import annotations

import json
import re
import subprocess
from collections import Counter
from pathlib import Path
from typing import Any, Iterator


REVIEW_DIRECTORY = Path(
    "docs/environment-captures/photoreal_river_previews/landscape_candidates"
)
REVIEW_PATTERN = re.compile(
    r"futaleufu_cordillera_cypress_v(?P<major>\d+)"
    r"(?:_(?P<minor>\d+))?_(?P<change>.+)_review\.json$"
)


def _walk_scalars(value: Any, path: tuple[str, ...] = ()) -> Iterator[tuple[tuple[str, ...], Any]]:
    if isinstance(value, dict):
        for key, child in value.items():
            yield from _walk_scalars(child, (*path, str(key)))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from _walk_scalars(child, (*path, str(index)))
    else:
        yield path, value


def _version_parts(path: Path) -> tuple[int, int | None, str]:
    match = REVIEW_PATTERN.fullmatch(path.name)
    if match is None:
        raise ValueError(f"Not a Futaleufu cypress review path: {path}")
    minor = match.group("minor")
    return int(match.group("major")), int(minor) if minor is not None else None, match.group("change")


def _version_label(major: int, minor: int | None) -> str:
    return f"v{major}.{minor}" if minor is not None else f"v{major}"


def _version_sort_key(path: Path) -> tuple[int, int]:
    major, minor, _ = _version_parts(path)
    return major, -1 if minor is None else minor


def discover_review_paths(repo_root: Path) -> list[Path]:
    review_root = repo_root / REVIEW_DIRECTORY
    return sorted(
        (path for path in review_root.glob("futaleufu_cordillera_cypress_v*_review.json") if REVIEW_PATTERN.fullmatch(path.name)),
        key=_version_sort_key,
    )


def _first_scalar(payload: dict[str, Any], key: str) -> Any | None:
    for path, value in _walk_scalars(payload):
        if path and path[-1] == key:
            return value
    return None


def _git_date(repo_root: Path, path: Path) -> str:
    relative = path.relative_to(repo_root)
    result = subprocess.run(
        ["git", "log", "-1", "--format=%cI", "--", relative.as_posix()],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()[:10] or "unknown"


def _review_date(repo_root: Path, path: Path, payload: dict[str, Any]) -> str:
    generated = _first_scalar(payload, "generated_on")
    if isinstance(generated, str) and generated:
        return generated[:10]
    return _git_date(repo_root, path)


def _gate_class(major: int) -> str:
    if major <= 24:
        return "morphology_visibility"
    if major <= 33:
        return "hlod_projection_transition"
    if major <= 35:
        return "temporal_handoff"
    return "lit_shape_material_shadow"


def _failed_gates(payload: dict[str, Any]) -> list[str]:
    failed: list[str] = []
    for path, value in _walk_scalars(payload):
        if value is not False or not path:
            continue
        key = path[-1]
        if key.endswith("_gate_passed") or key.endswith("_contract_passed"):
            failed.append(key)
    return sorted(set(failed))


def _metric_candidates(payload: dict[str, Any], light: str, metric_kind: str) -> list[tuple[int, float]]:
    candidates: list[tuple[int, float]] = []
    for path, value in _walk_scalars(payload):
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not path:
            continue
        key = path[-1].lower()
        lowered_path = ".".join(path).lower()
        if light not in lowered_path:
            continue
        if metric_kind == "silhouette":
            if "silhouette" not in key or "intersection_over_union" not in key:
                continue
        elif metric_kind == "luminance":
            if key not in {"candidate_to_source_luminance_ratio", "hlod_to_source_luminance_ratio"}:
                continue
        else:
            raise ValueError(f"Unknown metric kind: {metric_kind}")

        score = 0
        for preferred in ("merged_geometry_hlod", "candidate", "combined", "hlod"):
            if preferred in lowered_path:
                score += 4
        for control in ("flat_hlod_control", "control", "threshold", "delta"):
            if control in lowered_path:
                score -= 8
        candidates.append((score, float(value)))
    return candidates


def _preferred_metric(payload: dict[str, Any], light: str, metric_kind: str) -> float | None:
    candidates = _metric_candidates(payload, light, metric_kind)
    if not candidates:
        return None
    best_score = max(score for score, _ in candidates)
    values = [value for score, value in candidates if score == best_score]
    if metric_kind == "silhouette":
        return max(values)
    return min(values, key=lambda value: abs(1.0 - value))


def _peak_green_fraction(payload: dict[str, Any]) -> float | None:
    values = []
    for path, value in _walk_scalars(payload):
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not path:
            continue
        if path[-1] not in {"green_dominant_fraction", "mean_green_dominant_fraction"}:
            continue
        values.append(float(value))
    return max(values) if values else None


def build_review_row(repo_root: Path, path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    major, minor, change = _version_parts(path)
    failed_gates = _failed_gates(payload)
    status = payload.get("status")
    if not isinstance(status, str):
        status = str(_first_scalar(payload, "status") or "unknown")
    production_promoted = any(
        value is True for scalar_path, value in _walk_scalars(payload) if scalar_path and scalar_path[-1] == "production_promoted"
    )
    comparable_shape_metrics = major <= 42
    return {
        "version": _version_label(major, minor),
        "major": major,
        "minor": minor,
        "date": _review_date(repo_root, path, payload),
        "change": change.replace("_", " "),
        "gate_class": _gate_class(major),
        "status": status,
        "failed_gate_count": len(failed_gates),
        "failed_gates": failed_gates,
        "production_promoted": production_promoted,
        "metrics": {
            "peak_green_fraction": _peak_green_fraction(payload),
            "frontlit_silhouette_iou": (
                _preferred_metric(payload, "frontlit", "silhouette") if comparable_shape_metrics else None
            ),
            "backlit_silhouette_iou": (
                _preferred_metric(payload, "backlit", "silhouette") if comparable_shape_metrics else None
            ),
            "frontlit_luminance_ratio": (
                _preferred_metric(payload, "frontlit", "luminance") if comparable_shape_metrics else None
            ),
            "backlit_luminance_ratio": (
                _preferred_metric(payload, "backlit", "luminance") if comparable_shape_metrics else None
            ),
        },
        "source": path.relative_to(repo_root).as_posix(),
    }


def _late_backlit_analysis(rows: list[dict[str, Any]]) -> dict[str, Any]:
    points = [
        {"version": row["version"], "value": row["metrics"]["backlit_silhouette_iou"]}
        for row in rows
        if 36 <= row["major"] <= 42 and row["minor"] is None and row["metrics"]["backlit_silhouette_iou"] is not None
    ]
    if not points:
        return {"points": [], "latest": None, "gate": 0.9, "gap_to_gate": None, "trajectory": "unavailable"}
    latest = points[-1]["value"]
    values = [point["value"] for point in points]
    improvement = latest - values[0]
    return {
        "points": points,
        "latest": latest,
        "gate": 0.9,
        "gap_to_gate": 0.9 - latest,
        "net_improvement": improvement,
        "trajectory": "not_converged" if latest < 0.9 else "gate_reached",
    }


def build_canopy_review_report(repo_root: Path) -> dict[str, Any]:
    rows = [build_review_row(repo_root, path) for path in discover_review_paths(repo_root)]
    gate_class_counts = Counter(row["gate_class"] for row in rows)
    return {
        "schema": "raftsim.futaleufu.canopy_review_history.v1",
        "review_count": len(rows),
        "production_promotion_count": sum(bool(row["production_promoted"]) for row in rows),
        "date_range": {
            "first": min((row["date"] for row in rows), default=None),
            "last": max((row["date"] for row in rows), default=None),
        },
        "iterations_per_gate_class": dict(sorted(gate_class_counts.items())),
        "late_backlit_silhouette": _late_backlit_analysis(rows),
        "rows": rows,
    }


def _format_metric(value: float | None) -> str:
    return "-" if value is None else f"{value:.3f}"


def render_canopy_review_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Futaleufu Canopy Review History",
        "",
        f"Locked reviews: **{report['review_count']}**. Production promotions: **{report['production_promotion_count']}**.",
        "",
        "| Version | Date | Change | Gate class | Green peak | Front IoU | Back IoU | Primary result |",
        "| --- | --- | --- | --- | ---: | ---: | ---: | --- |",
    ]
    for row in report["rows"]:
        metrics = row["metrics"]
        primary_result = (
            f"failed: {row['failed_gates'][0]}" if row["failed_gates"] else row["status"]
        )
        lines.append(
            "| {version} | {date} | {change} | {gate_class} | {green} | {front} | {back} | {result} |".format(
                version=row["version"],
                date=row["date"],
                change=row["change"],
                gate_class=row["gate_class"],
                green=_format_metric(metrics["peak_green_fraction"]),
                front=_format_metric(metrics["frontlit_silhouette_iou"]),
                back=_format_metric(metrics["backlit_silhouette_iou"]),
                result=primary_result.replace("_", " "),
            )
        )
    lines.append("")
    return "\n".join(lines)
