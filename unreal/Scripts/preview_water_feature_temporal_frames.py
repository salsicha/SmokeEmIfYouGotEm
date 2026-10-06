"""Extract verified opening/middle/end animation frames for visual QA."""
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--clip',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    report=json.loads(args.clip.read_text())
    source=args.clip.parent/'feature.png'
    before=hashlib.sha256(source.read_bytes()).hexdigest()
    if (before!=report['feature_sha256'] or not report['complete'] or report['accepted']
            or report['frame_count']!=24 or args.output.exists()):
        raise ValueError('Exact unaccepted native comparison and fresh QA destination required')
    args.output.mkdir(parents=True)
    with Image.open(source) as image:
        if image.n_frames!=24:raise ValueError('Incomplete animation')
        for index in (0,12,23):
            image.seek(index)
            path=args.output/f'frame-{index:02d}.png'
            image.convert('RGB').save(path)
            print('TEMPORAL_VISUAL_QA_FRAME',path,flush=True)
    if hashlib.sha256(source.read_bytes()).hexdigest()!=before:
        raise ValueError('Animation changed during QA extraction')


if __name__=='__main__':main()
