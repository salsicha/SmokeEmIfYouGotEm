"""Request metadata validation, not visual acceptance tests."""
import runpy
import pytest
from pathlib import Path

PARSE = runpy.run_path(str(Path(__file__).resolve().parents[1] / 'scripts/audit_water_capture_series.py'))['parse_requests']


def line(index, time, frame, valid=1):
    return (f'capture-series request: index={index} world_s={time} frame={frame} '
        f'raft_river_valid={valid} raft_station_m=8369.934 raft_lateral_m=-0.262 '
        'camera_valid=1 camera_world_cm=V(X=-492279.13, Y=-24415.23, Z=20201.81)\n')


def test_capture_requests_preserve_actual_positions_and_timing():
    rows = PARSE(line(0, 10.038, 271) + line(1, 10.252, 275))
    assert rows[0]['raft_station_m'] == 8369.934
    assert rows[0]['camera_world_cm'] == [-492279.13, -24415.23, 20201.81]
    assert rows[1]['world_s'] == 10.252


def test_capture_requests_reject_missing_duplicate_and_nonadvancing_frames():
    for suffix in [line(2, 11, 275), line(0, 11, 275), line(1, 10, 275),
                   line(1, 11, 271), line(1, 11, 275, valid=0)]:
        try:
            PARSE(line(0, 10, 271) + suffix)
        except ValueError:
            continue
        raise AssertionError('Invalid capture metadata accepted')


def declared(index, time, frame):
    return line(index, time, frame).rstrip() + (
        ' camera_pitch_deg=-8.04 camera_yaw_deg=121.56 camera_roll_deg=0.0'
        ' camera_fov_deg=90.0 raft_coordinates=scenario_downstream\n')


def test_declared_downstream_camera_metadata_preserved():
    rows = PARSE(declared(0, 10, 271) + declared(1, 11, 275))
    assert rows[0]['raft_coordinate_frame'] == 'scenario_downstream'
    assert rows[0]['camera_rotation_pitch_yaw_roll_deg'] == [-8.04, 121.56, 0.0]
    assert rows[0]['camera_fov_deg'] == 90.0


@pytest.mark.parametrize('corruption', [
    lambda s: s.replace('camera_fov_deg=90.0', 'camera_fov_deg=0.0'),
    lambda s: s.replace('camera_fov_deg=90.0', 'camera_fov_deg=180.0'),
    lambda s: s.replace('camera_yaw_deg=121.56', 'camera_yaw_deg=nan'),
    lambda s: s.replace('scenario_downstream', 'cartesian_east_north'),
    lambda s: s.replace(' camera_roll_deg=0.0', ''),
    lambda s: line(1, 11, 275),
])
def test_declared_camera_metadata_fails_closed(corruption):
    with pytest.raises(ValueError):
        PARSE(declared(0, 10, 271) + corruption(declared(1, 11, 275)))
