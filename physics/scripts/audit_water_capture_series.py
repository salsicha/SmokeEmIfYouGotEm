"""Audit captured-frame timing/positions; never a photorealism or FPS test."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

import numpy as np
from PIL import Image


REQUEST = re.compile(
    r'capture-series request: index=(\d+) world_s=([\d.]+) frame=(\d+) '
    r'raft_river_valid=(\d) raft_station_m=([-\d.]+) raft_lateral_m=([-\d.]+) '
    r'camera_valid=(\d) camera_world_cm=V\(X=([-\d.]+), Y=([-\d.]+), Z=([-\d.]+)\)'
)

CAMERA = re.compile(
    r' camera_pitch_deg=([-\d.]+) camera_yaw_deg=([-\d.]+) '
    r'camera_roll_deg=([-\d.]+) camera_fov_deg=([\d.]+) '
    r'raft_coordinates=(\w+)')


def parse_requests(log: str) -> list[dict]:
    rows = []
    for match in REQUEST.finditer(log):
        p = match.groups()
        rows.append(dict(index=int(p[0]), world_s=float(p[1]), frame=int(p[2]),
            raft_river_valid=bool(int(p[3])), raft_station_m=float(p[4]),
            raft_lateral_m=float(p[5]), camera_valid=bool(int(p[6])),
            camera_world_cm=list(map(float, p[7:10]))))
        tail = log[match.end():].split('\n', 1)[0].rstrip('\r')
        metadata = CAMERA.fullmatch(tail)
        if tail and not metadata:
            raise ValueError('Malformed camera or coordinate-frame metadata')
        if metadata:
            pitch, yaw, roll, fov = map(float, metadata.groups()[:4])
            if not np.isfinite([pitch, yaw, roll, fov]).all() or not 0 < fov < 180:
                raise ValueError('Invalid camera orientation or field of view')
            if metadata[5] != 'scenario_downstream':
                raise ValueError('Unknown declared raft coordinate frame')
            rows[-1].update(camera_rotation_pitch_yaw_roll_deg=[pitch, yaw, roll],
                camera_fov_deg=fov, raft_coordinate_frame=metadata[5])
    if len(rows) < 2:
        raise ValueError('Need at least two fully instrumented screenshot requests')
    if [r['index'] for r in rows] != list(range(len(rows))):
        raise ValueError('Duplicate, missing, or unordered request index')
    if not all(r['raft_river_valid'] and r['camera_valid'] for r in rows):
        raise ValueError('Invalid raft or camera coordinates')
    if len({r.get('raft_coordinate_frame') for r in rows}) != 1:
        raise ValueError('Mixed declared and legacy coordinate frames')
    for a, b in zip(rows, rows[1:]):
        if b['world_s'] <= a['world_s'] or b['frame'] <= a['frame']:
            raise ValueError('Requests must advance game time and render frame')
    return rows


def audit(log_path: Path, directory: Path, label: str, roi: list[int],
          coordinate_frame: str | None = None) -> dict:
    if coordinate_frame not in (None, 'river_station_lateral', 'cartesian_east_north', 'scenario_downstream'):
        raise ValueError('Supported coordinate frame required')
    rows = parse_requests(log_path.read_text())
    declared_frame = rows[0].get('raft_coordinate_frame')
    if declared_frame and coordinate_frame not in (None, declared_frame):
        raise ValueError('Requested interpretation contradicts the recorded coordinate frame')
    if coordinate_frame == 'scenario_downstream' and not declared_frame:
        raise ValueError('Legacy log does not prove scenario-downstream coordinates')
    coordinate_frame = declared_frame or coordinate_frame or 'river_station_lateral'
    files = [directory / f'{label}_{r["index"]:03d}.png' for r in rows]
    actual = set(directory.glob(f'{label}_[0-9][0-9][0-9].png'))
    if actual != set(files):
        raise ValueError('Captured files do not match requested indices')
    if len(roi) != 4 or min(roi) < 0 or roi[2] <= roi[0] or roi[3] <= roi[1]:
        raise ValueError('ROI must be x0 y0 x1 y1 with positive area')
    hashes, differences, previous, size = [], [], None, None
    for file in files:
        hashes.append(hashlib.sha256(file.read_bytes()).hexdigest())
        with Image.open(file) as img:
            if size is None:
                size = img.size
            if img.size != size or roi[2] > size[0] or roi[3] > size[1]:
                raise ValueError('Inconsistent image size or ROI outside image')
            rgb = np.asarray(img.convert('RGB'), dtype=np.float32)[roi[1]:roi[3], roi[0]:roi[2]]
        if previous is not None:
            diff = np.abs(rgb - previous)
            differences.append(dict(mean_absolute_rgb_255=float(diff.mean()),
                p99_max_channel_rgb_255=float(np.percentile(diff.max(axis=2), 99))))
        previous = rgb
    cameras = np.array([r['camera_world_cm'] for r in rows])
    times = np.array([r['world_s'] for r in rows])
    first_range = [min(r['raft_station_m'] for r in rows), max(r['raft_station_m'] for r in rows)]
    second_range = [min(r['raft_lateral_m'] for r in rows), max(r['raft_lateral_m'] for r in rows)]
    if coordinate_frame == 'cartesian_east_north':
        for row in rows:
            row['raft_east_m'] = row.pop('raft_station_m')
            row['raft_north_m'] = row.pop('raft_lateral_m')
    result = dict(scope='Actual sampled game frames; request-time metadata, not exact GPU exposure time',
        log=str(log_path.resolve()), directory=str(directory.resolve()), label=label,
        image_size=list(size), frame_count=len(files), unique_png_hashes=len(set(hashes)),
        elapsed_game_seconds=float(times[-1]-times[0]),
        request_interval_seconds_min_median_max=np.percentile(np.diff(times), [0, 50, 100]).tolist(),
        camera_max_displacement_cm=float(np.linalg.norm(cameras-cameras[0], axis=1).max()),
        raft_coordinate_frame=coordinate_frame,
        raft_coordinate_ranges_m=[first_range, second_range],
        roi_xyxy=roi, adjacent_frame_roi_differences=differences,
        requests=rows, png_sha256=hashes, photorealism_accepted=False,
        limitations='Image differences establish changed pixels only, not correct flow, splash trajectories, temporal stability, or playable FPS. Screenshot I/O perturbs frame cadence.')
    if coordinate_frame != 'scenario_downstream':
        result['hydraulic_coordinate_frame'] = coordinate_frame
        result['raft_hydraulic_coordinate_ranges_m'] = [first_range, second_range]
    else:
        rotations = np.array([r['camera_rotation_pitch_yaw_roll_deg'] for r in rows])
        result['camera_max_angle_change_deg'] = float(np.max(np.abs((rotations-rotations[0]+180) % 360-180)))
        result['camera_fov_range_deg'] = [min(r['camera_fov_deg'] for r in rows), max(r['camera_fov_deg'] for r in rows)]
    if coordinate_frame in ('river_station_lateral', 'scenario_downstream'):
        result['raft_station_range_m'] = first_range
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--log', type=Path, required=True)
    parser.add_argument('--directory', type=Path, required=True)
    parser.add_argument('--label', required=True)
    parser.add_argument('--roi', type=int, nargs=4, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--coordinate-frame', choices=('river_station_lateral', 'cartesian_east_north', 'scenario_downstream'),
        help='New logs declare their frame. For legacy logs only, specify actual hydraulic coordinates (default river station/lateral).')
    args = parser.parse_args()
    result = audit(args.log, args.directory, args.label, args.roi, args.coordinate_frame)
    with args.output.open('x') as output:
        json.dump(result, output, indent=2)
        output.write('\n')
    print(json.dumps({k: result[k] for k in ['label', 'frame_count', 'unique_png_hashes',
        'elapsed_game_seconds', 'request_interval_seconds_min_median_max',
        'camera_max_displacement_cm', 'raft_coordinate_frame', 'raft_coordinate_ranges_m', 'photorealism_accepted']}))


if __name__ == '__main__':
    main()
