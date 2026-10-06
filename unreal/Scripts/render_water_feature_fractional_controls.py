"""Three actual evolved eddy liquids; matched optics, no cosmetic contact repair."""
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
    for name in ('standard','fractional','zero','output'):parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    if args.output.exists():raise FileExistsError(args.output)
    paths=(args.standard,args.fractional,args.zero);audits=[json.loads(p.read_text()) for p in paths]
    if any(not a['complete'] or a['accepted'] for a in audits):raise ValueError('Complete unaccepted audits required')
    if any(a['controls'][0]['colliders']!=audits[0]['controls'][0]['colliders'] for a in audits):
        raise ValueError('Identical authored colliders required')
    hashes={}
    for a in audits:hashes.update(a['dependency_sha256']);hashes.update(a['outputs_sha256'])
    for p in (Path(__file__),*paths):hashes[str(p.resolve())]=digest(p)
    if any(digest(p)!=sha for p,sha in hashes.items()):raise ValueError('Pinned evidence changed')
    source=Path(bpy.data.filepath).resolve()
    if source!=Path(audits[2]['controls'][0]['source_blend']).resolve():raise ValueError('Start with exact zero-control source')
    scene=bpy.context.scene;domain=bpy.data.objects['Feature liquid'];domain.hide_render=True
    for system in domain.particle_systems:system.settings.render_type='NONE'
    camera=scene.camera;camera.location=(7.7,-7.,4.4)
    camera.rotation_euler=(Vector((3.,0.,.35))-camera.location).to_track_quat('-Z','Y').to_euler()
    camera.data.type='ORTHO';camera.data.ortho_scale=7.6
    scene.render.engine='CYCLES';scene.cycles.samples=24;scene.cycles.use_denoising=True
    scene.cycles.seed=0;scene.cycles.use_animated_seed=False
    prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='OPTIX';prefs.get_devices()
    if not any(d.type=='OPTIX' for d in prefs.devices):raise RuntimeError('OptiX device required')
    for device in prefs.devices:device.use=device.type=='OPTIX'
    scene.cycles.device='GPU';scene.render.threads_mode='FIXED';scene.render.threads=4
    scene.render.resolution_x=640;scene.render.resolution_y=360;scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGB'
    water=bpy.data.materials['Clear water IOR 1.333'];shader=water.node_tree.nodes['Principled BSDF']
    if shader.inputs['IOR'].default_value!=np.float32(1.333) or shader.inputs['Transmission Weight'].default_value!=1:
        raise ValueError('Unchanged transparent water required')
    selected=[[r for r in a['rows'] if r['refinement']==2] for a in audits]
    if any([r['frame'] for r in rows]!=list(range(145,192,2)) for rows in selected):raise ValueError('Matched24-frame cohort required')
    args.output.mkdir();rows=[];started=time.perf_counter()
    for index in range(24):
        for panel,selection in zip(('standard','fractional','zero'),selected):
            row=selection[index];positions=np.load(row['arrays']['positions'],allow_pickle=False)
            triangles=np.load(row['arrays']['triangles'],allow_pickle=False)
            mesh=bpy.data.meshes.new('Native field surface '+panel);mesh.from_pydata(positions.tolist(),[],triangles.tolist());mesh.update()
            obj=bpy.data.objects.new(mesh.name,mesh);scene.collection.objects.link(obj);mesh.materials.append(water)
            bpy.context.view_layer.update()
            readback=np.empty(len(mesh.vertices)*3,np.float32);mesh.vertices.foreach_get('co',readback)
            np.testing.assert_array_equal(readback.reshape(-1,3),positions.astype(np.float32))
            if [tuple(p.vertices) for p in mesh.polygons]!=[tuple(map(int,t)) for t in triangles]:raise ValueError('Faces changed')
            bounds=np.array(np.meshgrid(*zip(positions.min(0),positions.max(0)),indexing='ij')).reshape(3,-1).T
            projected=np.array([world_to_camera_view(scene,camera,Vector(p))[:] for p in bounds])
            if projected[:,:2].min()<.015 or projected[:,:2].max()>.985 or projected[:,2].min()<=0:raise ValueError('Camera clips liquid')
            path=args.output/f'{panel}-{row["frame"]:04d}.png';scene.render.filepath=str(path.resolve())
            begin=time.perf_counter();bpy.ops.render.render(write_still=True);info=row['derived_mesh']
            rows.append(dict(panel=panel,frame=row['frame'],nominal_time_s=row['nominal_time_s'],image=str(path.resolve()),
                sha256=digest(path),render_elapsed_s=time.perf_counter()-begin,
                geometry_sha256=hashlib.sha256(positions.tobytes()+triangles.tobytes()).hexdigest(),
                renderer_coordinates_float32_bitexact=True,unchanged_triangles=True,
                camera_ndc_extent=[projected.min(0).tolist(),projected.max(0).tolist()],
                maximum_sampled_collider_intrusion_m=max(c[k]['deepest_inside_m'] for c in info['authored_solid_contact'].values()
                    for k in ('vertices','triangle_centers')),geometry_closed_edge_gate=row['geometry_closed_edge_gate'],
                authored_sampled_contact_gate=row['authored_sampled_contact_gate']))
            bpy.data.objects.remove(obj,do_unlink=True);bpy.data.meshes.remove(mesh)
        print('FRACTIONAL_THREE_CONTROLS_RENDERED',selected[0][index]['frame'],flush=True)
    if any(digest(p)!=sha for p,sha in hashes.items()):raise ValueError('Evidence changed during render')
    report=dict(complete=True,accepted=False,originals_unchanged=True,dependency_sha256=hashes,frames=rows,
        source=str(source),width=640,height=360,render_samples=24,render_device='GPU OptiX',denoised=True,fixed_seed=0,
        camera_position=list(camera.location),camera_rotation=list(camera.rotation_euler),ortho_scale=camera.data.ortho_scale,
        elapsed_s=time.perf_counter()-started,scope=__doc__,
        limitations='Same75mm grid, padded domain, authored solids, sources, FLIP and optics. Standard vs native fractional default0.5-cell clearance vs zero clearance. Native field-derived2x meshes, flat normals, no clipping or fake foam. Implicit boundary convention is not equivalent between standard and fractional; comparison is not isolated to pressure coefficients. No accepted optics/hydraulics/collision/game integration. Offline cost is not FPS.')
    with (args.output/'frames.json').open('x') as stream:json.dump(report,stream,indent=2)
    print('FRACTIONAL_RENDER_COMPLETE',len(rows),report['elapsed_s'],flush=True)


if __name__=='__main__':main()
