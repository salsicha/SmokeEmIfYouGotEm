"""Lossless normal-speed animation of audited geometry with explicit field-volume labels."""
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
    parser.add_argument('--capture',type=Path,required=True);parser.add_argument('--fields',type=Path,action='append',required=True)
    parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    if args.output.exists():raise FileExistsError(args.output)
    capture=json.loads(args.capture.read_text());fields=[json.loads(p.read_text()) for p in args.fields]
    if len(fields)!=len(capture['labels']) or any(not r['complete'] or r['accepted'] for r in (capture,*fields)):raise ValueError('Matched unaccepted complete evidence required')
    if any(not r['explicit_wall_station_gate'] for r in fields):raise ValueError('Actual wall gate required')
    hashes=dict(capture['dependency_sha256'])
    for r in fields:hashes.update(r['dependency_sha256'])
    for p in (args.capture,Path(__file__),Path('C:/Windows/Fonts/arial.ttf'),*args.fields):hashes[str(p.resolve())]=digest(p)
    for r in capture['frames']:hashes[r['image']]=r['sha256']
    if any(digest(p)!=sha for p,sha in hashes.items()):raise ValueError('Pinned evidence changed')
    panels=[[r for r in capture['frames'] if r['panel']==i] for i in range(len(fields))]
    if any([r['frame'] for r in rows]!=list(range(145,192,2)) for rows in panels):raise ValueError('Matched24 frames required')
    if any(r['frames'][-1]['frame']!=192 for r in fields):raise ValueError('Actual late frame192 required')
    volumes=[next(v['volume_m3'] for v in r['frames'][-1]['reconstructed_volume'] if v['quadrature_subdivisions']==16) for r in fields]
    width=640*len(panels);font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',18);images=[];content=[[] for _ in panels]
    for index in range(24):
        image=Image.new('RGB',(width,476),(12,18,26));draw=ImageDraw.Draw(image)
        for panel,rows in enumerate(panels):
            r=rows[index]
            with Image.open(r['image']) as original:view=original.convert('RGB')
            if view.size!=(640,360):raise ValueError('Actual640x360 source required')
            content[panel].append(np.asarray(view,float));image.paste(view,(640*panel,32))
            draw.text((640*panel+10,6),capture['labels'][panel],font=font,fill=(240,244,248))
            draw.text((640*panel+10,400),f'late field volume (frame192): {volumes[panel]:.3f} cubic metres',font=font,fill=(230,235,245))
            draw.text((640*panel+10,425),f'sampled collider overlap: {r["maximum_sampled_collider_intrusion_m"]*1000:.2f} mm; NOT ACCEPTED',font=font,fill=(247,190,132))
        draw.text((10,447),f't={panels[0][index]["nominal_time_s"]:.3f}s | Explicit matched walls; cutaway view | Same sources / grid / optics | No foam | Not a seamless loop',font=font,fill=(247,210,135))
        images.append(image)
    durations=np.diff(np.rint(np.arange(25)*1000/12)).astype(int).tolist();args.output.mkdir();output=args.output/'feature.png'
    images[0].save(output,format='PNG',save_all=True,append_images=images[1:],duration=durations,loop=0,disposal=0,blend=0)
    with Image.open(output) as decoded:
        if decoded.n_frames!=24:raise ValueError('Incomplete APNG')
        for i,frame in enumerate(images):decoded.seek(i);np.testing.assert_array_equal(np.asarray(decoded.convert('RGB')),np.asarray(frame))
    changes=[[float(np.abs(b-a).mean()) for a,b in zip(panel,panel[1:])] for panel in content]
    if any(not all(v>0 for v in row) for row in changes):raise ValueError('Actual image-content motion missing')
    if any(digest(p)!=sha for p,sha in hashes.items()):raise ValueError('Evidence changed during encoding')
    report=dict(complete=True,accepted=False,originals_unchanged=True,dependency_sha256=hashes,feature_sha256=digest(output),labels=capture['labels'],
        frame_count=24,width=width,height=476,playback_fps=12,duration_seconds=sum(durations)/1000,
        source_fps=24,source_stride=2,speed_multiplier=1,first_frame=145,last_frame=191,seamless_loop=False,
        lossless_all_frames_decode_verified=True,adjacent_content_mean_absolute_changes=changes,labels_excluded_from_motion_check=True,
        frame192_reconstructed_volumes_m3=volumes,scope=__doc__,
        limitations='Volume is supplied-field integration, not conserved mass. Realistically coupled foam/froth/optics/collision/circulation/convergence and game integration remain open. No altered velocity/geometry, interpolated frames or gameFPS claim.')
    with (args.output/'clip.json').open('x') as stream:json.dump(report,stream,indent=2)
    print('MATCHED_FIELD_ANIMATION_VERIFIED',output,report['feature_sha256'],flush=True)


if __name__=='__main__':main()
