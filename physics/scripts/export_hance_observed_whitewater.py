"""Bake the 2021 Hance imagery whitewater into a render-only station/lateral field (numpy only).

The cooked 2 m field cannot place Hance's whitewater where the photographs
show it (audit_hance_whitewater_indicators.py: best matched-area IoU 0.14,
Froude-based foam 0.07). The imagery was taken at the cooked flow (steady
~8,000 cfs, 2021), so the photographed extent is used directly as
appearance evidence.

For each cell of the cooked curvilinear grid (rows = lateral, columns =
station) the whitewater fraction is the share of 4 x 4 sub-points inside
the cell that fall on the evidence foam mask (1 m, 2021 orthophoto). The
sub-points follow the grid's local station/lateral axes (Jacobian of the
cell-centre world coordinates).

Writes cooked_flow_fields/observed_whitewater_<band>.bin in the RSBF v1
layout (rows = stations; channels: cooked surface, whitewater fraction in the
energy channel, all-ones mask) read by
URaftSimWaterRuntimeAdapter::LoadObservedWhitewaterFieldFromFile, a preview
PNG under evidence/, and records it in the cooked manifest (band
`observed_whitewater`); the moving-window manifest's hash of the cooked
manifest is refreshed. The cooked arrays are not touched.
"""
import argparse
import hashlib
import json
import os
import struct
from pathlib import Path

import numpy as np

from png_numpy import write_png

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / 'physics/data/real_world/colorado_river_grand_canyon_rowing'
SCEN = DATA / 'scenario_hance_evidence_2021'
X0, Y1 = 211300.0, 560300.0


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_text(path, text):
    # Some freshly checked-out files here refuse an in-place truncating open
    # (EINVAL on Windows); write beside them and swap.
    tmp = Path(str(path) + '.tmp')
    tmp.write_text(text)
    os.replace(tmp, path)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('evidence', type=Path, help='evidence folder holding evidence_grid.npz (build_hance_evidence_grid.py)')
    ap.add_argument('scenario_root', type=Path, help='scenario build folder holding reference.npz')
    args = ap.parse_args()
    cooked = SCEN / 'cooked_flow_fields'
    manifest_path = cooked / 'manifest.json'
    manifest = json.loads(manifest_path.read_text())
    (band,) = manifest['bands']
    grid = manifest['grid']
    ny, nx, d = grid['ny'], grid['nx'], grid['dx_m']
    evidence_grid = args.evidence / 'evidence_grid.npz'
    ev_manifest = json.loads((SCEN / 'evidence/evidence_manifest.json').read_text())
    assert sha(evidence_grid) == json.loads((DATA / 'terrain/hance_evidence_2021/hance_evidence_terrain_manifest.json')
                                            .read_text())['inputs']['evidence_grid_sha256'], 'evidence grid differs from the export'
    evg = np.load(evidence_grid)
    ref = np.load(args.scenario_root / 'reference.npz')
    wx, wy = ref['world_x'], ref['world_y']
    assert wx.shape == (ny, nx)
    foam_mask = evg['foam']
    # Local axes per cell: world metres per column (station) and per row (lateral).
    dxc, dyc = np.gradient(wx, axis=1), np.gradient(wy, axis=1)
    dxr, dyr = np.gradient(wx, axis=0), np.gradient(wy, axis=0)
    frac = np.zeros((ny, nx))
    offs = (np.arange(4) + 0.5) / 4 - 0.5
    for a in offs:
        for b in offs:
            px = wx + a * dxc + b * dxr
            py = wy + a * dyc + b * dyr
            cc = np.floor(px - X0).astype(int); rr = np.floor(Y1 - py).astype(int)
            inside = (cc >= 0) & (cc < foam_mask.shape[1]) & (rr >= 0) & (rr < foam_mask.shape[0])
            hit = np.zeros((ny, nx), bool)
            hit[inside] = foam_mask[rr[inside], cc[inside]]
            frac += hit
    frac /= 16.0
    # One 1-2-1 pass in both axes: 2 m cells otherwise draw rectangular
    # white blocks; the photographed patches have rounded edges.
    p = np.pad(frac, 1, mode='edge')
    frac = (0.25 * p[:-2, 1:-1] + 0.5 * p[1:-1, 1:-1] + 0.25 * p[2:, 1:-1])
    p = np.pad(frac, ((0, 0), (1, 1)), mode='edge')
    frac = 0.25 * p[:, :-2] + 0.5 * p[:, 1:-1] + 0.25 * p[:, 2:]
    bed = np.load(cooked / band['arrays']['bed']['file'])
    h = np.load(cooked / band['arrays']['h']['file'])
    wet = np.load(cooked / band['arrays']['wet_mask']['file']).astype(bool)
    surface = np.where(wet, bed + h, bed)
    out = cooked / f"observed_whitewater_{band['band_id']}.bin"
    with open(out, 'wb') as fb:
        fb.write(struct.pack('<IIiiff', 0x52534246, 1, ny, nx, float(grid['origin_y_m']), float(d)))
        for arr, fmt in ((np.arange(nx, dtype=np.float32) * np.float32(d), '<f4'),
                         (np.ascontiguousarray(surface.T), '<f4'), (np.ascontiguousarray(frac.T), '<f4'),
                         (np.ones((nx, ny), np.uint8), 'u1')):
            flat = arr.astype(fmt).ravel()
            fb.write(struct.pack('<i', flat.size)); fb.write(flat.tobytes())
    preview = SCEN / 'evidence/observed_whitewater_preview.png'
    img = np.zeros((ny, nx, 3), np.uint8)
    img[wet] = (30, 60, 90)
    v = (frac * 255).astype(np.uint8)
    img[frac > 0] = np.stack([v, v, v], -1)[frac > 0]
    write_png(preview, np.repeat(np.repeat(img[::-1], 3, 0), 2, 1))
    river = ref['river']
    band['observed_whitewater'] = dict(
        file=out.name, sha256=sha(out), format='RSBF v1 rows=station cols=lateral; energy channel = whitewater fraction 0-1',
        source='2021 corridor orthophoto whitewater mask (evidence_grid foam, 1 m), same flights and flow as the cook',
        evidence_grid_sha256=sha(evidence_grid), sampling='4 x 4 sub-points per 2 m cell along the local station/lateral axes, then one 1-2-1 smoothing pass per axis',
        cells_with_whitewater=int((frac > 0).sum()), mean_fraction_in_imagery_river=float(frac[river].mean()),
        provenance='measured appearance (photographed whitewater extent at the cooked flow); not predicted by the solver',
        use='render-only floor on the displayed live foam and the far-field cue, scaled by ARaftSimRiverWaterConfig::ObservedWhitewaterGain; never gameplay or foam transport state',
        preview=(SCEN / 'evidence/observed_whitewater_preview.png').relative_to(ROOT).as_posix())
    write_text(manifest_path, json.dumps(manifest, indent=2) + '\n')
    stream_path = SCEN / 'runtime/moving_water_streaming.json'
    stream = json.loads(stream_path.read_text())
    stream['full_reach_transit_seed']['cooked_fields_manifest_sha256'] = sha(manifest_path)
    write_text(stream_path, json.dumps(stream, indent=2) + '\n')
    print(json.dumps({k: band['observed_whitewater'][k] for k in ('sha256', 'cells_with_whitewater', 'mean_fraction_in_imagery_river')}))
    _ = ev_manifest


if __name__ == '__main__':
    main()
