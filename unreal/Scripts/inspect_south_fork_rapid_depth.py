"""Read-only cooked-depth transects for diagnosing a native failed approach.

This is the actual source atlas, NOT a live-fluid substitute or acceptance run.
"""
import json
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
base = ROOT/'tmp/troublemaker-envelope-runtime450-v1-20260927/atlas'
manifest = json.loads((base/'manifest.json').read_text())
depth = np.load(base/manifest['arrays']['h']['file'], mmap_mode='r')
points = np.array(json.loads((ROOT/'physics/data/real_world/south_fork_american_chili_bar/reconstruction_2026_09/full_reach/playable_route/coordinate_map.json').read_text())['points'])
origins = np.array([tile['origin_m'] for tile in manifest['tiles']])


def probe(station, lateral):
    i = int(np.clip(np.searchsorted(points[:, 0], station)-1, 0, len(points)-2))
    t = (station-points[i, 0])/(points[i+1, 0]-points[i, 0])
    point = points[i]+t*(points[i+1]-points[i])
    xy = point[1:3]+lateral*point[3:5]/np.linalg.norm(point[3:5])
    relative = xy-origins
    hits = np.flatnonzero(np.all((relative >= 0) & (relative < 80), axis=1))
    if len(hits) != 1:
        return None
    tile = hits[0]
    col, row = np.floor(relative[tile]).astype(int)
    return float(depth[tile*80+row, col])


if __name__ == '__main__':
    laterals = list(range(-16, 17, 2))
    print('Cooked source depth (m), not live simulation; columns are signed lateral m')
    print('station '+' '.join(f'{x:5}' for x in laterals))
    for station in (8245, 8260, 8275, 8290, 8305, 8320, 8335, 8350, 8368, 8380, 8395, 8410, 8440, 8460, 8490):
        values = [probe(station, lateral) for lateral in laterals]
        print(f'{station:7} '+' '.join('  n/a' if v is None else f'{v:5.2f}' for v in values))
