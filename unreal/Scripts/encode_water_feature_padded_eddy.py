"""Lossless two-second real-time comparison; disclose remaining contact failure."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont


def digest(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--capture',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists():raise FileExistsError(args.output)
    capture=json.loads(args.capture.read_text());hashes=dict(capture['dependency_sha256'])
    for p in (args.capture,Path(__file__),Path('C:/Windows/Fonts/arial.ttf')):hashes[str(p.resolve())]=digest(p)
    for row in capture['frames']:hashes[row['image']]=row['sha256']
    if not capture['complete'] or capture['accepted'] or any(digest(p)!=sha for p,sha in hashes.items()):
        raise ValueError('Complete unchanged actual captures required')
    panels=[[r for r in capture['frames'] if r['panel']==p] for p in ('original','padded')]
    if any([r['frame'] for r in rows]!=list(range(145,192,2)) for rows in panels):
        raise ValueError('Exact matched24-frame cohort required')
    font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',18);images=[];content=[[],[]]
    for index in range(24):
        image=Image.new('RGB',(1280,476),(12,18,26));draw=ImageDraw.Draw(image)
        for panel,rows in enumerate(panels):
            row=rows[index]
            with Image.open(row['image']) as original:view=original.convert('RGB')
            if view.size!=(640,360):raise ValueError('Actual matching640x360 views required')
            content[panel].append(np.asarray(view,float));image.paste(view,(640*panel,32))
            draw.text((640*panel+10,6),'ORIGINAL BOUNDARY' if panel==0 else '3 EXTRA GRID CELLS BELOW UNCHANGED BED',font=font,fill=(240,244,248))
            draw.text((640*panel+10,400),f'sampled mesh intrusion into bed: {row["floor_intrusion_m"]*1000:.2f} mm',font=font,fill=(230,235,245))
            draw.text((640*panel+10,425),f'worst collider intrusion: {row["maximum_sampled_collider_intrusion_m"]*1000:.2f} mm; not accepted',font=font,fill=(247,190,132))
        draw.text((10,447),f't={panels[0][index]["nominal_time_s"]:.3f}s | Different evolved liquids; copied field meshes; no foam; not a seamless loop',font=font,fill=(247,210,135))
        images.append(image)
    # Retain one-to-one physical playback: every second24fps simulation frame
    # becomes one12fps animation frame. No retiming or fabricated interpolation.
    duration=np.diff(np.rint(np.arange(25)*1000/12)).astype(int).tolist()
    args.output.mkdir();output=args.output/'feature.png'
    images[0].save(output,format='PNG',save_all=True,append_images=images[1:],duration=duration,loop=0,disposal=0,blend=0)
    with Image.open(output) as decoded:
        if decoded.n_frames!=24:raise ValueError('Incomplete APNG')
        for index,frame in enumerate(images):
            decoded.seek(index);np.testing.assert_array_equal(np.asarray(decoded.convert('RGB')),np.asarray(frame))
    changes=[[float(np.abs(b-a).mean()) for a,b in zip(panel,panel[1:])] for panel in content]
    if any(not all(v>0 for v in panel) for panel in changes):raise ValueError('Motion absent from actual render content')
    if any(digest(p)!=sha for p,sha in hashes.items()):raise ValueError('Pinned inputs changed during encoding')
    report=dict(complete=True,accepted=False,originals_unchanged=True,dependency_sha256=hashes,
        feature_sha256=digest(output),frame_count=24,width=1280,height=476,playback_fps=12,
        duration_seconds=sum(duration)/1000,first_frame=145,last_frame=191,source_fps=24,source_stride=2,
        speed_multiplier=1,seamless_loop=False,lossless_all_frames_decode_verified=True,
        adjacent_content_mean_absolute_changes=changes,labels_excluded_from_motion_check=True,
        scope='Actual separately evolved native FLIP liquids in identical synthetic flume, same75mm grid and physical settings except added computational space below bed. Copied2x zero-field extraction; water IOR1.333/transmission/absorption unchanged. Flat triangle normals. No particles or collision clipping, no invented foam/froth; hydraulic/contact/optical/game acceptance remains open.')
    with (args.output/'clip.json').open('x') as stream:json.dump(report,stream,indent=2)
    print('PADDED_EDDY_ANIMATION_VERIFIED',output,report['feature_sha256'],flush=True)


if __name__=='__main__':main()
