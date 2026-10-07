"""Condition only coarse fallback beside native terrain; keep captured data intact.

The output is a derived terrain candidate, NOT another measured elevation
product. Native pixels are immutable. A smooth, bounded taper extends the
native-minus-coarse difference into the coarse side of each source boundary.
Halo sampling makes the operation independent of tile boundaries.
"""
import argparse
import copy
import json
import shutil
from collections import OrderedDict
from pathlib import Path

import numpy as np
import rasterio
from rasterio.transform import from_origin
from rasterio.warp import reproject, Resampling
from scipy.ndimage import binary_dilation, distance_transform_edt

from assemble_chilko_corridor_terrain import checked_fallback
from chilko_corridor_terrain import CorridorTerrain
from mosaic_lidarbc_crops import sha


def condition(height, kind, coarse, radius=200., max_offset=30.):
    height, kind, coarse = np.asarray(height), np.asarray(kind), np.asarray(coarse)
    if (height.ndim != 2 or height.dtype != np.float32 or coarse.shape != height.shape or
            kind.shape != height.shape or not np.isin(kind, [0, 1, 2]).all() or
            not np.array_equal(np.isfinite(height), kind > 0) or np.isinf(height).any() or
            np.isinf(coarse).any() or not 1 <= radius <= 512 or not 0 < max_offset <= 100):
        raise ValueError('Finite-or-missing source terrain and bounded seam parameters required')
    native, fallback = kind == 1, kind == 2
    edge = native & binary_dilation(fallback)
    delta = np.zeros(height.shape, np.float32)
    result, sources = height.copy(), kind.copy()
    if not edge.any():
        return result, sources, delta
    if not np.isfinite(coarse[edge]).all():
        raise ValueError('No coarse overlap at native boundary; cannot infer a correction')
    residual = np.zeros(height.shape, np.float64)
    residual[edge] = height[edge].astype(float) - coarse[edge]
    if np.max(np.abs(residual[edge])) > max_offset:
        raise ValueError('Boundary offset exceeds the reviewed correction limit')
    distance, nearest = distance_transform_edt(~edge, return_indices=True)
    take = fallback & (distance < radius)
    t = np.clip(distance[take] / radius, 0, 1)
    weight = 1 - t*t*(3 - 2*t)
    delta[take] = (residual[tuple(nearest[:, take])] * weight).astype(np.float32)
    result[take] += delta[take]
    sources[take] = 3  # Explicitly inferred native/coarse transition, not LiDAR.
    return result, sources, delta


class HaloInputs:
    """One globally aligned coarse reprojection per source tile, bounded cache."""
    def __init__(self, source, dem):
        self.source, self.dem, self.cache = source, dem, OrderedDict()

    def tile(self, key):
        if key not in self.source.entries:
            return None
        if key in self.cache:
            self.cache.move_to_end(key)
            return self.cache[key]
        height, kind = self.source.load(key)
        row = self.source.entries[key][1]
        coarse = np.full(height.shape, np.nan, np.float32)
        reproject(rasterio.band(self.dem, 1), coarse, src_transform=self.dem.transform,
            src_crs=self.dem.crs, src_nodata=self.dem.nodata,
            dst_transform=from_origin(row['bounds'][0], row['bounds'][3], 1, 1),
            dst_crs='EPSG:3157', dst_nodata=np.nan, resampling=Resampling.bilinear, num_threads=1)
        self.cache[key] = (height, kind, coarse)
        while len(self.cache) > 4:
            self.cache.popitem(last=False)
        return height, kind, coarse

    def halo(self, key, pad):
        size = self.source.size
        height = np.full((size+2*pad, size+2*pad), np.nan, np.float32)
        kind = np.zeros(height.shape, np.uint8)
        coarse = np.full_like(height, np.nan)
        west, south = np.asarray(key)*size-pad
        east, north = west+size+2*pad, south+size+2*pad
        for x in range(key[0]-1, key[0]+2):
            for y in range(key[1]-1, key[1]+2):
                tile = self.tile((x, y))
                if tile is None:
                    continue
                x0, y0, x1, y1 = max(west,x*size), max(south,y*size), min(east,(x+1)*size), min(north,(y+1)*size)
                if x0 >= x1 or y0 >= y1:
                    continue
                src = np.s_[(y+1)*size-y1:(y+1)*size-y0, x0-x*size:x1-x*size]
                dst = np.s_[north-y1:north-y0, x0-west:x1-west]
                for target, values in zip((height, kind, coarse), tile):
                    target[dst] = values[src]
        return height, kind, coarse


