"""Full-reach NAIP colour drape for the normal South Fork terrain.

Outside the 680 m Troublemaker window, `M_SouthForkCompositeGround` currently
paints every terrain tile with one procedural rock/sand albedo, so the 33 km
run reads as bare desert hills. The repository already holds official
USDA/USGS NAIP exports for every full-reach window
(`production_corridor/full_reach_windows/*/source/naip.png`, EPSG:3857 bounds in
each window manifest). This builder reprojects them into the playable terrain
frame (UTM 10N, 2 m composite grid extent) and writes one RGBA drape:

* RGB: NAIP colour (orthophoto: includes capture lighting, canopy and roofs --
  it is appearance evidence, not intrinsic albedo);
* A: 1 where the drape may be used, 0 on the inferred submerged bed
  (`unknown_submerged_bed_mask.tif`) and where no window covers the pixel.

Registration is checked by cross-correlating an imagery water index against
the terrain's own water mask; the best integer offset and its correlation are
recorded. Run inside Blender (`--background --python`) for image I/O.
"""
import hashlib
import json
import struct
import sys
import zlib
from pathlib import Path

import bpy
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'physics/data/real_world/south_fork_american_chili_bar'
WINDOWS = BASE / 'production_corridor/full_reach_windows'
FULL = BASE / 'reconstruction_2026_09/full_reach'
MASK = FULL / 'unknown_submerged_bed_mask.tif'
CONTEXT = FULL / 'source_context_extension/manifest.json'
COMPOSITE = FULL / 'composite_terrain/manifest.json'

WIDTH, HEIGHT = 16384, 8192
WORLD_ORIGIN_UTM = (689237.0, 4293073.0)  # full-reach world frame: x=east*100, y=-north*100


def load_rgba(path):
    img = bpy.data.images.load(str(path))
    w, h = img.size
    arr = np.empty(w * h * img.channels, dtype=np.float32)
    img.pixels.foreach_get(arr)
    arr = arr.reshape(h, w, img.channels)[::-1]  # Blender rows are bottom-up
    bpy.data.images.remove(img)
    return arr


def utm_to_lonlat(e, n, zone=10):
    a, f, k0 = 6378137.0, 1 / 298.257223563, 0.9996
    e2 = f * (2 - f)
    ep2 = e2 / (1 - e2)
    x = e - 500000.0
    m = n / k0
    mu = m / (a * (1 - e2 / 4 - 3 * e2 ** 2 / 64 - 5 * e2 ** 3 / 256))
    e1 = (1 - np.sqrt(1 - e2)) / (1 + np.sqrt(1 - e2))
    phi1 = (mu + (3 * e1 / 2 - 27 * e1 ** 3 / 32) * np.sin(2 * mu)
            + (21 * e1 ** 2 / 16 - 55 * e1 ** 4 / 32) * np.sin(4 * mu)
            + (151 * e1 ** 3 / 96) * np.sin(6 * mu) + (1097 * e1 ** 4 / 512) * np.sin(8 * mu))
    s, c, t = np.sin(phi1), np.cos(phi1), np.tan(phi1)
    n1 = a / np.sqrt(1 - e2 * s * s)
    t1 = t * t
    c1 = ep2 * c * c
    r1 = a * (1 - e2) / (1 - e2 * s * s) ** 1.5
    d = x / (n1 * k0)
    lat = phi1 - (n1 * t / r1) * (d ** 2 / 2 - (5 + 3 * t1 + 10 * c1 - 4 * c1 ** 2 - 9 * ep2) * d ** 4 / 24
                                  + (61 + 90 * t1 + 298 * c1 + 45 * t1 ** 2 - 252 * ep2 - 3 * c1 ** 2) * d ** 6 / 720)
    lon0 = np.radians(-183.0 + 6.0 * zone)
    lon = lon0 + (d - (1 + 2 * t1 + c1) * d ** 3 / 6
                  + (5 - 2 * c1 + 28 * t1 - 3 * c1 ** 2 + 8 * ep2 + 24 * t1 ** 2) * d ** 5 / 120) / c
    return lon, lat


def lonlat_to_mercator(lon, lat):
    r = 6378137.0
    return r * lon, r * np.log(np.tan(np.pi / 4 + lat / 2))


def write_png_rgba(path, rgba):
    h, w, _ = rgba.shape
    compressor = zlib.compressobj(6)
    chunks = []
    row_bytes = w * 4
    for y0 in range(0, h, 256):
        block = rgba[y0:y0 + 256]
        raw = np.zeros((block.shape[0], row_bytes + 1), dtype=np.uint8)
        raw[:, 1:] = block.reshape(block.shape[0], row_bytes)
        chunks.append(compressor.compress(raw.tobytes()))
    chunks.append(compressor.flush())

    def chunk(tag, data):
        return struct.pack('>I', len(data)) + tag + data + struct.pack('>I', zlib.crc32(tag + data) & 0xffffffff)
    with open(path, 'wb') as out:
        out.write(b'\x89PNG\r\n\x1a\n')
        out.write(chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 6, 0, 0, 0)))
        out.write(chunk(b'IDAT', b''.join(chunks)))
        out.write(chunk(b'IEND', b''))


