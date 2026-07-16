"""Classify solver evidence without conflating fixture calibration with parity."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Literal

SolverParityMode = Literal["solver", "reference_playback"]


@dataclass(frozen=True, slots=True)
class SolverParityClassification:
    """Audit result derived from one C++ run manifest."""

    mode: SolverParityMode
    evidence: tuple[str, ...]


def classify_solver_parity(manifest: Mapping[str, object]) -> SolverParityClassification:
    """Return whether a C++ run is base-solver evidence or fixture playback evidence."""

    if manifest.get("disable_fixture_calibrations") is True:
        return SolverParityClassification(
            mode="solver",
            evidence=("fixture_calibrations_disabled",),
        )

    fixture_flags = sorted(
        key
        for key, value in manifest.items()
        if key.startswith("fixture_scoped_") and value is True
    )
    if not any(key.startswith("fixture_scoped_") for key in manifest):
        raise ValueError(
            "C++ manifest does not expose fixture-scoped audit flags; parity mode cannot be classified."
        )

    active_profiles = sorted(_active_reference_profiles(manifest))
    active_behaviors = tuple(dict.fromkeys((*fixture_flags, *active_profiles)))
    if active_behaviors:
        return SolverParityClassification(
            mode="reference_playback",
            evidence=active_behaviors,
        )
    return SolverParityClassification(
        mode="solver",
        evidence=("no_active_fixture_scoped_behavior",),
    )


def _active_reference_profiles(manifest: Mapping[str, object]) -> tuple[str, ...]:
    active: list[str] = []
    for key, value in manifest.items():
        if not isinstance(value, Mapping) or value.get("enabled") is not True:
            continue
        normalized_key = key.lower()
        if "geoclaw_profile" in normalized_key or "reference_profile" in normalized_key:
            active.append(f"{key}.enabled")
    return tuple(active)
