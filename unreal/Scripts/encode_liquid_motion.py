"""Lossless animated PNG from verified engine frames; playback is not game FPS."""
from pathlib import Path
import argparse
import hashlib
import json
import numpy as np
from PIL import Image


def encode(directory):
    directory = Path(directory)
    destination = directory/'motion.png'
    report_path = directory/'motion_report.json'
    if destination.exists() or report_path.exists():
        raise FileExistsError('Motion output already exists')
    capture = json.loads((directory/'capture.json').read_text())
    if not capture['complete'] or not capture['foam_motion_capture']:
        raise ValueError('Complete actual engine motion capture required')
    records = {r['name']+'.png': r for r in capture['captures']}
    images = []
    for i in range(30):
        path = directory/f'motion_{i:03d}.png'
        record = records[path.name]
        if hashlib.sha256(path.read_bytes()).hexdigest() != record['image_sha256']:
            raise ValueError(f'Changed engine frame: {path.name}')
        images.append(Image.open(path).convert('RGB'))
    if any(im.size != images[0].size for im in images):
        raise ValueError('Inconsistent frame dimensions')
    images[0].save(destination, format='PNG', save_all=True, append_images=images[1:],
                   duration=[66, 67, 67]*10, loop=0, disposal=0, blend=0)
    # Decode all frames, not just the first image: encoding must be lossless.
    with Image.open(destination) as decoded:
        if decoded.n_frames != len(images):
            raise ValueError('Incomplete animation')
        for i, original in enumerate(images):
            decoded.seek(i)
            np.testing.assert_array_equal(np.asarray(decoded.convert('RGB')), np.asarray(original))
    changes = [float(np.abs(np.asarray(b).astype(float)-np.asarray(a).astype(float)).mean())
               for a, b in zip(images, images[1:])]
    report = dict(frame_count=30, duration_seconds=2, playback_fps=15,
                  source_simulation_fps=60, source_step_stride=4,
                  decoded_frames_exactly_match_engine=True,
                  mean_absolute_frame_changes=changes,
                  exact_duplicate_adjacent_frames=sum(v == 0 for v in changes),
                  game_performance_or_visual_acceptance=False,
                  output_sha256=hashlib.sha256(destination.read_bytes()).hexdigest())
    report_path.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    encode(parser.parse_args().directory)