def run(source_folder, out, radius=200., max_offset=30.):
    if out.exists():
        raise ValueError('Fresh derived terrain directory required')
    source = CorridorTerrain(source_folder)
    m = source.manifest
    if m.get('schema') != 'raftsim.chilko_corridor_terrain.v1':
        raise ValueError('Condition the original captured terrain only once')
    if not np.isfinite([radius, max_offset]).all() or not 1 <= radius <= min(512, source.size-2) or not 0 < max_offset <= 100:
        raise ValueError('Invalid bounded seam correction')
    fallback_path = Path(m['inputs']['fallback_manifest'])
    if sha(fallback_path) != m['inputs']['fallback_sha256']:
        raise ValueError('Changed coarse fallback receipt')
    _, paths = checked_fallback(fallback_path)
    receipt = sha(source.folder/'manifest.json')
    out.mkdir(parents=True); (out/'tiles').mkdir()
    rows = []; pad = int(np.ceil(radius))+1
    with rasterio.open(paths['dtm']) as dem:
        inputs = HaloInputs(source, dem)
        for row in m['tiles']:
            path = source.folder/row['file']; target = out/row['file']
            if sha(path) != row['sha256']:
                raise ValueError('Changed source terrain tile')
            record = copy.deepcopy(row)
            record['source_sha256'] = row['sha256']
            record['conditioned_pixels'] = 0
            record['correction_range_m'] = [0., 0.]
            if row['coarse_pixels']:
                h, k, coarse = inputs.halo(tuple(row['cell']), pad)
                corrected, kinds, delta = condition(h, k, coarse, radius, max_offset)
                core = np.s_[pad:-pad, pad:-pad]
                corrected, kinds, delta = corrected[core], kinds[core], delta[core]
                with np.load(path, allow_pickle=False) as z:
                    arrays = {name:z[name] for name in z.files}
                original = arrays['height_m']; native = arrays['source_kind'] == 1
                if not np.array_equal(original[native], corrected[native]) or np.any(delta[native]):
                    raise AssertionError('Seam operation changed native survey terrain')
                arrays.update(height_m=corrected, source_kind=kinds, seam_correction_m=delta)
                np.savez_compressed(target, **arrays)
                record.update(sha256=sha(target), conditioned_pixels=int((kinds==3).sum()),
                    coarse_pixels=int((kinds==2).sum()), correction_range_m=[float(delta.min()),float(delta.max())])
            else:
                shutil.copyfile(path, target)
            rows.append(record)
            print(json.dumps({k:record[k] for k in ('cell','conditioned_pixels','correction_range_m')}), flush=True)
    result = copy.deepcopy(m)
    result.update(schema='raftsim.chilko_corridor_conditioned_terrain.v1', tiles=rows,
        source_terrain=dict(manifest=str(source.folder/'manifest.json'), sha256=receipt),
        inferred_seam=dict(radius_m=radius, max_boundary_offset_m=max_offset,
            method='nearest native boundary minus matched coarse terrain; cubic taper on coarse pixels only',
            native_pixels_unchanged=True, measured=False, engine_validated=False),
        ownership='All native heights preserved; coarse terrain within the recorded boundary taper is an inferred transition.')
    result['source_kind']['3'] = 'MRDEM-derived terrain with inferred native-boundary transition; NOT measured LiDAR'
    if sha(source.folder/'manifest.json') != receipt:
        raise ValueError('Terrain source changed during conditioning')
    (out/'manifest.json').write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')
    return result


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source', type=Path, required=True); p.add_argument('--out', type=Path, required=True)
    p.add_argument('--radius-m', type=float, default=200.); p.add_argument('--max-offset-m', type=float, default=30.)
    a = p.parse_args(); run(a.source.resolve(), a.out.resolve(), a.radius_m, a.max_offset_m)
