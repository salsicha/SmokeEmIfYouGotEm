"""Lossless labelled native-control animation; stationary water need not move."""
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
    parser.add_argument('--capture',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists():raise FileExistsError(args.output)
    capture=json.loads(args.capture.read_text());hashes=dict(capture['dependency_sha256'])
    hashes[str(args.capture.resolve())]=digest(args.capture);hashes[str(Path(__file__).resolve())]=digest(Path(__file__))
    font_path=Path('C:/Windows/Fonts/arial.ttf');hashes[str(font_path)]=digest(font_path)
    font=ImageFont.truetype(str(font_path),17)
    for row in capture['frames']:hashes[row['image']]=row['sha256']
    if not capture['complete'] or capture['accepted'] or any(digest(p)!=sha for p,sha in hashes.items()):
        raise ValueError('Unchanged complete native diagnostic views required')
    groups=[[row for row in capture['frames'] if row['control_index']==index] for index in range(3)]
    if any([r['frame'] for r in group]!=list(range(0,48,2)) for group in groups):
        raise ValueError('All native matching24-frame views required')
    labels=('STOCK: 2 substeps/frame','STOCK: 8 substeps/frame','ANALYTIC PLANE-RADIUS CONTROL')
    frames=[];content=[[] for _ in range(3)]
    for index in range(24):
        image=Image.new('RGB',(1440,374),(12,18,26));draw=ImageDraw.Draw(image)
        for panel,group in enumerate(groups):
            row=group[index]
            with Image.open(row['image']) as native:view=native.convert('RGB')
            if view.size!=(480,270):raise ValueError('Matching native view sizes required')
            image.paste(view,(panel*480,32));content[panel].append(np.asarray(view,float))
            draw.text((panel*480+8,7),labels[panel],font=font,fill=(239,244,248))
            draw.text((panel*480+8,310),f'field height error: {row["phi_minus_initial_mm"]:+.3f} mm',font=font,fill=(239,244,248))
            draw.text((panel*480+8,332),f'mesh - field: {row["mesh_minus_phi_mm"]:+.2f} mm',font=font,fill=(239,244,248))
        draw.text((8,354),f't={groups[0][index]["time_s"]:.3f}s | GOLD = analytic wet box / height | UNACCEPTED GEOMETRY DIAGNOSTIC - NOT FOAM',font=font,fill=(239,210,135))
        frames.append(image)
    durations=np.diff(np.rint(np.arange(25)*1000/12)).astype(int).tolist()
    args.output.mkdir();output=args.output/'feature.png'
    frames[0].save(output,format='PNG',save_all=True,append_images=frames[1:],duration=durations,loop=0,disposal=0,blend=0)
    with Image.open(output) as decoded:
        if decoded.n_frames!=24:raise ValueError('Incomplete animation')
        for index,frame in enumerate(frames):
            decoded.seek(index);np.testing.assert_array_equal(np.asarray(decoded.convert('RGB')),np.asarray(frame))
    changes=[[float(np.abs(b-a).mean()) for a,b in zip(panel,panel[1:])] for panel in content]
    if any(digest(p)!=sha for p,sha in hashes.items()):raise ValueError('Input changed during encoding')
    report=dict(complete=True,accepted=False,originals_unchanged=True,dependency_sha256=hashes,
        feature_sha256=digest(output),frame_count=24,width=1440,height=374,playback_fps=12,duration_seconds=sum(durations)/1000,
        simulation_fps=24,speed_multiplier=1,seamless_loop=False,lossless_decode_every_frame_verified=True,
        native_content_frame_changes=changes,labels_excluded_from_content_change_metric=True,
        scope='Native still-water controls with analytic annotations and opaque blue diagnostic shading. No claim of visible flow: stationary water is the required control. Tiny image changes do not prove physical motion. No foam, optical, wall collision or game acceptance; unchanged failed native meshes are deliberately shown.')
    with (args.output/'clip.json').open('x') as stream:json.dump(report,stream,indent=2)
    print('NATIVE_FLAT_ANIMATION_VERIFIED',output,report['feature_sha256'],flush=True)


if __name__=='__main__':main()
