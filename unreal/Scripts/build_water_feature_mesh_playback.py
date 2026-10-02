"""Self-contained audited-mesh playback, explicitly NOT a new CFD solver scene."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import bpy
import numpy as np
from mathutils import Vector


def digest(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--audit',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    if args.output.exists():raise FileExistsError(args.output)
    audit=json.loads(args.audit.read_text());source=Path(audit['controls'][0]['source_blend']).resolve()
    if not audit['complete'] or audit['accepted'] or Path(bpy.data.filepath).resolve()!=source:raise ValueError('Open exact audited source with -b')
    hashes={**audit['dependency_sha256'],**audit['outputs_sha256']}
    for p in (Path(__file__),args.audit):hashes[str(p.resolve())]=digest(p)
    if any(digest(p)!=sha for p,sha in hashes.items()):raise ValueError('Source changed')
    rows=[r for r in audit['rows'] if r['refinement']==2]
    if [r['frame'] for r in rows]!=list(range(145,192,2)):raise ValueError('Full24-frame cohort required')
    args.output.mkdir();scene=bpy.context.scene;domain=bpy.data.objects['Feature liquid']
    # Redirect before removing the in-memory solver object. Original cache and
    # source files stay hash-pinned. Playback uses embedded audited meshes only.
    domain.modifiers[0].domain_settings.cache_directory=str((args.output/'unused-playback-cache').resolve())
    bpy.data.objects.remove(domain,do_unlink=True);del domain
    for obj in list(bpy.data.objects):
        fluid=[m for m in obj.modifiers if m.type=='FLUID']
        if any(m.fluid_type=='FLOW' for m in fluid):bpy.data.objects.remove(obj,do_unlink=True);continue
        for modifier in fluid:obj.modifiers.remove(modifier)
        if obj.hide_render:obj.hide_set(True)
    water=bpy.data.materials['Clear water IOR 1.333'];embedded=[]
    for row in rows:
        positions=np.load(row['arrays']['positions'],allow_pickle=False);triangles=np.load(row['arrays']['triangles'],allow_pickle=False)
        name=f'Audited liquid frame {row["frame"]:04d}';mesh=bpy.data.meshes.new(name);mesh.from_pydata(positions.tolist(),[],triangles.tolist());mesh.update()
        obj=bpy.data.objects.new(name,mesh);scene.collection.objects.link(obj);mesh.materials.append(water);obj['audited_source_frame']=row['frame']
        check=np.empty(len(mesh.vertices)*3,np.float32);mesh.vertices.foreach_get('co',check);np.testing.assert_array_equal(check.reshape(-1,3),positions.astype(np.float32))
        if [tuple(p.vertices) for p in mesh.polygons]!=[tuple(map(int,t)) for t in triangles]:raise ValueError('Embedded triangles differ')
        for field in ('hide_viewport','hide_render'):
            for frame,value in ((1,True),(row['frame'],False),(row['frame']+2,True)):
                setattr(obj,field,value);obj.keyframe_insert(field,frame=frame)
        for layer in obj.animation_data.action.layers:
            for strip in layer.strips:
                for bag in strip.channelbags:
                    for curve in bag.fcurves:
                        for key in curve.keyframe_points:key.interpolation='CONSTANT'
        embedded.append(dict(frame=row['frame'],object_name=name,arrays=row['arrays']))
    camera=scene.camera;camera.location=(7.7,-7.,4.4);camera.rotation_euler=(Vector((3.,0.,.35))-camera.location).to_track_quat('-Z','Y').to_euler()
    camera.data.type='ORTHO';camera.data.ortho_scale=7.6
    scene.frame_start=145;scene.frame_end=192;scene.render.fps=24;scene.frame_set(145)
    scene.render.engine='CYCLES';scene.cycles.samples=24;scene.cycles.use_denoising=True;scene.cycles.seed=0;scene.cycles.use_animated_seed=False
    scene.render.resolution_x=640;scene.render.resolution_y=360;scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGB'
    scene['accepted_feature']=False;scene['playback_scope']='Embedded field-derived geometry at12 sampled frames/s, held for two24fps timeline frames. NOT CFD or foam. Unaccepted corners/hydraulics/optics.'
    scene['preserved_CFD_source']=str(source)
    if any(m.type=='FLUID' for obj in bpy.data.objects for m in obj.modifiers):raise ValueError('Playback retains active fluid dependency')
    if bpy.data.libraries or any(i.source=='FILE' and i.filepath for i in bpy.data.images):raise ValueError('Unexpected external playback library/image')
    bpy.context.preferences.filepaths.save_version=0;output=args.output/'feature.blend'
    bpy.ops.wm.save_as_mainfile(filepath=str(output.resolve()),compress=True)
    if any(digest(p)!=sha for p,sha in hashes.items()):raise ValueError('Playback packaging changed originals')
    report=dict(complete=True,accepted=False,originals_unchanged=True,dependency_sha256=hashes,blend=str(output.resolve()),
        blend_sha256=digest(output),blend_bytes=output.stat().st_size,embedded_frames=embedded,first_frame=145,last_frame=192,
        timeline_fps=24,sampled_motion_fps=12,stepwise_visibility_not_interpolation=True,active_fluid_modifiers=0,external_libraries_images=0,
        colliders=audit['controls'][0]['colliders'],scope=__doc__)
    with (args.output/'playback.json').open('x') as stream:json.dump(report,stream,indent=2)
    print('EMBEDDED_FIELD_PLAYBACK_SAVED',output,report['blend_bytes'],flush=True)


if __name__=='__main__':main()
