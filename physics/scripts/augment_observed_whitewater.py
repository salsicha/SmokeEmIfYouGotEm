"""Add a reach's observed-rapid catalogue to a curved map's observed-whitewater layer (numpy only).

    augment_observed_whitewater.py <scenario_export_dir> <catalogue.json>

<scenario_export_dir> is a committed export (cooked_flow_fields/manifest.json with
one band whose `observed_whitewater` is the photographed layer the exporter just
wrote, and runtime/moving_water_streaming.json). The catalogue is in the
scenario (in-game) station/lateral frame. Each cell's whitewater fraction
becomes the larger of the photographed fraction and the catalogue's expected
whitewater (export_cartesian_observed_whitewater.catalogue_whitewater: broken
water across each rapid by class, a white core behind every hole and pour-over,
crest caps along wave trains, a band along laterals). Photographs at 10 m
(Sentinel-2) miss narrow holes and wave trains that outfitters, guidebooks and
videos describe; this adds them as appearance evidence. Render-only.

The layer file, the band's `observed_whitewater` record (with the catalogue and
its hash) and the streaming manifest's hash of the cooked manifest are updated.
Run once, right after the exporter: a layer that already carries a catalogue is
refused, so catalogue whitewater never compounds.
"""
import argparse
import hashlib
import json
import os
import struct
from pathlib import Path

import numpy as np

from export_cartesian_observed_whitewater import catalogue_whitewater


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def write_text(path, text):
    tmp = str(path) + '.tmp'
    Path(tmp).write_text(text)
    os.replace(tmp, path)


def read_rsbf(path):
    b = Path(path).read_bytes()
    magic, ver, width, rows, lat0, dlat = struct.unpack_from('<IIiiff', b, 0)
    assert magic == 0x52534246 and ver == 1
    off = struct.calcsize('<IIiiff'); out = []
    for dt in ('<f4', '<f4', '<f4', 'u1'):
        n = struct.unpack_from('<i', b, off)[0]; off += 4
        a = np.frombuffer(b, dtype=dt, count=n, offset=off); off += n * np.dtype(dt).itemsize
        out.append(a.copy())
    st, elev, energy, wet = out
    return dict(width=width, rows=rows, lat0=lat0, dlat=dlat, station=st, elev=elev.reshape(rows, width),
                energy=energy.reshape(rows, width), wet=wet.reshape(rows, width))


def write_rsbf(path, f):
    # write beside and rename: truncating a tracked file in place can fail on
    # Windows while another process has it mapped
    tmp = str(path) + '.tmp'
    with open(tmp, 'wb') as fb:
        fb.write(struct.pack('<IIiiff', 0x52534246, 1, f['width'], f['rows'], float(f['lat0']), float(f['dlat'])))
        for arr, fmt in ((f['station'], '<f4'), (f['elev'], '<f4'), (f['energy'], '<f4'), (f['wet'], 'u1')):
            flat = np.ascontiguousarray(arr).astype(fmt).ravel()
            fb.write(struct.pack('<i', flat.size)); fb.write(flat.tobytes())
    os.replace(tmp, path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('export', type=Path)
    ap.add_argument('catalogue', type=Path)
    args = ap.parse_args()
    cooked = args.export / 'cooked_flow_fields'
    mpath = cooked / 'manifest.json'
    manifest = json.loads(mpath.read_text())
    (band,) = manifest['bands']
    rec = band['observed_whitewater']
    assert not rec.get('catalogue'), 'layer already carries a catalogue: re-run the exporter first'
    cat = json.loads(args.catalogue.read_text(encoding='utf-8'))
    assert cat.get('station_frame') == 'scenario', 'curved-map catalogues use the scenario (in-game) frame'
    if cat.get('rapid_station_frame', 'scenario').startswith('evidence'):
        # rapids given in the evidence frame keep their scenario station beside it (Futaleufu)
        cat = dict(cat, rapids=[dict(r, station_m=r['scenario_station_m']) for r in cat.get('rapids', [])])
    path = cooked / rec['file']
    assert sha(path) == rec['sha256'], 'layer differs from its manifest record'
    f = read_rsbf(path)
    st = np.broadcast_to(f['station'][:, None], (f['rows'], f['width'])).astype(float)
    lat = np.broadcast_to((f['lat0'] + f['dlat'] * np.arange(f['width']))[None, :], (f['rows'], f['width'])).astype(float)
    # where the cook is wet (the layer's own wet flag is all ones on curved maps)
    wet_arr = np.load(cooked / band['arrays']['wet_mask']['file']).astype(bool).T
    cw = catalogue_whitewater(st, lat, wet_arr, cat)
    photographed = f['energy'].astype(float)
    f['energy'] = np.maximum(photographed, cw).astype(np.float32)
    write_rsbf(path, f)
    rec.update(sha256=sha(path), cells_with_whitewater=int((f['energy'] > 0).sum()),
               catalogue=dict(path=args.catalogue.resolve().relative_to(Path(__file__).resolve().parents[2]).as_posix(),
                              sha256=sha(args.catalogue), rapids=len(cat.get('rapids', [])), features=len(cat.get('features', [])),
                              cells_raised=int((cw > photographed + 0.02).sum()),
                              method='max(photographed fraction, catalogue expected whitewater): broken water per rapid class, '
                                     'hole/pour-over cores two widths downstream, wave-train crest caps, lateral bands'),
               provenance=rec.get('provenance', '') + '; plus observed rapids that the imagery does not resolve (outfitter, '
                          'guidebook, video observations; positions and sizes approximate)')
    write_text(mpath, json.dumps(manifest, indent=2) + '\n')
    spath = args.export / 'runtime/moving_water_streaming.json'
    if spath.exists():
        stream = json.loads(spath.read_text())
        if 'full_reach_transit_seed' in stream:
            stream['full_reach_transit_seed']['cooked_fields_manifest_sha256'] = sha(mpath)
            write_text(spath, json.dumps(stream, indent=2) + '\n')
    print(json.dumps(dict(cells_with_whitewater=rec['cells_with_whitewater'], cells_raised=rec['catalogue']['cells_raised'])))


if __name__ == '__main__':
    main()
