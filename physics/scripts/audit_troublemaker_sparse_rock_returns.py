"""Account for measured returns discarded by the two-returns-per-cell gate.

This is source inspection, not automatic rock classification. Search polygons
are interpreted, class 1 is unclassified, and water-height returns are ambiguous.
"""
import json
from pathlib import Path
import numpy as np
from audit_captured_rock_selection_edges import connected_to_seed

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT/'tmp/south-fork-rock-return-xy-candidate-v2-20260907'
BASE = ROOT/'physics/data/real_world/south_fork_american_chili_bar/reconstruction_2026_09/troublemaker'


def inside_polygon(x, y, vertices):
    inside = np.zeros(np.broadcast(x, y).shape, bool)
    for a, b in zip(vertices, vertices[1:]+vertices[:1]):
        if a[1] != b[1]:
            inside ^= ((a[1] > y) != (b[1] > y)) & (x < (b[0]-a[0])*(y-a[1])/(b[1]-a[1])+a[0])
    return inside


def load_candidates(threshold=.3):
    manifest = json.loads((SOURCE/'manifest.json').read_text())
    with np.load(SOURCE/'registered_mesh_source.npz') as data:
        mesh = {key: data[key] for key in data.files}
    with np.load(BASE/'classified_lidar_returns.npz') as data:
        points = {key: data[key] for key in data.files}
    x = points['utm_easting_m']-manifest['origin_utm_m'][0]
    y = points['utm_northing_m']-manifest['origin_utm_m'][1]
    r = np.floor((mesh['nominal_north_axis_m'][0]+.25-y)/.5).astype(int)
    c = np.floor((x-mesh['nominal_east_axis_m'][0]+.25)/.5).astype(int)
    rows, cols = mesh['authority'].shape
    eligible = (r >= 0)&(r < rows)&(c >= 0)&(c < cols)
    eligible &= points['within_survey_water'] & np.isin(points['classification'], [1, 2, 20])
    eligible &= (points['height_above_flattened_surface_m'] > threshold)&(points['height_above_flattened_surface_m'] < 8)
    region = np.zeros(len(x), bool)
    for polygon in json.loads((BASE/'rock_review_regions.json').read_text())['regions']:
        region |= inside_polygon(x, y, polygon['polygon'])
    indices = np.flatnonzero(eligible & region)
    cells = r[indices]*cols+c[indices]
    counts = np.bincount(cells, minlength=rows*cols).reshape(rows, cols)
    order = np.lexsort((indices, points['navd88_m'][indices], cells))
    sorted_cells = cells[order]
    first = np.r_[True, sorted_cells[1:] != sorted_cells[:-1]]
    chosen = np.full(rows*cols, -1, dtype=np.int64)
    chosen[sorted_cells[first]] = indices[order[first]]
    chosen = chosen.reshape(rows, cols)
    rock = mesh['authority'] == 3
    connected = connected_to_seed((counts > 0) | rock, rock)
    additions = connected & (mesh['authority'] == 2) & (counts > 0)
    return manifest, mesh, points, chosen, counts, additions


def main():
    for threshold in (.3, .15, 0, -.1):
        manifest, mesh, points, chosen, counts, additions = load_candidates(threshold)
        north = (mesh['east_m'] > 3)&(mesh['east_m'] < 44)&(mesh['north_m'] > 0)&(mesh['north_m'] < 12)
        height = points['navd88_m'][chosen[additions]]-manifest['vertical_origin_navd88_m']
        print(json.dumps(dict(threshold_m=threshold, connected_cells=int(additions.sum()),
            single_return_cells=int((additions & (counts == 1)).sum()),
            north_bedrock_cells=int((additions & north).sum()),
            added_height_quantiles=np.quantile(height-mesh['z_m'][additions], [0,.5,.95,1]).tolist(),
            interpretation='Candidates only; no geometry modified or unclassified returns certified as rock.')))


if __name__ == '__main__':
    main()
