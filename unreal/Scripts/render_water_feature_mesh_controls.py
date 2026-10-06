"""Matched audited native-field surfaces with preserved lab optics; unaccepted."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import time
import bpy
import numpy as np
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view


def digest(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--audit',type=Path,action='append',required=True)
    parser.add_argument('--label',action='append',required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    if args.output.exists():raise FileExistsError(args.output)
    if len(args.audit)!=len(args.label) or not 1<=len(args.label)<=3 or any(len(s)>58 for s in args.label):raise ValueError('One-to-three matched labeled controls required')
    audits=[json.loads(p.read_text()) for p in args.audit]
    if any(not a['complete'] or a['accepted'] for a in audits):raise ValueError('Unaccepted completed audits required')
    if any(a['controls'][0]['colliders']!=audits[0]['controls'][0]['colliders'] for a in audits):raise ValueError('Identical actual colliders required')
    if Path(bpy.data.filepath).resolve()!=Path(audits[-1]['controls'][0]['source_blend']).resolve():raise ValueError('Open exact last-control source with -b')
    hashes={}
    for a in audits:hashes.update(a['dependency_sha256']);hashes.update(a['outputs_sha256'])
    for p in (Path(__file__),*args.audit):hashes[str(p.resolve())]=digest(p)
    if any(digest(p)!=sha for p,sha in hashes.items()):raise ValueError('Pinned evidence changed')
    selected=[[r for r in a['rows'] if r['refinement']==2] for a in audits]
    if any([r['frame'] for r in rows]!=list(range(145,192,2)) for rows in selected):raise ValueError('Matched24-frame audit cohort required')
    scene=bpy.context.scene;domain=bpy.data.objects['Feature liquid'];domain.hide_render=True
    for ps in domain.particle_systems:ps.settings.render_type='NONE'
    camera=scene.camera;camera.location=(7.7,-7.,4.4)
    camera.rotation_euler=(Vector((3.,0.,.35))-camera.location).to_track_quat('-Z','Y').to_euler()
    camera.data.type='ORTHO';camera.data.ortho_scale=7.6
    scene.render.engine='CYCLES';scene.cycles.samples=24;scene.cycles.use_denoising=True
    scene.cycles.seed=0;scene.cycles.use_animated_seed=False
    prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='OPTIX';prefs.get_devices()
    if not any(d.type=='OPTIX' for d in prefs.devices):raise RuntimeError('OptiX device required')
    for d in prefs.devices:d.use=d.type=='OPTIX'
    scene.cycles.device='GPU';scene.render.threads_mode='FIXED';scene.render.threads=4
    scene.render.resolution_x=640;scene.render.resolution_y=360;scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGB'
    water=bpy.data.materials['Clear water IOR 1.333'];shader=water.node_tree.nodes['Principled BSDF']
    if shader.inputs['IOR'].default_value!=np.float32(1.333) or shader.inputs['Transmission Weight'].default_value!=1:raise ValueError('Preserved dielectric required')
    args.output.mkdir();rows=[];started=time.perf_counter()
    for index in range(24):
        for panel,selection in enumerate(selected):
            row=selection[index];positions=np.load(row['arrays']['positions'],allow_pickle=False);triangles=np.load(row['arrays']['triangles'],allow_pickle=False)
            mesh=bpy.data.meshes.new('Audited native field surface');mesh.from_pydata(positions.tolist(),[],triangles.tolist());mesh.update()
            obj=bpy.data.objects.new(mesh.name,mesh);scene.collection.objects.link(obj);mesh.materials.append(water);bpy.context.view_layer.update()
            check=np.empty(len(mesh.vertices)*3,np.float32);mesh.vertices.foreach_get('co',check)
            np.testing.assert_array_equal(check.reshape(-1,3),positions.astype(np.float32))
            if [tuple(p.vertices) for p in mesh.polygons]!=[tuple(map(int,t)) for t in triangles]:raise ValueError('Triangles changed')
            bounds=np.array(np.meshgrid(*zip(positions.min(0),positions.max(0)),indexing='ij')).reshape(3,-1).T
            projected=np.array([world_to_camera_view(scene,camera,Vector(p))[:] for p in bounds])
            if projected[:,:2].min()<.015 or projected[:,:2].max()>.985 or projected[:,2].min()<=0:raise ValueError('Camera clips liquid')
            path=args.output/f'panel-{panel}-{row["frame"]:04d}.png';scene.render.filepath=str(path.resolve())
            begin=time.perf_counter();bpy.ops.render.render(write_still=True)
            info=row['derived_mesh'];rows.append(dict(panel=panel,label=args.label[panel],frame=row['frame'],nominal_time_s=row['nominal_time_s'],
                image=str(path.resolve()),sha256=digest(path),render_elapsed_s=time.perf_counter()-begin,
                geometry_sha256=hashlib.sha256(positions.tobytes()+triangles.tobytes()).hexdigest(),
                renderer_coordinates_float32_bitexact=True,unchanged_triangles=True,camera_ndc_extent=[projected.min(0).tolist(),projected.max(0).tolist()],
                maximum_sampled_collider_intrusion_m=max(c[k]['deepest_inside_m'] for c in info['authored_solid_contact'].values() for k in ('vertices','triangle_centers')),
                geometry_closed_edge_gate=row['geometry_closed_edge_gate'],authored_sampled_contact_gate=row['authored_sampled_contact_gate']))
            bpy.data.objects.remove(obj,do_unlink=True);bpy.data.meshes.remove(mesh)
        print('MATCHED_FIELD_CONTROLS_RENDERED',selected[0][index]['frame'],flush=True)
    if any(digest(p)!=sha for p,sha in hashes.items()):raise ValueError('Evidence changed during render')
    report=dict(complete=True,accepted=False,originals_unchanged=True,dependency_sha256=hashes,frames=rows,labels=args.label,
        width=640,height=360,render_samples=24,render_device='GPU OptiX',denoised=True,fixed_seed=0,
        camera_position=list(camera.location),camera_rotation=list(camera.rotation_euler),ortho_scale=camera.data.ortho_scale,
        colliders=audits[0]['controls'][0]['colliders'],elapsed_s=time.perf_counter()-started,scope=__doc__,
        limitations='Actual copied2x fluid/obstacle zero-field meshes, flat triangle normals. Same actual solids/source scene/camera/lights/water shader, separately evolved controls. Authored cutaway-wall visibility is retained and disclosed in colliders. No particle projection, surface clipping, smoothing/displacement, secondary foam or retiming. Not accepted complete optics/CFD/physics or playable integration. Offline cost is not FPS.')
    with (args.output/'frames.json').open('x') as stream:json.dump(report,stream,indent=2)
    print('MATCHED_FIELD_RENDER_COMPLETE',len(rows),report['elapsed_s'],flush=True)


if __name__=='__main__':main()
