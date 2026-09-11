"""Request metadata validation, not visual acceptance tests."""
import runpy
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