def main():
    args = sys.argv[sys.argv.index('--') + 1:]
    out_dir = Path(args[0]).resolve()
    out_dir.mkdir(parents=True, exist_ok=False)
    context = json.loads(CONTEXT.read_text())
    composite = json.loads(COMPOSITE.read_text())
    first = context['grid']['first_vertex_utm_m']
    cell = context['grid']['cell_m']
    rows, cols = context['grid']['shape']
    e0, n_top = first[0], first[1]
    extent_e = (cols - 1) * cell
    px = extent_e / WIDTH  # square pixels spanning the terrain grid east-west
    extent_n_used = (rows - 1) * cell
    used_rows = int(np.ceil(extent_n_used / px))
    if used_rows > HEIGHT:
        raise SystemExit('Drape height exceeds texture')

    windows = []
    for manifest_path in sorted(WINDOWS.glob('*/manifest.json')):
        manifest = json.loads(manifest_path.read_text())
        naip = manifest_path.parent / 'source/naip.png'
        requested = manifest['bounds']['epsg3857_buffered']
        # The exports requested a square 4096x4096 image for a non-square
        # bbox without adjustAspectRatio=false. ArcGIS ImageServer then
        # expands the bbox about its centre to the image aspect (square
        # pixels), so the returned image spans a square extent, not the
        # requested box. Using the requested box stretched one axis up to 2x.
        cx, cy = (requested[0] + requested[2]) / 2, (requested[1] + requested[3]) / 2
        half = max(requested[2] - requested[0], requested[3] - requested[1]) / 2
        bounds = [cx - half, cy - half, cx + half, cy + half]
        windows.append(dict(name=manifest_path.parent.name, bounds=bounds, requested_bounds=requested, path=naip,
                            sha256=hashlib.sha256(naip.read_bytes()).hexdigest()))

    # Overlapping windows are blended with weights that fall to zero at each
    # window's edge (feather FEATHER_PX source pixels), so exposure differences
    # between separately exported windows do not leave hard seams.
    FEATHER_PX = 200.0
    acc = np.zeros((used_rows, WIDTH, 3), dtype=np.float32)
    wsum = np.zeros((used_rows, WIDTH), dtype=np.float32)
    ee = e0 + (np.arange(WIDTH) + 0.5) * px
    for window in windows:
        img = load_rgba(window['path'])
        h, w = img.shape[:2]
        x0, y0, x1, y1 = window['bounds']
        count = 0
        for r0 in range(0, used_rows, 512):
            r1 = min(r0 + 512, used_rows)
            nn = n_top - (np.arange(r0, r1) + 0.5) * px
            E, N = np.meshgrid(ee, nn)
            lon, lat = utm_to_lonlat(E, N)
            mx, my = lonlat_to_mercator(lon, lat)
            fx = (mx - x0) / (x1 - x0) * w - 0.5
            fy = (y1 - my) / (y1 - y0) * h - 0.5
            inside = (fx >= 0) & (fx <= w - 1) & (fy >= 0) & (fy <= h - 1)
            if not inside.any():
                continue
            ix = np.clip(np.floor(fx[inside]).astype(np.int64), 0, w - 2)
            iy = np.clip(np.floor(fy[inside]).astype(np.int64), 0, h - 2)
            tx = (fx[inside] - ix)[:, None]
            ty = (fy[inside] - iy)[:, None]
            c = (img[iy, ix, :3] * (1 - tx) * (1 - ty) + img[iy, ix + 1, :3] * tx * (1 - ty)
                 + img[iy + 1, ix, :3] * (1 - tx) * ty + img[iy + 1, ix + 1, :3] * tx * ty)
            edge = np.minimum(np.minimum(fx[inside], w - 1 - fx[inside]),
                              np.minimum(fy[inside], h - 1 - fy[inside]))
            weight = np.clip(edge / FEATHER_PX, 1e-4, 1.0).astype(np.float32)
            acc[r0:r1][inside] += (c * weight[:, None]).astype(np.float32)
            wsum[r0:r1][inside] += weight
            count += int(inside.sum())
        window['pixels_used'] = count
        del img

    out = np.zeros((HEIGHT, WIDTH, 4), dtype=np.uint8)
    filled = np.zeros((HEIGHT, WIDTH), dtype=bool)
    covered = wsum > 0
    out[:used_rows][covered, :3] = np.clip(acc[covered] / wsum[covered][:, None] * 255.0 + 0.5, 0, 255).astype(np.uint8)
    out[:used_rows][covered, 3] = 255
    filled[:used_rows] = covered
    del acc, wsum

    # Submerged-bed exclusion from the terrain's own mask (composite grid).
    # Mask values: 0 dry corridor, 1 inferred submerged bed, 255 outside the corridor.
    mask = np.abs(load_rgba(MASK)[..., 0] * 255.0 - 1.0) < 0.5
    mgrid = composite['grid']
    me0, mn_top = mgrid['first_vertex_utm_m']
    mcell = mgrid['cell_m']
    submerged_px = 0
    water_index_rows = []
    for r0 in range(0, used_rows, 512):
        r1 = min(r0 + 512, used_rows)
        nn = n_top - (np.arange(r0, r1) + 0.5) * px
        E, N = np.meshgrid(ee, nn)
        mi = np.round((mn_top - N) / mcell).astype(np.int64)
        mj = np.round((E - me0) / mcell).astype(np.int64)
        ok = (mi >= 0) & (mi < mask.shape[0]) & (mj >= 0) & (mj < mask.shape[1])
        sub = np.zeros(E.shape, bool)
        sub[ok] = mask[mi[ok], mj[ok]]
        out[r0:r1][sub, 3] = 0
        submerged_px += int(sub.sum())
    del mask

    # Registration check: imagery water index (blue minus red, then darkness)
    # correlated with the terrain's submerged mask inside the corridor, over
    # offsets of +/-6 steps of 4 drape pixels (~4.9 m). A registration error
    # shows as a peak away from zero.
    step = 4
    rgb = out[:used_rows:step, ::step, :3].astype(np.float32) / 255.0
    index = (rgb[..., 2] - rgb[..., 0]) - rgb.mean(axis=2)
    rr, cc = np.mgrid[0:rgb.shape[0], 0:rgb.shape[1]]
    E = e0 + (cc * step + 0.5) * px
    N = n_top - (rr * step + 0.5) * px
    raw_mask = load_rgba(MASK)[..., 0] * 255.0

    def mask_values(dn, de):
        mi = np.round((mn_top - (N + dn)) / mcell).astype(np.int64)
        mj = np.round((E + de - me0) / mcell).astype(np.int64)
        ok = (mi >= 0) & (mi < raw_mask.shape[0]) & (mj >= 0) & (mj < raw_mask.shape[1])
        values = np.full(E.shape, 255.0, dtype=np.float32)
        values[ok] = raw_mask[mi[ok], mj[ok]]
        return values
    scores = []
    for dy in range(-6, 7):
        for dx in range(-6, 7):
            v = mask_values(dy * step * px, dx * step * px)
            corridor = v < 128
            scores.append((float(np.corrcoef(index[corridor], (np.abs(v[corridor] - 1) < 0.5))[0, 1]),
                           dy * step * px, dx * step * px))
    zero = [s_ for s_ in scores if s_[1] == 0 and s_[2] == 0][0][0]
    best = max(scores)
    del raw_mask

    png = out_dir / 'T_SouthForkFullReachNAIP.png'
    write_png_rgba(png, out)
    receipt = dict(
        schema='raftsim.south_fork_naip_drape.v1',
        texture=str(png.relative_to(ROOT).as_posix()), sha256=hashlib.sha256(png.read_bytes()).hexdigest(),
        width=WIDTH, height=HEIGHT, used_rows=used_rows, pixel_m=px,
        top_left_utm_m=[e0, n_top], world_origin_utm_m=list(WORLD_ORIGIN_UTM),
        world_uv=dict(u=f'(x*0.01 + {WORLD_ORIGIN_UTM[0] - e0:.4f}) / {px * WIDTH:.4f}',
                      v=f'({n_top - WORLD_ORIGIN_UTM[1]:.4f} + y*0.01) / {px * HEIGHT:.4f}'),
        windows=[{k: v for k, v in w_.items() if k != 'path'} | {'path': str(w_['path'].relative_to(ROOT).as_posix())}
                 for w_ in windows],
        filled_fraction=float(filled[:used_rows].mean()), submerged_pixels_excluded=submerged_px,
        submerged_mask=str(MASK.relative_to(ROOT).as_posix()),
        registration_check=dict(method='(B-R)-luma water index vs terrain submerged mask in the corridor',
                                correlation_at_zero=zero, best_correlation=best[0],
                                best_offset_north_east_m=[best[1], best[2]], offset_step_m=px * step),
        appearance_evidence='USDA NAIP orthoimagery via the USGS/USDA ImageServer exports already in the repository; '
                            'public domain per the service description; includes capture lighting and canopy tops',
        intrinsic_albedo=False, geometry_changed=False)
    (out_dir / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print('DRAPE_RECEIPT ' + json.dumps({k: receipt[k] for k in ('sha256', 'pixel_m', 'filled_fraction', 'registration_check')}))


main()
