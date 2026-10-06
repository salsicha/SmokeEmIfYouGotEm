"""Annotated APNG of engine-rendered saved gravity-control motion, not AI art.

Keeps actual physical timestamps, states slowdown and exclusions on every frame.
Does not edit liquid geometry, solver data or Blender scene/materials.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--render', type=Path, required=True)
    parser.add_argument('--motion', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    render, motion = (json.loads(p.read_text()) for p in (args.render, args.motion))
    if len(render['frames']) != 21 or render.get('preview_only'):
        raise ValueError('Complete 21 engine views required, not a preview')
    pins = {str(args.render.resolve()): digest(args.render), str(args.motion.resolve()): digest(args.motion),
        str(Path(__file__).resolve()): digest(__file__), **render['outputs_sha256'], **motion['outputs_sha256']}
    if any(digest(p) != sha for p, sha in pins.items()):
        raise ValueError('Pinned engine/physical evidence changed')
    font = ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf', 20)
    small = ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf', 15)
    times = np.load(motion['arrays']['times'], allow_pickle=False); frames = []
    for i, path in enumerate(render['frames']):
        with Image.open(path) as image:
            source = image.convert('RGB')
        canvas = Image.new('RGB', (640, 700), (15, 24, 34)); canvas.paste(source, (0, 76)); draw = ImageDraw.Draw(canvas)
        draw.text((18, 8), 'Free-flight liquid parcel: gravity calibration', font=font, fill=(231, 241, 249))
        draw.text((18, 37), 'NOT a completed waterfall, impact or splash', font=small, fill=(251, 207, 137))
        time_s = times[i]; u = np.array(motion['initial_velocity_m_s'])+time_s*np.array(motion['gravity_m_s2'])
        draw.text((18, 642), f'Physical t = {time_s:.2f} s    speed = {np.linalg.norm(u):.3f} m/s    mass = 1.800 kg', font=small, fill=(230, 240, 250))
        draw.text((18, 668), '5x slow motion; end hold. No surface tension, air drag or impact.', font=small, fill=(173, 191, 208))
        frames.append(canvas)
    frames[0].save(args.output, format='PNG', save_all=True, append_images=frames[1:],
        duration=[100]*20+[500], loop=1, disposal=0, blend=0)
    with Image.open(args.output) as saved:
        if saved.n_frames != 21 or saved.size != (640, 700) or saved.info.get('loop') != 1:
            raise ValueError('APNG frame count, geometry or repeat setting changed')
        durations = []
        for i in range(saved.n_frames):
            saved.seek(i); durations.append(saved.info['duration'])
            if not np.array_equal(np.asarray(saved.convert('RGB')), np.asarray(frames[i])):
                raise ValueError('Stored animation frame differs from annotated engine view')
    if any(digest(p) != sha for p, sha in pins.items()):
        raise ValueError('Assembly changed original views or motion')
    result = dict(complete=True, accepted=False, dependency_sha256=pins,
        outputs_sha256={str(args.output.resolve()): digest(args.output)}, frames=21, dimensions=[640, 700],
        physical_duration_seconds=.4, presentation_milliseconds=durations,
        scope='Annotated engine-rendered RT0 gravity/translation calibration, 5x slow presentation plus end hold. Not waterfall/impact/splash or visual-feature acceptance.')
    with args.output.with_suffix('.json').open('x') as stream:
        json.dump(result, stream, indent=2); stream.write('\n')


if __name__ == '__main__':
    main()
