"""Matched actual views of preserved particle mesh and copied-field extraction.

Opaque shading exposes geometry; it is deliberately NOT accepted water optics.
No foam, artificial motion, displaced vertices, smoothing or source-cache edits.
"""
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
sys.path.insert(0,str(Path(__file__).resolve().parent))
from water_feature_geometry import world_coordinates


def digest(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--audit',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--cpu',action='store_true')
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    if args.output.exists():raise FileExistsError(args.output)
    audit=json.loads(args.audit.read_text());source=Path(bpy.data.filepath).resolve()
    if not audit['complete'] or audit['accepted'] or source!=Path(audit['source_blend']).resolve():
        raise ValueError('Complete unaccepted preserved extraction required')
    hashes={**audit['dependency_sha256'],**audit['outputs_sha256']}
    hashes[str(args.audit.resolve())]=digest(args.audit);hashes[str(Path(__file__).resolve())]=digest(Path(__file__))
    if any(digest(p)!=sha for p,sha in hashes.items()):raise ValueError('Pinned extraction changed before render')
    scene=bpy.context.scene;domain=bpy.data.objects['Feature liquid']
    domain.modifiers[0].domain_settings.cache_directory=str(source.parent/'cache')
    domain.hide_render=True
    for system in domain.particle_systems:system.settings.render_type='NONE'
    camera=scene.camera;camera.location=(3.,-5.,8.)
    camera.rotation_euler=(Vector((3.,0.,.3))-camera.location).to_track_quat('-Z','Y').to_euler()
    camera.data.type='ORTHO';camera.data.ortho_scale=7.2
    scene.render.engine='CYCLES';scene.cycles.samples=16;scene.cycles.use_denoising=True
    scene.cycles.seed=0;scene.cycles.use_animated_seed=False
    if args.cpu:scene.cycles.device='CPU'
    else:
        prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='OPTIX';prefs.get_devices()
        if not any(d.type=='OPTIX' for d in prefs.devices):raise RuntimeError('No OptiX device; choose --cpu explicitly')
        for device in prefs.devices:device.use=device.type=='OPTIX'
        scene.cycles.device='GPU'
    scene.render.threads_mode='FIXED';scene.render.threads=4
    scene.render.resolution_x=640;scene.render.resolution_y=360;scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGB'
    water=bpy.data.materials.new('Opaque field geometry diagnostic - not water optics');water.use_nodes=True
    shader=water.node_tree.nodes.get('Principled BSDF');shader.inputs['Base Color'].default_value=(.025,.25,.36,1)
    shader.inputs['Roughness'].default_value=.38;shader.inputs['Metallic'].default_value=0
    shader.inputs['Transmission Weight'].default_value=0
    frames=[r for r in audit['rows'] if r['refinement']==2]
    if [r['frame'] for r in frames]!=list(range(193,240,2)):raise ValueError('Complete matching24-frame coverage required')
    args.output.mkdir();rows=[];started=time.perf_counter()
    for row in frames:
        frame=row['frame'];scene.frame_set(frame)
        native=domain.evaluated_get(bpy.context.evaluated_depsgraph_get());original=native.to_mesh()
        try:
            original.calc_loop_triangles()
            old_vertices=world_coordinates([v.co[:] for v in original.vertices],native.matrix_world)
            old_triangles=np.array([t.vertices[:] for t in original.loop_triangles],np.int64)
        finally:native.to_mesh_clear()
        old=row['original_particle_mesh']
        if len(old_vertices)!=old['vertex_count'] or len(old_triangles)!=old['triangle_count']:
            raise ValueError('Unchanged native particle mesh coverage required')
        for panel,positions,triangles in (
                ('particle',old_vertices,old_triangles),
                ('field',np.load(row['arrays']['positions'],allow_pickle=False),np.load(row['arrays']['triangles'],allow_pickle=False))):
            mesh=bpy.data.meshes.new('Unchanged diagnostic '+panel);mesh.from_pydata(positions.tolist(),[],triangles.tolist());mesh.update()
            obj=bpy.data.objects.new(mesh.name,mesh);scene.collection.objects.link(obj);mesh.materials.append(water)
            bpy.context.view_layer.update()
            readback=np.empty(len(mesh.vertices)*3,np.float32);mesh.vertices.foreach_get('co',readback)
            np.testing.assert_array_equal(readback.reshape(-1,3),positions.astype(np.float32))
            if [tuple(p.vertices) for p in mesh.polygons]!=[tuple(map(int,t)) for t in triangles]:
                raise ValueError('Native/derived faces changed in actual render')
            bounds=np.array(np.meshgrid(*zip(positions.min(0),positions.max(0)),indexing='ij')).reshape(3,-1).T
            projected=np.array([world_to_camera_view(scene,camera,Vector(point))[:] for point in bounds])
            if projected[:,:2].min()<.03 or projected[:,:2].max()>.97 or projected[:,2].min()<=0:
                raise ValueError('Full liquid bounding box does not fit fixed camera with3percent margin')
            path=args.output/f'{panel}-{frame:04d}.png';scene.render.filepath=str(path.resolve())
            begin=time.perf_counter();bpy.ops.render.render(write_still=True)
            info=row['original_particle_mesh'] if panel=='particle' else row['derived_mesh']
            rows.append(dict(frame=frame,panel=panel,image=str(path.resolve()),sha256=digest(path),
                nominal_time_s=row['nominal_time_s'],native_cache_time_s=row['native_cache_time_s'],
                render_elapsed_s=time.perf_counter()-begin,geometry_sha256=hashlib.sha256(positions.tobytes()+triangles.tobytes()).hexdigest(),
                renderer_float32_coordinate_readback_bitexact=True,unchanged_triangle_indices=True,
                native_bounding_box_ndc_extent=[projected.min(0).tolist(),projected.max(0).tolist()],
                columns_supported=info['supported_columns'],mesh_phi_absolute_vertical_gap_quantiles_m=info['mesh_phi_absolute_vertical_gap_quantiles_m'],
                topology=info['topology'],exact_zero_area_triangles=info['exact_zero_area_triangles'],
                maximum_sampled_authored_collider_intrusion_m=max(c[k]['deepest_inside_m']
                    for c in info['authored_solid_contact'].values() for k in ('vertices','triangle_centers'))))
            bpy.data.objects.remove(obj,do_unlink=True);bpy.data.meshes.remove(mesh)
        print('EDDY_FIELD_PAIR_RENDERED',frame,flush=True)
    if any(digest(p)!=sha for p,sha in hashes.items()):raise ValueError('Preserved evidence changed during actual render')
    report=dict(complete=True,accepted=False,originals_unchanged=True,dependency_sha256=hashes,frames=rows,
        source_blend=str(source),render_device=scene.cycles.device,render_samples=16,denoising=True,fixed_seed=0,
        camera_position=list(camera.location),camera_rotation=list(camera.rotation_euler),ortho_scale=camera.data.ortho_scale,
        width=640,height=360,elapsed_s=time.perf_counter()-started,
        source_evolution_clock=audit['source_evolution_clock'],
        scope=__doc__+' Both panels use identical opaque diagnostic material and flat triangle normals. Original authored collider geometry/lights unchanged. Field mesh is a diagnostic candidate, not a fixed liquid solver. Offline render/extraction costs are not gameFPS. All8 features and river integration remain unfinished.')
    with (args.output/'frames.json').open('x') as stream:json.dump(report,stream,indent=2)
    print('EDDY_FIELD_PAIR_RENDER_COMPLETE',len(rows),report['elapsed_s'],flush=True)


if __name__=='__main__':main()
