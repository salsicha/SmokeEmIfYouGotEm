"""Infer bank-canopy instances from retained LiDAR plus registered NAIP.

Canopy locations/heights are evidence-constrained approximations, NOT a surveyed
tree inventory. Species, crown form, orientation and trunk locations are inferred.
This does not edit terrain, rock returns, collision triangles or hydraulic fields.
"""
import hashlib
import json
from pathlib import Path
import numpy as np
from PIL import Image
from south_fork_registered_mesh import RegisteredMeshSampler

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT/'physics/data/real_world/south_fork_american_chili_bar/reconstruction_2026_09'
MESH = ROOT/'tmp/south-fork-rock-return-xy-candidate-v2-20260907/registered_mesh_source.npz'
OUT = BASE/'troublemaker/playable_canopy.json'


def image_pixels(east, north, bounds, shape):
    """North-up metric image registration; reject rather than clamp outside."""
    col = np.floor((east-bounds['xmin'])/(bounds['xmax']-bounds['xmin'])*shape[1]).astype(int)
    row = np.floor((bounds['ymax']-north)/(bounds['ymax']-bounds['ymin'])*shape[0]).astype(int)
    if np.any((col < 0) | (row < 0) | (col >= shape[1]) | (row >= shape[0])):
        raise ValueError('Canopy query outside source imagery')
    return row, col


def separated_peaks(xy, heights):
    """Deterministic crown-centre approximation, never random landscape scatter."""
    kept = []
    radii = np.clip(heights*.35, 3., 7.)
    for i in np.argsort(-heights, kind='stable'):
        if not kept or np.all(np.linalg.norm(xy[kept]-xy[i], axis=1) >= np.maximum(radii[kept], radii[i])):
            kept.append(int(i))
    return np.asarray(kept, dtype=int)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    manifest = json.loads(MESH.with_name('manifest.json').read_text())
    points_path = BASE/'troublemaker/classified_lidar_returns.npz'
    image_path = BASE/'sources/troublemaker_naip.png'
    image_meta = BASE/'sources/troublemaker_naip_export.json'
    assert sha(MESH) == manifest['mesh_sha256']
    assert sha(points_path) == manifest['original_returns_sha256']
    with np.load(MESH) as data:
        mesh = {k: data[k] for k in data.files}
    with np.load(points_path) as data:
        points = {k: data[k] for k in data.files}
    rgb = np.asarray(Image.open(image_path).convert('RGB'), dtype=float)
    bounds = json.loads(image_meta.read_text())['extent']
    assert bounds['spatialReference']['wkid'] == 32610
    origin = np.asarray(manifest['origin_utm_m'])
    east = points['utm_easting_m']-origin[0]
    north = points['utm_northing_m']-origin[1]
    height = points['height_above_flattened_surface_m']
    valid = (~points['within_survey_water']) & (points['classification'] == 1)
    valid &= np.isfinite(height) & (height >= 3.5) & (height <= 30)
    valid &= (abs(east) < 173) & (abs(north) < 133)
    ids = np.flatnonzero(valid)
    row, col = image_pixels(east[ids]+origin[0], north[ids]+origin[1], bounds, rgb.shape)
    color = rgb[row, col]
    # Positive visible-green evidence excludes most bare rock, roads and roofs.
    # A conservative filter, not a vegetation/species classifier certification.
    green = (color[:, 1] > color[:, 0]*1.04) & (color[:, 1] > color[:, 2]*1.10)
    ids = ids[green]
    tile_col = np.floor((east[ids]+180)/3).astype(int)
    tile_row = np.floor((north[ids]+140)/3).astype(int)
    cells = tile_row*120+tile_col
    order = np.argsort(cells, kind='stable')
    groups = np.split(order, np.flatnonzero(np.diff(cells[order]))+1)
    candidates = []
    for group in groups:
        if len(group) < 12:
            continue
        selected = ids[group]
        ex, ny = np.median(east[selected]), np.median(north[selected])
        canopy_height = float(np.quantile(height[selected], .90))
        candidates.append([ex, ny, canopy_height, len(selected)])
    candidates = np.asarray(candidates)
    assert len(candidates), 'No supported canopy, do not fabricate fallback scatter'
    rr = np.floor((mesh['nominal_north_axis_m'][0]+.25-candidates[:, 1])/.5).astype(int)
    cc = np.floor((candidates[:, 0]-mesh['nominal_east_axis_m'][0]+.25)/.5).astype(int)
    dry = np.ones(len(candidates), dtype=bool)
    # An inferred trunk must have a full two-metre dry-ground collar, not sit
    # on a rock island or inferred wet bed underneath an overhanging crown.
    for dr in range(-4, 5):
        for dc in range(-4, 5):
            dry &= mesh['authority'][rr+dr, cc+dc] == 1
    candidates = candidates[dry]
    keep = separated_peaks(candidates[:, :2], candidates[:, 2])
    selected = candidates[keep]
    sampler = RegisteredMeshSampler(mesh)
    ground, normals = sampler.sample(selected[:, 0], selected[:, 1], with_normals=True)
    instances = []
    for i, (data, z, normal) in enumerate(zip(selected, ground, normals)):
        ex, ny, h, count = data
        if normal[2] < .55:
            continue
        # The ordinary scene is reflected north -> -Unreal Y, not the old
        # review map's +Y convention. Z remains the same centimetre datum.
        instances.append({'id': i, 'location_cm': [float(ex*100), float(-ny*100), float(z*100)],
            'height_m': float(h), 'support_return_count': int(count),
            'yaw_degrees': float((int(round(ex*100))*17+int(round(ny*100))*31) % 360),
            'form_index': i % 3, 'ground_authority': 1})
    record = {'schema': 'raftsim.troublemaker.captured_canopy.v1',
        'normal_playable_level': '/Game/RaftSim/Maps/L_SouthFork_Troublemaker',
        'sources': {str(p.relative_to(ROOT)).replace('\\', '/'): sha(p) for p in (MESH, points_path, image_path, image_meta)},
        'source_geometry_sha256': manifest['mesh_sha256'],
        'source_crs': 'EPSG:32610; NAVD88 metres', 'world_y_sign': -1,
        'method': '3m tiles; at least12 non-water class1 returns at3.5..30m over ground and visibly green NAIP pixels;90th percentile height; deterministic separated peaks;2m dry collar;ground slope<56.7deg',
        'candidate_tile_count': int(len(candidates)), 'instance_count': len(instances),
        'tree_inventory_surveyed': False, 'species_and_trunk_positions_measured': False,
        'appearance': 'Project-authored interior live oak crown family; species and form inferred, not photoreal accepted',
        'collision': 'Visual canopy only outside wet bed; solid tree obstacles remain unverified',
        'source_dates_coincident': False, 'terrain_or_hydraulic_geometry_modified': False,
        'instances': instances}
    OUT.write_text(json.dumps(record, indent=2)+'\n')
    print(json.dumps({k:v for k,v in record.items() if k != 'instances'}, indent=2))


if __name__ == '__main__':
    main()
