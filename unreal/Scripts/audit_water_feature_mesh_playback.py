"""Reopen saved scene, verify EVERY embedded pose/subframe, render three views."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import bpy
import numpy as np


def digest(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    if args.output.exists():raise FileExistsError(args.output)
    manifest=json.loads(args.manifest.read_text());source=Path(manifest['blend'])
    if not manifest['complete'] or manifest['accepted'] or Path(bpy.data.filepath).resolve()!=source.resolve():raise ValueError('Open exact saved playback')
    hashes={**manifest['dependency_sha256'],str(source.resolve()):manifest['blend_sha256']}
    for p in (Path(__file__),args.manifest):hashes[str(p.resolve())]=digest(p)
    if any(digest(p)!=sha for p,sha in hashes.items()):raise ValueError('Pinned source changed')
    scene=bpy.context.scene
    if scene['accepted_feature'] or (scene.frame_start,scene.frame_end,scene.render.fps)!=(145,192,24):raise ValueError('Playback scope/timing changed')
    if any(m.type=='FLUID' for o in bpy.data.objects for m in o.modifiers) or bpy.data.libraries or any(i.source=='FILE' and i.filepath for i in bpy.data.images):raise ValueError('External/runtime fluid dependency remains')
    objects=[bpy.data.objects[r['object_name']] for r in manifest['embedded_frames']];checks=[]
    for row,obj in zip(manifest['embedded_frames'],objects):
        positions=np.load(row['arrays']['positions'],allow_pickle=False);triangles=np.load(row['arrays']['triangles'],allow_pickle=False)
        check=np.empty(len(obj.data.vertices)*3,np.float32);obj.data.vertices.foreach_get('co',check)
        np.testing.assert_array_equal(check.reshape(-1,3),positions.astype(np.float32))
        if [tuple(p.vertices) for p in obj.data.polygons]!=[tuple(map(int,t)) for t in triangles]:raise ValueError('Saved faces changed')
        for offset in (0,.5,1,1.5):
            value=row['frame']+offset;scene.frame_set(int(value),subframe=value-int(value))
            if [o.name for o in objects if not o.hide_render]!=[obj.name]:raise ValueError('Saved render visibility fails')
            if [o.name for o in objects if not o.hide_viewport]!=[obj.name]:raise ValueError('Saved viewport visibility fails')
            checks.append(dict(source_frame=row['frame'],timeline_frame=value,sole_visible_object=obj.name))
    args.output.mkdir();prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='OPTIX';prefs.get_devices()
    if not any(d.type=='OPTIX' for d in prefs.devices):raise RuntimeError('OptiX device required')
    for d in prefs.devices:d.use=d.type=='OPTIX'
    scene.cycles.device='GPU';scene.render.threads_mode='FIXED';scene.render.threads=4;images=[]
    for frame in (145,169,191):
        scene.frame_set(frame);path=args.output/f'frame-{frame:04d}.png';scene.render.filepath=str(path.resolve());bpy.ops.render.render(write_still=True)
        images.append(dict(frame=frame,path=str(path.resolve()),sha256=digest(path)))
    if any(digest(p)!=sha for p,sha in hashes.items()):raise ValueError('Source changed during reopened audit')
    report=dict(complete=True,accepted=False,originals_unchanged=True,dependency_sha256=hashes,all_saved_poses_float32_bitexact=True,
        all_saved_triangles_unchanged=True,visibility_subframe_checks=checks,active_fluid_modifiers=0,external_libraries_images=0,images=images,scope=__doc__,
        caveats='Self-contained saved geometry playback only. Discrete12fps sample motion, not interpolated solver evolution, conserved mass or accepted optics/physics. Original CFD caches remain preserved separately.')
    with (args.output/'audit.json').open('x') as stream:json.dump(report,stream,indent=2)
    print('REOPENED_FIELD_PLAYBACK_VERIFIED',len(checks),len(images),flush=True)


if __name__=='__main__':main()
