"""Identify inferred tree roots inside the preserved context water mask.

Only positive water-mask cells nominate removals; unknown/outside cells are
reported, not silently clamped or interpreted as water. Source data is read-only.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'physics/data/real_world/south_fork_american_chili_bar/reconstruction_2026_09/full_reach'


def sample_mask(mask, xy, origin, cell):
    xy = np.asarray(xy)
    cols = np.rint((xy[:, 0] - origin[0]) / cell).astype(int)
    rows = np.rint((origin[1] - xy[:, 1]) / cell).astype(int)
    inside = (rows >= 0) & (rows < mask.shape[0]) & (cols >= 0) & (cols < mask.shape[1])
    values = np.full(len(xy), 255, dtype=np.uint8)
    values[inside] = mask[rows[inside], cols[inside]]
    return values


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    path = BASE / 'naip_canopy_20260926/placement.json'
    mask_path = BASE / 'source_context_extension/unknown_submerged_bed_mask.tif'
    context = json.loads((mask_path.parent / 'manifest.json').read_text())
    data = json.loads(path.read_text())
    Image.MAX_IMAGE_PIXELS = None
    with Image.open(mask_path) as image:
        mask = np.asarray(image)
    assert list(mask.shape) == context['grid']['shape']
    assert hashlib.sha256(mask_path.read_bytes()).hexdigest() == context['artifacts'][mask_path.name]
    rows = data['instances']
    xy = np.array([[r['world_root_cm'][0] / 100 + 689237,
                    4293073 - r['world_root_cm'][1] / 100] for r in rows])
    values = sample_mask(mask, xy, context['grid']['first_vertex_utm_m'], context['grid']['cell_m'])
    report = dict(schema='raftsim.canopy_channel_audit.v1',
                  placement=path.relative_to(ROOT).as_posix(),
                  placement_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                  mask=mask_path.relative_to(ROOT).as_posix(),
                  mask_sha256=hashlib.sha256(mask_path.read_bytes()).hexdigest(),
                  total=len(rows), wet_count=int((values == 1).sum()),
                  unknown_count=int((values == 255).sum()),
                  wet_instances=[r for r, v in zip(rows, values) if v == 1],
                  source_data_modified=False, clearance_2m_validated=False)
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: v for k, v in report.items() if k != 'wet_instances'}))


if __name__ == '__main__':
    main()
