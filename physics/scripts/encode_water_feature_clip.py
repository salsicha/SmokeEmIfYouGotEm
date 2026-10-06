"""Encode a uniform-time sequence of verified rendered liquid frames to MP4/APNG."""
import argparse
import hashlib
import json
from pathlib import Path

import imageio_ffmpeg
import numpy as np
from PIL import Image


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    args = parser.parse_args()
    source = json.loads((args.directory/'frames.json').read_text())
    rows = source['frames']
    if not source['complete'] or len(rows) < 2:
        raise ValueError('Complete motion sequence required')
    stride = rows[1]['frame']-rows[0]['frame']
    if stride <= 0 or any(b['frame']-a['frame'] != stride for a, b in zip(rows, rows[1:])):
        raise ValueError('Frame sequence must be strictly increasing and uniform')
    fps = source['simulation_fps']/stride
    dest = args.directory/'feature.mp4'
    apng = args.directory/'feature.png'
    if dest.exists() or apng.exists():
        raise FileExistsError('Refusing to replace a rendered clip')
    images = []
    for row in rows:
        path = Path(row['image'])
        if hashlib.sha256(path.read_bytes()).hexdigest() != row['sha256']:
            raise ValueError(f'Rendered frame changed: {path}')
        images.append(Image.open(path).convert('RGB'))
    if len({im.size for im in images}) != 1:
        raise ValueError('Inconsistent image dimensions')
    writer = imageio_ffmpeg.write_frames(str(dest), images[0].size, fps=fps,
        codec='libx264', pix_fmt_out='yuv420p', macro_block_size=2,
        output_params=['-crf', '18', '-movflags', '+faststart'])
    writer.send(None)
    for im in images:
        writer.send(np.asarray(im))
    writer.close()
    # APNG gives an inline preview. It repeats playback; simulation itself was
    # not constructed or altered to be a seamless loop.
    images[0].save(apng, save_all=True, append_images=images[1:],
                   duration=1000/fps, loop=0, disposal=0, blend=0)
    with Image.open(apng) as decoded:
        assert decoded.n_frames == len(images)
        for i, im in enumerate(images):
            decoded.seek(i)
            np.testing.assert_array_equal(np.asarray(decoded.convert('RGB')), np.asarray(im))
    decoded_video = imageio_ffmpeg.read_frames(str(dest), pix_fmt='rgb24')
    meta = next(decoded_video)
    decoded_count = sum(1 for _ in decoded_video)
    if decoded_count != len(images):
        raise ValueError('MP4 frame-count mismatch')
    changes = [float(np.abs(np.asarray(b).astype(float)-np.asarray(a).astype(float)).mean())
               for a, b in zip(images, images[1:])]
    report = dict(frames=len(images), playback_fps=fps, duration_seconds=len(images)/fps,
                  simulation_interval_seconds=[rows[0]['seconds'], rows[-1]['seconds']],
                  speed_multiplier=1, apng_lossless_verified=True, mp4_decoded_frames=decoded_count,
                  mean_pixel_changes=changes, adjacent_duplicate_frames=sum(v == 0 for v in changes),
                  seamless_loop=False, real_time_performance_measured=False,
                  mp4_sha256=hashlib.sha256(dest.read_bytes()).hexdigest())
    (args.directory/'clip.json').write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
