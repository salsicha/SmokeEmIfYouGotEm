"""Label and encode matching native renders; no scene/cache/motion modification."""
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
    parser.add_argument('--captures',type=Path,nargs=3,required=True)
    parser.add_argument('--audit',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists():raise FileExistsError(args.output)
    audit=json.loads(args.audit.read_text())
    if not audit['complete'] or audit['accepted'] or not audit['originals_unchanged']:
        raise ValueError('Complete unaccepted native comparison audit required')
    hashes=dict(audit['dependency_sha256'])
    if any(digest(path)!=sha for path,sha in hashes.items()):
        raise ValueError('Audited scene/cache/source changed before encoding')
    hashes[str(args.audit.resolve())]=digest(args.audit)
    capture=[]
    for path,control in zip(args.captures,audit['controls']):
        data=json.loads(path.read_text())
        if (not data['complete'] or data['physical_accuracy_accepted'] or data['visual_accuracy_accepted']
            or not data['secondary_particles_hidden'] or data['solid_clipped_diagnostic'] or data['view']!='eddy'
            or data['simulation_fps']!=24 or data['render_samples']!=4 or data['render_device']!='GPU'
            or [r['frame'] for r in data['frames']]!=list(range(193,240,2))
            or f'v6-m{2*control["subdivision"]}' not in data['source_blend']):
            raise ValueError('Matching complete unchanged native-mesh captures required')
        if digest(data['source_blend'])!=data['source_blend_sha256']:
            raise ValueError('Native scene changed during render')
        for name,sha in data['source_code_sha256'].items():
            source=Path(__file__).with_name(name).resolve()
            if digest(source)!=sha:raise ValueError('Renderer source changed')
            hashes[str(source)]=sha
        hashes[str(path.resolve())]=digest(path)
        for row in data['frames']:
            if digest(row['image'])!=row['sha256']:raise ValueError('Native image changed')
            hashes[row['image']]=row['sha256']
        capture.append(data)
    fonts=Path('C:/Windows/Fonts/arial.ttf')
    font=ImageFont.truetype(str(fonts),18)
    hashes[str(fonts)]=digest(fonts)
    frames=[]
    labels=['NORMAL: 2-8 substeps','HALF STEP: 4-16 substeps','QUARTER STEP: 8-32 substeps']
    for index in range(24):
        images=[]
        for data in capture:
            with Image.open(data['frames'][index]['image']) as img:images.append(img.convert('RGB'))
        if any(img.size!=(480,270) for img in images):raise ValueError('Exact same-size native views required')
        out=Image.new('RGB',(1440,348),(14,20,29));draw=ImageDraw.Draw(out)
        for panel,(img,label) in enumerate(zip(images,labels)):
            out.paste(img,(panel*480,38));draw.text((panel*480+12,9),label,font=font,fill=(237,242,248))
        frame=capture[0]['frames'][index]['frame']
        draw.text((12,319),f't={(frame-1)/24:.2f}s | LIQUID ONLY - NOT CONVERGED / NOT FOAM | Replay is not seamless',font=font,fill=(237,242,248))
        frames.append(out)
    durations=np.diff(np.rint(np.arange(25)*1000/12)).astype(int).tolist()
    args.output.mkdir(parents=True)
    output=args.output/'feature.png'
    frames[0].save(output,format='PNG',save_all=True,append_images=frames[1:],duration=durations,loop=0,disposal=0,blend=0)
    with Image.open(output) as decoded:
        if decoded.n_frames!=24:raise ValueError('Incomplete animation decode')
        for i,img in enumerate(frames):
            decoded.seek(i);np.testing.assert_array_equal(np.asarray(decoded.convert('RGB')),np.asarray(img))
    # Test liquid render content alone, so changing labels cannot fake motion.
    differences=[]
    for panel in range(3):
        images=[np.asarray(img.crop((panel*480,38,(panel+1)*480,308)),float) for img in frames]
        changes=[float(np.mean(np.abs(b-a))) for a,b in zip(images,images[1:])]
        if any(value==0 for value in changes):raise ValueError('Adjacent native content did not move')
        differences.append(changes)
    module=Path(__file__).resolve();hashes[str(module)]=digest(module)
    if any(digest(path)!=sha for path,sha in hashes.items()):raise ValueError('Input changed during encoding')
    report=dict(complete=True,accepted=False,frame_count=24,width=1440,height=348,playback_fps=12,
        duration_seconds=sum(durations)/1000,source_stride=2,first_frame=193,last_frame=239,
        native_content_adjacent_mean_absolute_frame_changes=differences,
        lossless_decode_every_frame_verified=True,originals_unchanged=True,dependency_sha256=hashes,
        feature_sha256=digest(output),speed_multiplier=1,seamless_loop=False,
        observed_native_mesh_defects=[dict(subdivision=control['subdivision'],
            zero_area_frames=[dict(frame=row['frame'],count=row['exact_zero_area_triangles'])
                for row in data['frames'] if row['exact_zero_area_triangles']],
            failed_edge_topology_frames=[dict(frame=row['frame'],topology=row['topology'])
                for row in data['frames'] if any(row['topology'].values())]) for data,control in zip(capture,audit['controls'])],
        model='Three fresh host-backed native FLIP eddy controls from the same serialized seed; timestep bounds only differ',
        limitations='Unchanged native mesh, authored studio materials/lights and fixed camera; no secondary particles, clipping, corrective displacement, retiming or claimed foam. 4 samples plus existing denoising are a low-cost geometry preview, not optical acceptance. Native integrator/cache clock discrepancy documented in audit; playback FPS is not game performance.')
    with (args.output/'clip.json').open('x') as stream:json.dump(report,stream,indent=2)
    print('TEMPORAL_COMPARISON_ANIMATION_VERIFIED',output,digest(output),flush=True)


if __name__=='__main__':main()
