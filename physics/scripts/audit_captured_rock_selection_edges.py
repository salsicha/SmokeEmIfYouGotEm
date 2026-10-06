"""Check whether interpreted search regions truncate classified rock support.

Read-only with respect to geometry. Additional returns are candidates, not
permission to relabel inferred bed or extend a boulder automatically.
"""
from collections import deque
import hashlib
import json
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
MESH = ROOT / 'tmp/south-fork-rock-return-xy-candidate-v2-20260907/registered_mesh_source.npz'
POINTS = ROOT / 'physics/data/real_world/south_fork_american_chili_bar/reconstruction_2026_09/troublemaker/classified_lidar_returns.npz'


def connected_to_seed(available, seeds):
    """Four-connected support; diagonal contact alone does not fill a gap."""
    if available.shape != seeds.shape or available.ndim != 2:
        raise ValueError('Matching two-dimensional masks required')
    reached = np.asarray(seeds & available, dtype=bool).copy()
    queue = deque(map(tuple, np.argwhere(reached)))
    rows, cols = available.shape
    while queue:
        row, col = queue.popleft()
        for rr, cc in ((row-1, col), (row+1, col), (row, col-1), (row, col+1)):
            if 0 <= rr < rows and 0 <= cc < cols and available[rr, cc] and not reached[rr, cc]:
                reached[rr, cc] = True
                queue.append((rr, cc))
    return reached


def polygon_distance(x, y, polygon):
    """Euclidean distance to interpreted region edges, not a rock boundary."""
    best = np.full(np.broadcast(x, y).shape, np.inf)
    polygon = np.asarray(polygon, dtype=float)
    for a, b in zip(polygon, np.roll(polygon, -1, axis=0)):
        edge = b-a
        t = np.clip(((x-a[0])*edge[0]+(y-a[1])*edge[1])/np.dot(edge, edge), 0, 1)
        best = np.minimum(best, np.hypot(x-a[0]-t*edge[0], y-a[1]-t*edge[1]))
    return best


def cliff_audit(mesh, regions):
    """Attribute steep connecting faces without modifying any source vertex."""
    xyz = np.column_stack([mesh[k].ravel() for k in ('east_m', 'north_m', 'z_m')])
    faces = mesh['triangles']
    p = xyz[faces]
    cross = np.cross(p[:, 1]-p[:, 0], p[:, 2]-p[:, 0])
    area = np.linalg.norm(cross, axis=1)/2
    steep = np.abs(cross[:, 2]) < np.linalg.norm(cross, axis=1)*.5
    authority = mesh['authority'].ravel()[faces]
    transition = np.any(authority == 3, axis=1) & np.any(authority == 2, axis=1)
    selected = steep & transition
    center = p[selected].mean(axis=1)
    distance = np.full(len(center), np.inf)
    for region in regions:
        distance = np.minimum(distance, polygon_distance(center[:, 0], center[:, 1], region['polygon']))
    selected_area = area[selected]
    return {'steeper_than_60_degrees_rock_to_inferred_bed_faces': int(selected.sum()),
            'steep_connecting_face_area_m2': float(selected_area.sum()),
            'within_075m_of_search_region_edge_faces': int((distance <= .75).sum()),
            'within_075m_of_search_region_edge_area_m2': float(selected_area[distance <= .75].sum()),
            'distance_to_search_region_edge_quantiles_m': np.quantile(distance, [0,.5,.95,1]).tolist() if len(distance) else [],
            'interpretation': 'Connecting faces are inferred; proximity alone does not prove clipping or justify adding unclassified returns.'}


def main():
    with np.load(MESH) as source:
        mesh = {key: source[key] for key in source.files}
    manifest = json.loads(MESH.with_name('manifest.json').read_text())
    digest = hashlib.sha256(MESH.read_bytes()).hexdigest()
    assert digest == manifest['mesh_sha256']
    with np.load(POINTS) as source:
        points = {key: source[key] for key in source.files}
    assert hashlib.sha256(POINTS.read_bytes()).hexdigest() == manifest['original_returns_sha256']
    origin = manifest['origin_utm_m']
    east = points['utm_easting_m']-origin[0]
    north = points['utm_northing_m']-origin[1]
    cols = np.floor((east-mesh['nominal_east_axis_m'][0]+.25)/.5).astype(int)
    rows = np.floor((mesh['nominal_north_axis_m'][0]+.25-north)/.5).astype(int)
    shape = mesh['authority'].shape
    inside = (rows >= 0) & (cols >= 0) & (rows < shape[0]) & (cols < shape[1])
    eligible = inside & points['within_survey_water']
    eligible &= (points['height_above_flattened_surface_m'] > .3) & (points['height_above_flattened_surface_m'] < 8)
    # Outside the interpreted search regions use only classified ground and
    # ignored-ground, never unclassified canopy returns.
    eligible &= np.isin(points['classification'], (2, 20))
    indices = np.flatnonzero(eligible)
    cells = rows[indices]*shape[1]+cols[indices]
    counts = np.bincount(cells, minlength=np.prod(shape)).reshape(shape)
    minimum = np.full(shape, np.inf)
    np.minimum.at(minimum, (rows[indices], cols[indices]), points['navd88_m'][indices]-manifest['vertical_origin_navd88_m'])
    measured_rock = mesh['authority'] == 3
    inferred = np.isin(mesh['authority'], (2, 4))
    supported = counts >= 2
    connected = connected_to_seed((supported & inferred) | measured_rock, measured_rock)
    additions = connected & inferred & supported
    rr, cc = np.where(additions)
    delta = minimum[additions]-mesh['z_m'][additions]
    record = {'schema': 'raftsim.captured_rock_selection_edge_audit.v1',
              'source_mesh_sha256': digest,
              'classified_ground_candidate_points': int(eligible.sum()),
              'classified_supported_cells_outside_current_rock': int((supported & inferred).sum()),
              'connected_additional_cells': int(additions.sum()),
              'connected_additional_area_m2': float(additions.sum()*.25),
              'additional_cell_height_delta_quantiles_m': np.quantile(delta, [0,.5,.95,1]).tolist() if len(delta) else [],
              'additional_cells': [{'row': int(r), 'col': int(c),
                  'local_east_north_m': [float(mesh['east_m'][r,c]),float(mesh['north_m'][r,c])],
                  'ground_return_count': int(counts[r,c]),
                  'candidate_minimum_ground_height_m': float(minimum[r,c]),
                  'existing_inferred_height_m': float(mesh['z_m'][r,c])} for r,c in zip(rr,cc)],
              'geometry_modified': False, 'additional_returns_accepted_as_rock': False}
    regions = json.loads(POINTS.with_name('rock_review_regions.json').read_text())['regions']
    record['steep_face_attribution'] = cliff_audit(mesh, regions)
    chosen_classes, class_counts = np.unique(points['classification'][mesh['rock_source_return_index']], return_counts=True)
    record['existing_selected_rock_return_classification_counts'] = {str(int(k)): int(v) for k,v in zip(chosen_classes, class_counts)}
    output = ROOT / 'docs/reconstruction-review-2026-09-07/captured-rock-selection-edge-audit.json'
    output.write_text(json.dumps(record, indent=2)+'\n')
    print(json.dumps({key:value for key,value in record.items() if key != 'additional_cells'}, indent=2))


if __name__ == '__main__':
    main()
