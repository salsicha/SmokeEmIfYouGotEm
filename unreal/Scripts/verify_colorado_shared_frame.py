"""Exercise the full-river coordinate map through the production native adapter.

RAFTSIM_SHARED_FRAME selects the construction directory; RAFTSIM_FRAME_REPORT
selects a fresh tmp receipt. This is not a boat descent or rendering test.
"""
import hashlib
import json
import math
import os
from pathlib import Path
import time

import unreal

ROOT = Path(__file__).resolve().parents[2]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    directory = (ROOT/os.environ['RAFTSIM_SHARED_FRAME']).resolve()
    report_path = (ROOT/os.environ['RAFTSIM_FRAME_REPORT']).resolve()
    directory.relative_to(ROOT)
    report_path.relative_to(ROOT/'tmp')
    assert not report_path.exists(), 'Fresh report required'
    manifest = json.loads((directory/'manifest.json').read_text())
    assert manifest['schema'] == 'raftsim.colorado_shared_hydraulic_frame.v1'
    for name, digest in manifest['files_sha256'].items():
        assert sha(directory/name) == digest, 'Shared frame changed'
    mapping = json.loads((directory/'coordinate_map.json').read_text())
    adapter = unreal.RaftSimWaterRuntimeAdapter()
    assert adapter.configure_river_coordinate_map(str(directory/'coordinate_map.json'))
    points = mapping['points']
    sample = points[::100]+[points[-1]]
    # Densely exercise the two adjoining source domains as well as the whole
    # river at 200 m intervals; never extrapolate at the endpoints.
    stations = {p[0] for p in sample}
    stations.update(p[0] for p in points if 850 <= p[0] <= 1550)
    maximum = 0.; worst = None; probes = 0
    start = time.perf_counter()
    for station in sorted(stations):
        for lateral in (-3., 0., 3.):
            world = adapter.river_to_world_position(unreal.Vector2D(station, lateral), 925.)
            assert world is not None and all(math.isfinite(v) for v in (world.x, world.y, world.z))
            returned = adapter.world_to_river_coordinates(world)
            assert returned is not None
            coordinate, tangent, normal = returned
            assert all(math.isfinite(v) for vector in (tangent, normal) for v in (vector.x, vector.y, vector.z))
            error = math.hypot(coordinate.x-station, coordinate.y-lateral)
            assert math.isfinite(error)
            if error > maximum:
                maximum, worst = error, [station, lateral]
            probes += 1
    result = dict(schema='raftsim.colorado_shared_native_frame_review.v1', passed=maximum < .1,
        manifest_sha256=sha(directory/'manifest.json'),
        coordinate_map_sha256=sha(directory/'coordinate_map.json'),
        probes=probes, point_count=len(points), station_range_m=[points[0][0], points[-1][0]],
        maximum_roundtrip_error_m=maximum, worst_station_lateral_m=worst,
        query_seconds=time.perf_counter()-start,
        full_hull_descent=False, connected_water_validated=False, rendered_fps=None)
    report_path.write_text(json.dumps(result, indent=2)+'\n')
    unreal.log('Shared native frame report: '+str(report_path))
    assert result['passed'], 'Native full-river coordinate projection failed'


if __name__ == '__main__':
    try:
        main()
    finally:
        unreal.SystemLibrary.quit_editor()
