"""Register captured valley colour once, never tile it as metre-scale detail.

This is dated appearance (including capture shadows), not measured albedo or
new terrain/vegetation geometry. Original native-grid reflectance is retained
in the pinned source archive. Tone mapping is an explicit display operation.
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def display_rgb(raw, valid):
    values = np.stack([raw[b] for b in ('red', 'green', 'blue')], axis=-1)
    if values.shape[:2] != valid.shape or not valid.all() or np.any(values == 0):
        raise ValueError('Complete valid RGB coverage required; no invented fill')
    linear = np.clip((values.astype(np.float64) * .0001 - .1) / .3, 0, 1)
    srgb = np.where(linear <= .0031308, linear * 12.92, 1.055 * linear ** (1/2.4) - .055)
    return np.rint(srgb * 255).astype(np.uint8)


def registration(grid, origin):
    t = grid['transform']; h, w = grid['shape']
    if (grid['epsg'] != 32718 or t[0] != 10 or t[4] != -10 or t[1] != 0 or t[3] != 0
            or min(h, w) < 2 or not np.isfinite([*t, *origin]).all()):
        raise ValueError('Finite north-up native UTM18S 10 m frame required')
    # World X=east-origin; Y=origin_north-north, both in centimetres.
    # UV=0 is the outer northwest pixel edge; texel centres use (index+.5)/size.
    return dict(scale_xy=[1/(w*1000), 1/(h*1000)],
                offset_xy=[(origin[0]-t[2])/(w*10), (t[5]-origin[1])/(h*10)])


def build(source, output, date='2026-01-04'):
    source, output = Path(source), Path(output)
    if output.exists():
        raise ValueError('Fresh output required')
    manifest_path = source/'manifest.json'
    manifest = json.loads(manifest_path.read_text())
    if manifest['schema'] != 'raftsim.futaleufu_continuous_sources.v1':
        raise ValueError('Expected verified full corridor source window')
    item = next(x for x in manifest['optical'] if x['datetime'].startswith(date))
    path = (source/item['file']).resolve(); path.relative_to(source.resolve())
    if sha(path) != item['sha256']:
        raise ValueError('Captured optical source changed')
    with np.load(path, allow_pickle=False) as raw:
        rgb = display_rgb(raw, raw['valid'])
    if list(rgb.shape[:2]) != manifest['grid']['shape']:
        raise ValueError('Pixel shape differs from frame')
    origin = [739986., 5195961.5]
    uv = registration(manifest['grid'], origin)
    output.mkdir(parents=True)
    image = output/'captured_colour.png'; Image.fromarray(rgb).save(image)
    receipt = dict(schema='raftsim.futaleufu_continuous_colour.v1',
                   source_manifest_sha256=sha(manifest_path), source_pixels_sha256=sha(path),
                   capture_datetime=item['datetime'], attribution=manifest['optical_attribution'].replace('[year]',date[:4]),
                   license=manifest['optical_license'], grid=manifest['grid'], horizontal_origin_m=origin,
                   world_y_sign=-1, world_cm_to_uv=uv, image='captured_colour.png', image_sha256=sha(image),
                   display_transform='clip((DN*0.0001-0.1)/0.3,0,1), linear-to-sRGB, nearest uint8',
                   limitations=['Captured lighting and shadows, not measured albedo',
                                '10 m appearance, not metre-scale surface detail',
                                'Source not cloud-screened; visual review required',
                                'No geometry, river stage, collision, flow or vegetation changed'])
    (output/'manifest.json').write_text(json.dumps(receipt, indent=2)+'\n')
    return receipt


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--sources', type=Path, required=True); p.add_argument('--out', type=Path, required=True)
    p.add_argument('--date', default='2026-01-04')
    a = p.parse_args(); print(json.dumps(build(a.sources, a.out, a.date), indent=2))
