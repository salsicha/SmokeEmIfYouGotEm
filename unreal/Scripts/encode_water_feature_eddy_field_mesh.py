"""Lossless24-frame moving native-mesh comparison with failed contact disclosed."""
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
    for path in (args.capture,Path(__file__),Path('C:/Windows/Fonts/arial.ttf')):hashes[str(path.resolve())]=digest(path)
    font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',18)
    for row in capture['frames']:hashes[row['image']]=row['sha256']
    if not capture['complete'] or capture['accepted'] or any(digest(p)!=s for p,s in hashes.items()):
        raise ValueError('Complete unchanged actual renders required')
    panels=[[r for r in capture['frames'] if r['panel']==p] for p in ('particle','field')]
    if any([r['frame'] for r in panel]!=list(range(193,240,2)) for panel in panels):raise ValueError('Exact full native frame cohort required')
    images=[];content=[[],[]]
    for index in range(24):
        image=Image.new('RGB',(1280,482),(12,18,26));draw=ImageDraw.Draw(image)
        for panel,rows in enumerate(panels):
            row=rows[index]
            with Image.open(row['image']) as original:view=original.convert('RGB')
            if view.size!=(640,360):raise ValueError('Matching native640x360 view required')
            content[panel].append(np.asarray(view,float));image.paste(view,(panel*640,32))
            draw.text((panel*640+10,6),('PRESERVED PARTICLE MESH' if panel==0 else 'COPIED FLUID / OBSTACLE FIELD MESH (2x)'),font=font,fill=(240,244,248))
            gap=row['mesh_phi_absolute_vertical_gap_quantiles_m'][1]*1000
            draw.text((panel*640+10,400),f'median sampled mesh-field gap: {gap:.4f} mm | {row["columns_supported"]}/54 columns',font=font,fill=(240,244,248))
            draw.text((panel*640+10,425),f'sampled collider penetration: {row["maximum_sampled_authored_collider_intrusion_m"]*1000:.2f} mm',font=font,fill=(247,190,132))
        draw.text((10,454),f't={panels[0][index]["nominal_time_s"]:.3f}s | IDENTICAL MOTION, opaque geometry views | CONTACT FAILED; not foam / accepted eddy',font=font,fill=(247,210,135))
        images.append(image)
    duration=np.diff(np.rint(np.arange(25)*1000/12)).astype(int).tolist()
    args.output.mkdir();output=args.output/'feature.png'
    images[0].save(output,format='PNG',save_all=True,append_images=images[1:],duration=duration,loop=0,disposal=0,blend=0)
    with Image.open(output) as decoded:
        if decoded.n_frames!=24:raise ValueError('Incomplete APNG')
        for index,frame in enumerate(images):
            decoded.seek(index);np.testing.assert_array_equal(np.asarray(decoded.convert('RGB')),np.asarray(frame))
    changes=[[float(np.abs(b-a).mean()) for a,b in zip(panel,panel[1:])] for panel in content]
    if any(digest(p)!=s for p,s in hashes.items()):raise ValueError('Preserved inputs changed during encoding')
    report=dict(complete=True,accepted=False,originals_unchanged=True,dependency_sha256=hashes,
        feature_sha256=digest(output),frame_count=24,width=1280,height=482,playback_fps=12,duration_seconds=sum(duration)/1000,
        first_frame=193,last_frame=239,source_fps=24,source_stride=2,speed_multiplier=1,seamless_loop=False,
        lossless_all_frames_decode_verified=True,native_content_adjacent_mean_absolute_frame_changes=changes,
        labels_excluded_from_content_changes=True,source_evolution_clock=capture['source_evolution_clock'],
        scope='Actual matched native render comparison of the same preserved moving liquid; extraction only. Full liquid bounds fit fixed camera. Both panels are opaque geometry diagnostics with flat triangle normals, not measured water/foam optics. Per-frame collider and mesh/field measurements disclosed. Contact remains failed; no solver fix, hydraulic/foam/river/gameFPS acceptance.')
    with (args.output/'clip.json').open('x') as stream:json.dump(report,stream,indent=2)
    print('EDDY_FIELD_MESH_ANIMATION_VERIFIED',output,report['feature_sha256'],flush=True)


if __name__=='__main__':main()
