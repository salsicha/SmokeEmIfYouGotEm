"""Plotting helpers for non-graphical simulation diagnostics."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Sequence

from .math3d import Quaternion, Vec3
from .telemetry import TelemetryFrame


def _pyplot():
    if "MPLCONFIGDIR" not in os.environ:
        cache_dir = Path(tempfile.gettempdir()) / "raftsim-matplotlib"
        cache_dir.mkdir(parents=True, exist_ok=True)
        os.environ["MPLCONFIGDIR"] = str(cache_dir)

    import matplotlib

    matplotlib.use("Agg", force=True)
    import matplotlib.pyplot as plt

    return plt


def _save_or_return(fig, output_path: str | Path | None):
    if output_path is not None:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(path, bbox_inches="tight")
    return fig


def plot_trajectory(
    positions: Sequence[Vec3],
    *,
    output_path: str | Path | None = None,
    title: str = "Raft trajectory",
):
    """Plot an XYZ trajectory and optionally save it to disk."""

    if not positions:
        raise ValueError("positions must not be empty.")

    plt = _pyplot()
    fig = plt.figure()
    ax = fig.add_subplot(111, projection="3d")
    ax.plot([p.x for p in positions], [p.y for p in positions], [p.z for p in positions])
    ax.set_title(title)
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.set_zlabel("z")
    return _save_or_return(fig, output_path)


def plot_force_magnitudes(
    frames: Sequence[TelemetryFrame],
    *,
    output_path: str | Path | None = None,
    title: str = "Net force magnitude",
):
    """Plot net force magnitude per telemetry frame."""

    plt = _pyplot()
    times = [frame.time for frame in frames]
    magnitudes = [frame.net_force.magnitude for frame in frames]

    fig, ax = plt.subplots()
    ax.plot(times, magnitudes)
    ax.set_title(title)
    ax.set_xlabel("time")
    ax.set_ylabel("|net force|")
    return _save_or_return(fig, output_path)


def plot_orientation_euler(
    orientations: Sequence[Quaternion],
    *,
    output_path: str | Path | None = None,
    title: str = "Orientation",
):
    """Plot roll, pitch, and yaw diagnostics from quaternions."""

    if not orientations:
        raise ValueError("orientations must not be empty.")

    plt = _pyplot()
    roll: list[float] = []
    pitch: list[float] = []
    yaw: list[float] = []
    for orientation in orientations:
        r, p, y = orientation.to_euler_radians()
        roll.append(r)
        pitch.append(p)
        yaw.append(y)

    fig, ax = plt.subplots()
    ax.plot(roll, label="roll")
    ax.plot(pitch, label="pitch")
    ax.plot(yaw, label="yaw")
    ax.set_title(title)
    ax.set_xlabel("sample")
    ax.set_ylabel("radians")
    ax.legend()
    return _save_or_return(fig, output_path)
