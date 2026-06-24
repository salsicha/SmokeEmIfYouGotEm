import pytest

from raftsim.math3d import Quaternion, Vec3
from raftsim.plotting import plot_force_magnitudes, plot_orientation_euler, plot_trajectory
from raftsim.telemetry import TelemetryRecorder


pytest.importorskip("matplotlib")


def test_plotting_helpers_create_output_files(tmp_path):
    recorder = TelemetryRecorder()
    recorder.begin_frame(step_index=0, time=0.0, dt=0.1)
    recorder.record_force("test", Vec3(1.0, 2.0, 3.0))
    recorder.end_frame()

    trajectory_path = tmp_path / "trajectory.png"
    forces_path = tmp_path / "forces.png"
    orientation_path = tmp_path / "orientation.png"

    plot_trajectory([Vec3(), Vec3(1.0, 2.0, 0.0)], output_path=trajectory_path)
    plot_force_magnitudes(recorder.frames, output_path=forces_path)
    plot_orientation_euler([Quaternion.identity()], output_path=orientation_path)

    assert trajectory_path.exists()
    assert forces_path.exists()
    assert orientation_path.exists()
