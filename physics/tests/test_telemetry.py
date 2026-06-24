import csv

from raftsim.math3d import Vec3
from raftsim.telemetry import TelemetryRecorder


def test_telemetry_records_force_rows_and_net_force(tmp_path):
    recorder = TelemetryRecorder()
    frame = recorder.begin_frame(step_index=7, time=0.35, dt=0.05)
    recorder.record_force("buoyancy", Vec3(0.0, 0.0, 10.0), metadata={"sample": 1})
    recorder.record_force("drag", Vec3(-3.0, 0.0, 0.0), torque=Vec3(0.0, 0.0, 2.0))
    ended = recorder.end_frame()

    assert ended is frame
    assert frame.net_force == Vec3(-3.0, 0.0, 10.0)
    assert frame.net_torque == Vec3(0.0, 0.0, 2.0)

    output_path = recorder.write_force_csv(tmp_path / "forces.csv")
    with output_path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))

    assert len(rows) == 2
    assert rows[0]["name"] == "buoyancy"
    assert rows[0]["metadata"] == '{"sample": 1}'


def test_telemetry_enforces_frame_boundaries():
    recorder = TelemetryRecorder()

    try:
        recorder.record_force("bad", Vec3())
    except RuntimeError as error:
        assert "No active telemetry frame" in str(error)
    else:
        raise AssertionError("Expected force recording outside a frame to fail.")
