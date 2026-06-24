"""Plotting helpers for non-graphical simulation diagnostics."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Sequence

from .math2d import Vec2
from .math3d import Quaternion, Vec3
from .river2d import GeneratedRiver2D
from .telemetry import TelemetryFrame


def _pyplot():
    if "MPLCONFIGDIR" not in os.environ:
        cache_dir = Path(tempfile.gettempdir()) / "raftsim-matplotlib"
        cache_dir.mkdir(parents=True, exist_ok=True)
        os.environ["MPLCONFIGDIR"] = str(cache_dir)
    if "XDG_CACHE_HOME" not in os.environ:
        xdg_cache_dir = Path(tempfile.gettempdir()) / "raftsim-cache"
        xdg_cache_dir.mkdir(parents=True, exist_ok=True)
        os.environ["XDG_CACHE_HOME"] = str(xdg_cache_dir)

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


def plot_river2d(
    river: GeneratedRiver2D,
    *,
    output_path: str | Path | None = None,
    title: str = "Generated 2D river",
):
    """Plot river banks, centerline, and generated features."""

    plt = _pyplot()
    fig, ax = plt.subplots()
    left = river.left_bank_points
    right = river.right_bank_points
    center = tuple(section.center for section in river.cross_sections)

    ax.plot([p.x for p in left], [p.y for p in left], color="black", linewidth=1.0, label="left bank")
    ax.plot([p.x for p in right], [p.y for p in right], color="black", linewidth=1.0, label="right bank")
    ax.plot([p.x for p in center], [p.y for p in center], color="steelblue", linestyle="--", linewidth=0.8, label="centerline")

    colors = {
        "rock": "dimgray",
        "eddy": "teal",
        "standing_wave": "royalblue",
        "wave_train": "navy",
        "hole": "purple",
        "lateral_wave": "deepskyblue",
        "boil": "orange",
        "hypoviscous": "gold",
        "shallow": "sandybrown",
        "strainer": "crimson",
    }
    for feature in river.features:
        circle = plt.Circle(
            (feature.position.x, feature.position.y),
            feature.radius,
            color=colors.get(feature.kind, "gray"),
            alpha=0.28,
        )
        ax.add_patch(circle)
        ax.text(feature.position.x, feature.position.y, feature.kind[:2], fontsize=6, ha="center", va="center")

    ax.set_title(title)
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.set_aspect("equal", adjustable="box")
    ax.legend(loc="upper right", fontsize=7)
    return _save_or_return(fig, output_path)


def plot_river2d_flow(
    river: GeneratedRiver2D,
    *,
    output_path: str | Path | None = None,
    title: str = "2D river flow",
    stride: int = 8,
):
    """Plot sampled flow vectors across the generated river."""

    plt = _pyplot()
    fig, ax = plt.subplots()
    xs: list[float] = []
    ys: list[float] = []
    us: list[float] = []
    vs: list[float] = []
    for section in river.cross_sections[:: max(1, stride)]:
        for lateral_fraction in (-0.35, 0.0, 0.35):
            position = section.center + section.normal * (section.width * lateral_fraction)
            sample = river.sample(position)
            xs.append(position.x)
            ys.append(position.y)
            us.append(sample.current.x)
            vs.append(sample.current.y)

    ax.quiver(xs, ys, us, vs, angles="xy", scale_units="xy", scale=1.0, width=0.0025)
    ax.plot([p.x for p in river.left_bank_points], [p.y for p in river.left_bank_points], color="black", linewidth=0.8)
    ax.plot([p.x for p in river.right_bank_points], [p.y for p in river.right_bank_points], color="black", linewidth=0.8)
    ax.set_title(title)
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.set_aspect("equal", adjustable="box")
    return _save_or_return(fig, output_path)


def plot_trajectory2d(
    positions: Sequence[Vec2],
    *,
    river: GeneratedRiver2D | None = None,
    output_path: str | Path | None = None,
    title: str = "2D raft trajectory",
):
    """Plot a top-down raft trajectory, optionally over a river."""

    if not positions:
        raise ValueError("positions must not be empty.")

    plt = _pyplot()
    fig, ax = plt.subplots()
    if river is not None:
        ax.plot([p.x for p in river.left_bank_points], [p.y for p in river.left_bank_points], color="black", linewidth=0.8)
        ax.plot([p.x for p in river.right_bank_points], [p.y for p in river.right_bank_points], color="black", linewidth=0.8)
    ax.plot([p.x for p in positions], [p.y for p in positions], color="firebrick", linewidth=1.5)
    ax.scatter([positions[0].x], [positions[0].y], color="green", s=18, label="start")
    ax.scatter([positions[-1].x], [positions[-1].y], color="red", s=18, label="end")
    ax.set_title(title)
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.set_aspect("equal", adjustable="box")
    ax.legend(fontsize=7)
    return _save_or_return(fig, output_path)
