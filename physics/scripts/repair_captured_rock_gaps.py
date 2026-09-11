"""Conservative candidate-only interpolation of tiny enclosed LiDAR gaps.

No extension of rock outlines, no filling channels/open cracks, no editing
captured returns or dry ground. Every filled cell has separate inferred authority.
"""
from pathlib import Path
import argparse
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tmp/south-fork-geospatial-deps'))
import numpy as np
from scipy.ndimage import binary_fill_holes, binary_dilation, label


def repair_gaps(bed, authority, cell_m, max_area_m2=1.0, max_rim_relief_m=1.0):
    if bed.shape != authority.shape or bed.ndim != 2 or not np.isfinite(bed).all():
        raise ValueError('Finite two-dimensional bed and matching authority are required')
    if not np.isfinite(cell_m) or cell_m <= 0:
        raise ValueError('Cell size must be positive and finite')
    if not np.isfinite(max_area_m2) or max_area_m2 <= 0 or not np.isfinite(max_rim_relief_m) or max_rim_relief_m < 0:
        raise ValueError('Interpolation limits must be finite and non-negative (area positive)')
    rock = authority == 3
    # Eight-connected exterior: a diagonal water connection is still open.
    structure = np.ones((3, 3), dtype=bool)
    holes = binary_fill_holes(rock, structure=structure) & ~rock
    ids, count = label(holes, structure=structure)
    result = bed.copy()
    provenance = authority.copy()
    filled = 0
    for index in range(1, count + 1):
        gap = ids == index
        if gap.sum() * cell_m**2 > max_area_m2 or not np.all(authority[gap] == 2):
            continue
        rim = binary_dilation(gap, structure=structure) & ~gap
        if not np.all(rock[rim]) or np.ptp(bed[rim]) > max_rim_relief_m:
            continue
        rim_y, rim_x = np.where(rim)
        heights = bed[rim]
        for y, x in zip(*np.where(gap)):
            weights = 1.0 / ((rim_y - y)**2 + (rim_x - x)**2)
            result[y, x] = np.sum(weights * heights) / weights.sum()
        provenance[gap] = 4  # inferred interpolation, never captured rock
        filled += int(gap.sum())
    return result, provenance, {'enclosed_gap_cells': int(holes.sum()),
                               'filled_cells': filled, 'filled_area_m2': filled * cell_m**2}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=ROOT / 'physics/data/real_world/south_fork_american_chili_bar/reconstruction_2026_09/troublemaker/geometry_candidate')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    import rasterio
    manifest = json.loads((args.source / 'manifest.json').read_text())
    bed_path = ROOT / manifest['shared_geometry_path']
    if hashlib.sha256(bed_path.read_bytes()).hexdigest() != manifest['shared_geometry_sha256']:
        raise ValueError('Source geometry hash differs from its manifest')
    with rasterio.open(bed_path) as source:
        bed, profile = source.read(1), source.profile.copy()
    with rasterio.open(args.source / 'geometry_authority.tif') as source:
        authority = source.read(1)
    repaired, new_authority, stats = repair_gaps(bed, authority, manifest['cell_m'])
    measured = np.isin(authority, [1, 3])
    if not np.array_equal(repaired[measured], bed[measured]):
        raise ValueError('Measured geometry changed')
    args.output.mkdir(parents=True, exist_ok=False)
    target = args.output / bed_path.name
    with rasterio.open(target, 'w', **profile) as output:
        output.write(repaired, 1)
        output.set_band_unit(1, 'metre')
        output.update_tags(vertical_datum='NAVD88', bathymetry='INFERRED_NOT_SURVEYED')
    with rasterio.open(args.output / 'geometry_authority.tif', 'w', **dict(profile, dtype='uint8', nodata=0)) as output:
        output.write(new_authority, 1)
    with np.load(args.source / 'engine_mesh_source.npz') as source:
        packed = {key: source[key] for key in source.files}
    packed['z_m'] = repaired - manifest['vertical_origin_navd88_m']
    packed['authority'] = new_authority
    np.savez_compressed(args.output / 'engine_mesh_source.npz', **packed)
    manifest.update({'status': 'gap_interpolation_candidate_not_cooked_or_engine_integrated',
        'parent_geometry_sha256': manifest['shared_geometry_sha256'],
        'shared_geometry_path': target.resolve().relative_to(ROOT).as_posix(),
        'shared_geometry_sha256': hashlib.sha256(target.read_bytes()).hexdigest(),
        'small_gap_interpolation': dict(stats, max_area_m2=1.0, max_rim_relief_m=1.0,
            authority_code=4, measured_values_unchanged=True),
        'hydraulic_validation_passed': False, 'game_integrated': False, 'production_promoted': False})
    (args.output / 'manifest.json').write_text(json.dumps(manifest, indent=2))
    print(json.dumps(manifest['small_gap_interpolation'], indent=2))


if __name__ == '__main__':
    main()
