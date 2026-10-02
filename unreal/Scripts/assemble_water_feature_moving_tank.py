"""Annotate actual moving-tank engine views with physical time and exclusions."""
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
    for key in ('render', 'surface', 'output'):
        parser.add_argument('--'+key, type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists() or args.output.with_suffix('.json').exists():
        raise FileExistsError(args.output)
    render, surface = (json.loads(p.read_text()) for p in (args.render, args.surface))
    if len(render['frames']) != 21 or render['preview_only'] or not surface['complete']:
        raise ValueError('Full qualified 21-view control required')
    pins = {str(args.render.resolve()): digest(args.render), str(args.surface.resolve()): digest(args.surface),
            str(Path(__file__).resolve()): digest(__file__), **render['outputs_sha256'], **surface['outputs_sha256']}
    if any(digest(p) != sha for p, sha in pins.items()):
        raise ValueError('Physical/render evidence changed')
    times = np.load(surface['arrays']['times'], allow_pickle=False)
    font = ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf', 22)
    small = ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf', 16)
    frames = []
    for i, path in enumerate(render['frames']):
        with Image.open(path) as source:
            picture = source.convert('RGB')
        if picture.size != (760, 520):
            raise ValueError('Engine-view dimensions changed')
        canvas = Image.new('RGB', (760, 660), (15, 24, 34))
        canvas.paste(picture, (0, 76)); draw = ImageDraw.Draw(canvas)
        draw.text((18, 7), 'Deforming-tank calibration: computed 3D liquid', font=font, fill=(231, 241, 249))
        draw.text((18, 38), 'NOT an accepted standing wave or river feature', font=small, fill=(251, 207, 137))
        draw.text((18, 602), f'Physical t = {times[i]:.2f} s     1.0 x 0.6 m tank     orange = material-node diagnostics',
                  font=small, fill=(230, 240, 250))
        draw.text((18, 632), '5x slow + end hold. No through-flow, breaking, foam, viscosity or surface tension.',
                  font=small, fill=(173, 191, 208))
        frames.append(canvas)
    frames[0].save(args.output, format='PNG', save_all=True, append_images=frames[1:],
                   duration=[100]*20+[500], loop=1, disposal=0, blend=0)
    with Image.open(args.output) as saved:
        if saved.n_frames != 21 or saved.size != (760, 660) or saved.info.get('loop') != 1:
            raise ValueError('Stored animation coverage changed')
        durations = []
        for i in range(saved.n_frames):
            saved.seek(i); durations.append(saved.info['duration'])
            if not np.array_equal(np.asarray(saved.convert('RGB')), np.asarray(frames[i])):
                raise ValueError('Stored APNG differs from annotated engine view')
    if any(digest(p) != sha for p, sha in pins.items()):
        raise ValueError('Assembly modified physical evidence')
    result = dict(complete=True, accepted=False, dependency_sha256=pins,
        outputs_sha256={str(args.output.resolve()): digest(args.output)}, frames=21,
        dimensions=[760, 660], physical_duration_seconds=.4, presentation_milliseconds=durations,
        scope='Annotated engine views of independently checked preliminary moving tank. Not standing-wave/feature or visual acceptance.')
    with args.output.with_suffix('.json').open('x') as stream:
        json.dump(result, stream, indent=2); stream.write('\n')


if __name__ == '__main__':
    main()
