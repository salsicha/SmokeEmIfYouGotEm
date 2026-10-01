"""October leaf state for the Zambezi upper-gorge evidence canopy (numpy only).

    apply_zambezi_october_leaf_state.py [--ndvi-evergreen 0.5] [--ndvi-dry-leaves 0.33]

The canopy (build_zambezi_evidence_dressing.py) places trees inside the May
2025 Sentinel-2 woodland cover, the end of the rains, when the whole gorge is
green. L_ZambeziUpperGorge is the October low-water gorge (283 m3/s image
day), late in the dry season, when the mopane, Combretum and Commiphora
woodland stands leafless or holds a few dry leaves and only the riverine and
spray-fed trees stay green.

Each tree's leaf state is measured, not assumed: the mean NDVI of the two
October Sentinel-2 scenes (2024-10-08 and 2025-10-03, 10 m) at the tree:

* NDVI >= --ndvi-evergreen: green crown (form 0, the existing broadleaf form);
* --ndvi-dry-leaves <= NDVI < --ndvi-evergreen: a few dry leaves (form 3);
* NDVI < --ndvi-dry-leaves: leafless (form 2).

Understory shrubs keep their green form (kind 0) where NDVI >= --ndvi-evergreen
and are leafless thorn scrub (kind 1) elsewhere. Positions, sizes and counts
are unchanged; only the form and kind columns and the placement metadata are
rewritten, so the script can be re-run. Species stay inferred.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
GORGE = ROOT / 'physics/data/real_world/zambezi_batoka_gorge'
S2 = GORGE / 'zambezi_sources_2026_09/sentinel2'
CANOPY = GORGE / 'terrain/upper_gorge_evidence_2025/upper_gorge_evidence_2025_canopy_placement.json'
OCTOBER = ('S2A_T35KLA_20241008T083054_L2A.npz', 'S2C_T35KLA_20251003T082652_L2A.npz')
FORM_GREEN, FORM_BARE, FORM_DRY_LEAVES = 0, 2, 3


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def october_ndvi(east, north):
    """Mean October NDVI (two scenes) at UTM 35S points, nearest 10 m pixel."""
    fm = json.loads((S2 / 'fetch_manifest.json').read_text(encoding='utf-8'))
    values = []
    for name in OCTOBER:
        item = next(i for i in fm['items'] if i['npz'] == name)
        assert sha(S2 / name) == item['npz_sha256'], name
        w = item['window_utm_m']; z = np.load(S2 / name)
        red, nir = [z[k].astype(np.float32) * 1e-4 - 0.1 for k in ('red', 'nir')]
        ndvi = (nir - red) / np.maximum(nir + red, 1e-3)
        c = np.clip(((east - w['xmin']) / 10.0).astype(int), 0, ndvi.shape[1] - 1)
        r = np.clip(((w['ymax'] - north) / 10.0).astype(int), 0, ndvi.shape[0] - 1)
        values.append(ndvi[r, c])
    return np.mean(values, axis=0)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--canopy', type=Path, default=CANOPY)
    ap.add_argument('--ndvi-evergreen', type=float, default=0.5)
    ap.add_argument('--ndvi-dry-leaves', type=float, default=0.33)
    args = ap.parse_args()
    placement = json.loads(args.canopy.read_text(encoding='utf-8'))
    frame = placement['frame']
    west_e = float(frame['x_cm'].split('E - ')[1].split(')')[0])
    centre_n = float(frame['y_cm'].split('N - ')[1].split(')')[0])

    trees = np.array([row[:2] for row in placement['instances']], float)
    tree_ndvi = october_ndvi(west_e + trees[:, 0] / 100.0, centre_n - trees[:, 1] / 100.0)
    form = np.where(tree_ndvi >= args.ndvi_evergreen, FORM_GREEN,
                    np.where(tree_ndvi >= args.ndvi_dry_leaves, FORM_DRY_LEAVES, FORM_BARE))
    for row, f in zip(placement['instances'], form):
        row[5] = int(f)
    shrubs = np.array([row[:2] for row in placement['understory']], float)
    shrub_ndvi = october_ndvi(west_e + shrubs[:, 0] / 100.0, centre_n - shrubs[:, 1] / 100.0)
    kind = (shrub_ndvi < args.ndvi_evergreen).astype(int)
    placement['understory'] = [row[:5] + [int(k)] for row, k in zip(placement['understory'], kind)]

    placement['forms'] = {
        '0': 'green broadleaf crown: riverine and spray-fed trees that stay green in October (species INFERRED)',
        '2': 'leafless dry-season tree (October NDVI below %.2f; species INFERRED)' % args.ndvi_dry_leaves,
        '3': 'dry-season tree holding a few dry leaves (October NDVI %.2f-%.2f; species INFERRED)'
             % (args.ndvi_dry_leaves, args.ndvi_evergreen)}
    placement['understory_fields'] = ['x_cm', 'y_cm', 'height_m', 'width_m', 'yaw_deg', 'kind']
    placement['understory_kinds'] = {'0': 'green shrub (October NDVI >= %.2f)' % args.ndvi_evergreen,
                                     '1': 'leafless thorn scrub'}
    placement['october_leaf_state'] = dict(
        generator='physics/scripts/apply_zambezi_october_leaf_state.py',
        method='mean NDVI of two October Sentinel-2 L2A scenes at each position (nearest 10 m pixel)',
        scenes=list(OCTOBER), scene_sha256=[sha(S2 / n) for n in OCTOBER],
        ndvi_evergreen=args.ndvi_evergreen, ndvi_dry_leaves=args.ndvi_dry_leaves,
        trees=dict(green=int((form == FORM_GREEN).sum()), dry_leaves=int((form == FORM_DRY_LEAVES).sum()),
                   leafless=int((form == FORM_BARE).sum())),
        understory=dict(green=int((kind == 0).sum()), leafless=int((kind == 1).sum())),
        tree_ndvi_p10_p50_p90=[round(float(v), 3) for v in np.percentile(tree_ndvi, [10, 50, 90])],
        note='leaf state measured per 10 m pixel; species, branching and the dry-leaf colour are inferred')
    tmp = args.canopy.with_suffix('.json.tmp')
    tmp.write_text(json.dumps(placement, separators=(',', ':')) + '\n', encoding='utf-8')
    os.replace(tmp, args.canopy)
    print(json.dumps(placement['october_leaf_state'], indent=1))


if __name__ == '__main__':
    main()
