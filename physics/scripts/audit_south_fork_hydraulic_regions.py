"""Verify exact shared cells across all Cartesian hydraulic-region overlaps."""
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT/'physics/data/real_world/south_fork_american_chili_bar/reconstruction_2026_09/full_reach'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    from scipy.spatial import cKDTree
    folder = BASE/'hydraulic_regions_context'
    manifest = json.loads((folder/'manifest.json').read_text())
    assert manifest['completed']
    assert manifest['source_geometry_sha256'] == sha(BASE/'source_context_extension/manifest.json')
    assert manifest['base_geometry_sha256'] == sha(BASE/'composite_terrain/manifest.json')
    assert manifest['coordinate_map_sha256'] == sha(BASE/'playable_route/coordinate_map.json')
    assert manifest['minimum_complete_window_margin_m'] >= 112
    assert manifest['original_water_domain_probe_count'] == 406823
    records = manifest['regions']
    fields = ['bed_navd88_m','captured_surface_navd88_m','captured_water_mask','terrain_owner']
    @lru_cache(maxsize=96)
    def arrays(index):
        path = ROOT/records[index]['geometry_file']
        assert sha(path) == records[index]['geometry_sha256']
        with np.load(path, allow_pickle=False) as data:
            values = {name:data[name] for name in fields}
        assert all(list(value.shape) == records[index]['shape'] for value in values.values())
        assert all(np.isfinite(values[name]).all() for name in fields)
        return values
    for index in range(len(records)):
        arrays(index)
    centers = np.asarray([r['center_utm_m'] for r in records])
    pairs = sorted(cKDTree(centers).query_pairs(320, p=np.inf))
    overlap_cells = 0
    for count, (a,b) in enumerate(pairs):
        ra, rb = records[a], records[b]
        ba, bb = np.asarray(ra['bounds_utm_m']), np.asarray(rb['bounds_utm_m'])
        lower, upper = np.maximum(ba[:2],bb[:2]), np.minimum(ba[2:],bb[2:])
        assert (upper >= lower).all()
        start_a, end_a = (lower-ba[:2]).astype(int), (upper-ba[:2]).astype(int)+1
        start_b, end_b = (lower-bb[:2]).astype(int), (upper-bb[:2]).astype(int)+1
        aa, ab = arrays(a), arrays(b)
        for field in fields:
            av = aa[field][start_a[1]:end_a[1],start_a[0]:end_a[0]]
            bv = ab[field][start_b[1]:end_b[1],start_b[0]:end_b[0]]
            assert av.size and np.array_equal(av,bv), f'Shared source cells differ: {a}/{b} {field}'
        overlap_cells += av.size
        if count % 1000 == 0:
            print(f'Verified {count+1}/{len(pairs)} exact region overlaps',flush=True)
    report = dict(manifest_sha256=sha(folder/'manifest.json'), region_count=len(records),
        all_packet_hashes_verified=True, all_region_values_finite=True,
        overlapping_region_pair_count=len(pairs), shared_cell_comparison_count=overlap_cells,
        compared_fields=fields, shared_values_bit_identical=True,
        all_original_water_domain_has_complete_224m_windows=True,
        minimum_complete_source_margin_m=manifest['minimum_complete_window_margin_m'],
        hydraulic_state_solved=False, normal_map_integrated=False, full_reconstruction_accepted=False)
    output = folder/'overlap_audit.json'
    assert not output.exists(), 'Preserve existing audit evidence'
    output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2),flush=True)


if __name__ == '__main__':
    main()
