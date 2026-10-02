"""Lossless real-time three-control comparison, with honest volume/contact labels."""
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
    for name in ('capture','default-volume','zero-volume','output'):parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists():raise FileExistsError(args.output)
    capture=json.loads(args.capture.read_text());default=json.loads(args.default_volume.read_text());zero=json.loads(args.zero_volume.read_text())
    if any(not r['complete'] or r['accepted'] for r in (capture,default,zero)):raise ValueError('Unaccepted completed evidence required')
    if not default['section_units_qualified'] or not zero['section_units_qualified']:raise ValueError('Qualified units required')
    hashes=dict(capture['dependency_sha256'])
    for r in (default,zero):hashes.update(r['dependency_sha256'])
    for p in (args.capture,args.default_volume,args.zero_volume,Path(__file__),Path('C:/Windows/Fonts/arial.ttf')):
        hashes[str(p.resolve())]=digest(p)
    for row in capture['frames']:hashes[row['image']]=row['sha256']
    if any(digest(p)!=sha for p,sha in hashes.items()):raise ValueError('Evidence changed')
    def last_volume(control):
        row=control['frames'][-1]
        if row['frame']!=192:raise ValueError('Late native frame192 required')
        return next(v['volume_m3'] for v in row['reconstructed_volume'] if v['quadrature_subdivisions']==16)
    volumes=[last_volume(default['controls'][0]),last_volume(default['controls'][1]),last_volume(zero['controls'][1])]
    if volumes[0]!=last_volume(zero['controls'][0]):raise ValueError('Standard reference changed')
    panels=[[r for r in capture['frames'] if r['panel']==p] for p in ('standard','fractional','zero')]
    if any([r['frame'] for r in rows]!=list(range(145,192,2)) for rows in panels):raise ValueError('Matched24frames required')
    titles=('STANDARD PADDED FLIP','FRACTIONAL: 37.5 mm PARTICLE CLEARANCE','FRACTIONAL: ZERO ARTIFICIAL CLEARANCE')
    font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',18);images=[];content=[[],[],[]]
    for index in range(24):
        image=Image.new('RGB',(1920,476),(12,18,26));draw=ImageDraw.Draw(image)
        for panel,rows in enumerate(panels):
            row=rows[index]
            with Image.open(row['image']) as original:view=original.convert('RGB')
            if view.size!=(640,360):raise ValueError('Actual640x360 views required')
            content[panel].append(np.asarray(view,float));image.paste(view,(640*panel,32))
            draw.text((640*panel+10,6),titles[panel],font=font,fill=(240,244,248))
            draw.text((640*panel+10,400),f'late field volume (frame192): {volumes[panel]:.3f} cubic metres',font=font,fill=(230,235,245))
            draw.text((640*panel+10,425),f'sampled rock overlap: {row["maximum_sampled_collider_intrusion_m"]*1000:.2f} mm; NOT ACCEPTED',font=font,fill=(247,190,132))
        draw.text((10,447),f't={panels[0][index]["nominal_time_s"]:.3f}s | Same authored solids / sources / grid / optics; different native boundary behavior | No foam | Not a seamless loop',font=font,fill=(247,210,135))
        images.append(image)
    duration=np.diff(np.rint(np.arange(25)*1000/12)).astype(int).tolist();args.output.mkdir();output=args.output/'feature.png'
    images[0].save(output,format='PNG',save_all=True,append_images=images[1:],duration=duration,loop=0,disposal=0,blend=0)
    with Image.open(output) as decoded:
        if decoded.n_frames!=24:raise ValueError('IncompleteAPNG')
        for index,frame in enumerate(images):
            decoded.seek(index);np.testing.assert_array_equal(np.asarray(decoded.convert('RGB')),np.asarray(frame))
    changes=[[float(np.abs(b-a).mean()) for a,b in zip(panel,panel[1:])] for panel in content]
    if any(not all(v>0 for v in panel) for panel in changes):raise ValueError('Actual content motion absent')
    if any(digest(p)!=sha for p,sha in hashes.items()):raise ValueError('Evidence changed during encode')
    report=dict(complete=True,accepted=False,originals_unchanged=True,dependency_sha256=hashes,feature_sha256=digest(output),
        frame_count=24,width=1920,height=476,playback_fps=12,duration_seconds=sum(duration)/1000,
        first_frame=145,last_frame=191,source_fps=24,source_stride=2,speed_multiplier=1,seamless_loop=False,
        lossless_all_frames_decode_verified=True,adjacent_content_mean_absolute_changes=changes,labels_excluded_from_motion_check=True,
        frame192_reconstructed_volumes_m3=volumes,
        scope='Three separately evolved nativeFLIP controls, matched syntheticflume and optics. Actual copied2x field meshes; unaccepted. Field-integrated volume is not conserved mass. No clipping, fake foam, altered velocities or retiming. No accepted fullfeature/game/20FPS claim.')
    with (args.output/'clip.json').open('x') as stream:json.dump(report,stream,indent=2)
    print('FRACTIONAL_ANIMATION_VERIFIED',output,report['feature_sha256'],flush=True)


if __name__=='__main__':main()
