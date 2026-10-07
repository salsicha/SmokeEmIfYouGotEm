"""Assemble verified native LidarBC crops without resampling or gap invention.

The first finite source pixel owns each output cell. Later inputs fill only
missing cells. Overlap differences are reported, never averaged away. The
source-index array identifies the owning input (zero means still missing).
"""
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from capture_lidarbc_window import LICENCE, validate_window

CRS = 'EPSG:3157 NAD83(CSRS) / UTM zone 10N'
VERTICAL = 'CGVD2013 (EPSG:6647)'
# Offline assembly may span several bounded network captures. This limits only
# allocation, not source coverage or acceptance: gaps remain NaN and every
# captured input is still verified. Network crops retain their 8 Mpx limit.
MAX_MOSAIC_PIXELS = 32_000_000


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def mosaic_crops(paths, bounds, out):
    x0, y0, x1, y1 = validate_window(bounds, MAX_MOSAIC_PIXELS)
    out = Path(out)
    if out.suffix != '.npz' or out.exists() or out.with_suffix('.json').exists():
        raise ValueError('Fresh NPZ and receipt paths required')
    if not paths or len(paths) > 65535:
        raise ValueError('Expected one to 65535 verified source crops')
    height = np.full((y1-y0, x1-x0), np.nan, np.float32)
    owner = np.zeros(height.shape, np.uint16)
    inputs, tiles = [], []
    for index, path in enumerate(map(Path, paths), 1):
        receipt = path.with_suffix('.json')
        meta = json.loads(receipt.read_text())
        digest = sha(path)
        if (meta.get('schema') != 'raftsim.lidarbc_dem_crop.v1' or
                meta.get('npz_sha256') != digest or meta.get('crs') != CRS or
                meta.get('vertical') != VERTICAL or meta.get('cell_m') != 1.):
            raise ValueError('Unverified crop identity, spacing or coordinate frame')
        sx0, sy0, sx1, sy1 = validate_window(meta['window_utm'], MAX_MOSAIC_PIXELS)
        with np.load(path, allow_pickle=False) as src:
            data = src['height_m']
            if (float(src['cell_m']) != 1. or float(src['x0']) != sx0 or
                    float(src['y_top']) != sy1 or data.dtype != np.float32 or
                    data.shape != (sy1-sy0, sx1-sx0) or
                    list(data.shape) != meta['shape'] or np.isinf(data).any()):
                raise ValueError('Crop array differs from its native grid receipt')
            left, right = max(x0, sx0), min(x1, sx1)
            bottom, top = max(y0, sy0), min(y1, sy1)
            if left >= right or bottom >= top:
                raise ValueError('Input crop does not intersect requested window')
            values = data[sy1-top:sy1-bottom, left-sx0:right-sx0]
            target = height[y1-top:y1-bottom, left-x0:right-x0]
            target_owner = owner[y1-top:y1-bottom, left-x0:right-x0]
            overlap = np.isfinite(target) & np.isfinite(values)
            delta = np.abs(target[overlap].astype(float) - values[overlap])
            take = ~np.isfinite(target) & np.isfinite(values)
            target[take] = values[take]
            target_owner[take] = index
            inputs.append(dict(path=str(path), sha256=digest,
                               receipt_sha256=sha(receipt), source_index=index,
                               contributed_pixels=int(take.sum()), overlap_pixels=int(overlap.sum()),
                               overlap_abs_difference_m_p95=float(np.percentile(delta, 95)) if delta.size else None,
                               overlap_abs_difference_m_max=float(delta.max()) if delta.size else None))
        for tile in meta['tiles']:
            if tile not in tiles:
                tiles.append(tile)
    finite = np.isfinite(height)
    if not finite.any():
        raise ValueError('No valid captured terrain in requested window')
    out.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(out, height_m=height, x0=float(x0), y_top=float(y1),
                        cell_m=1., source_index=owner)
    metadata = dict(schema='raftsim.lidarbc_dem_crop.v1',
                    generator='physics/scripts/mosaic_lidarbc_crops.py',
                    generated_utc=datetime.now(timezone.utc).isoformat(),
                    window_utm=[x0, y0, x1, y1], shape=list(height.shape), cell_m=1.,
                    crs=CRS, vertical=VERTICAL, source='LidarBC native DEM crop mosaic',
                    licence_url=LICENCE,
                    attribution='Contains information licensed under the Open Government Licence - British Columbia',
                    ownership='first finite native pixel; later inputs fill gaps only; no averaging or interpolation',
                    inputs=inputs, tiles=tiles, npz=out.name, npz_sha256=sha(out),
                    valid_share=float(finite.mean()), missing_pixels=int((~finite).sum()),
                    height_range_m=[float(height[finite].min()), float(height[finite].max())],
                    measured_underwater_bed=False, rapid_boundaries_verified=False,
                    playable_acceptance=False)
    out.with_suffix('.json').write_text(json.dumps(metadata, indent=2)+'\n', encoding='utf-8')
    return metadata


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('crops', type=Path, nargs='+')
    parser.add_argument('--window', type=float, nargs=4, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    result = mosaic_crops(args.crops, args.window, args.out)
    print(json.dumps({key: result[key] for key in ('shape', 'valid_share', 'missing_pixels', 'inputs', 'npz_sha256')}, indent=2))
