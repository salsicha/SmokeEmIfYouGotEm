"""Fixed native views of unchanged manufactured-control meshes, not foam optics."""
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
    parser.add_argument('--audit',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    if args.output.exists():raise FileExistsError(args.output)
    audit=json.loads(args.audit.read_text());hashes=dict(audit['dependency_sha256'])
    hashes[str(args.audit.resolve())]=digest(args.audit)
    hashes[str(Path(__file__).resolve())]=digest(Path(__file__))
    if not audit['complete'] or audit['accepted'] or any(digest(p)!=sha for p,sha in hashes.items()):
        raise ValueError('Complete unchanged manufactured native controls required')
    controls=[json.loads(Path(c['receipt']).read_text()) for c in audit['controls']]
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.device='CPU'
    scene.cycles.samples=4;scene.cycles.use_denoising=True;scene.cycles.seed=0;scene.cycles.use_animated_seed=False
    scene.render.resolution_x=480;scene.render.resolution_y=270;scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGB'
    scene.render.threads_mode='FIXED';scene.render.threads=4
    scene.view_settings.view_transform='Standard'
    world=bpy.data.worlds.new('Authored diagnostic environment');scene.world=world;world.use_nodes=True
    world.node_tree.nodes['Background'].inputs['Color'].default_value=(.09,.12,.16,1)
    world.node_tree.nodes['Background'].inputs['Strength'].default_value=.5
    water=bpy.data.materials.new('Blue geometry diagnostic - NOT measured water optics');water.use_nodes=True
    bsdf=water.node_tree.nodes.get('Principled BSDF');bsdf.inputs['Base Color'].default_value=(.025,.25,.36,1)
    bsdf.inputs['Roughness'].default_value=.38;bsdf.inputs['Metallic'].default_value=0
    gold=bpy.data.materials.new('Analytic box/height annotation');gold.diffuse_color=(1,.7,.06,1)
    gold.use_nodes=True;b=gold.node_tree.nodes.get('Principled BSDF')
    b.inputs['Base Color'].default_value=(1,.7,.06,1);b.inputs['Emission Color'].default_value=(1,.55,.01,1)
    b.inputs['Emission Strength'].default_value=.4
    def line(name,points):
        curve=bpy.data.curves.new(name,'CURVE');curve.dimensions='3D';curve.bevel_depth=.004;curve.bevel_resolution=1
        spline=curve.splines.new('POLY');spline.points.add(len(points)-1)
        for point,coordinate in zip(spline.points,points):point.co=(*coordinate,1)
        obj=bpy.data.objects.new(name,curve);scene.collection.objects.link(obj);obj.data.materials.append(gold)
    # These are labelled analytic annotations, not fake fluid/colliders or foam.
    for z in (.15,.9):line('Analytic allowed wet-box outline',[(.15,.15,z),(2.25,.15,z),(2.25,1.65,z),(.15,1.65,z),(.15,.15,z)])
    for x,y in ((.15,.15),(2.25,.15),(2.25,1.65),(.15,1.65)):
        line('Analytic closed-wall annotation',[(x,y,.15),(x,y,.9)])
    def aim(obj,target):obj.rotation_euler=(Vector(target)-obj.location).to_track_quat('-Z','Y').to_euler()
    camera_data=bpy.data.cameras.new('Fixed manufactured-view camera');camera=bpy.data.objects.new(camera_data.name,camera_data)
    scene.collection.objects.link(camera);camera.location=(3.6,-3.8,3.2);aim(camera,(1.2,.9,.48))
    camera_data.type='ORTHO';camera_data.ortho_scale=4.5;scene.camera=camera
    for position,power,size in (((1.2,-1.5,4.),650,3.),((-2.,1.,2.8),300,2.)):
        data=bpy.data.lights.new('Authored diagnostic area','AREA');data.energy=power;data.shape='DISK';data.size=size
        obj=bpy.data.objects.new(data.name,data);scene.collection.objects.link(obj);obj.location=position;aim(obj,(1.2,.9,.6))
    args.output.mkdir();rows=[];start=time.perf_counter()
    for control_index,report in enumerate(controls):
        for frame in range(0,48,2):
            row=report['mesh_frames'][frame]
            positions=np.load(row['positions'],allow_pickle=False).astype(np.float64)*report['mesh_cell_m']
            triangles=np.load(row['triangles'],allow_pickle=False)
            mesh=bpy.data.meshes.new('Unchanged native control mesh')
            mesh.from_pydata(positions.tolist(),[],triangles.tolist());mesh.update()
            obj=bpy.data.objects.new(mesh.name,mesh);scene.collection.objects.link(obj);mesh.materials.append(water)
            bpy.context.view_layer.update()
            bounds=np.array(np.meshgrid(*zip(positions.min(0),positions.max(0)),indexing='ij')).reshape(3,-1).T
            projected=np.array([world_to_camera_view(scene,camera,Vector(point))[:] for point in bounds])
            if projected[:,:2].min()<.03 or projected[:,:2].max()>.97 or projected[:,2].min()<=0:
                raise ValueError('Native mesh bounding box does not fit the fixed view with3-percent margin')
            # Preserve native triangle faces, coordinates and flat normals.
            readback=np.empty(len(mesh.vertices)*3,np.float32);mesh.vertices.foreach_get('co',readback)
            np.testing.assert_array_equal(readback.reshape(-1,3),positions.astype(np.float32))
            if [tuple(p.vertices) for p in mesh.polygons]!=[tuple(map(int,t)) for t in triangles]:
                raise ValueError('Rendered native faces changed')
            path=args.output/f'control-{control_index}-frame-{frame:03d}.png';scene.frame_set(frame)
            scene.render.filepath=str(path.resolve());started=time.perf_counter();bpy.ops.render.render(write_still=True)
            state=audit['controls'][control_index]['frames'][frame]
            rows.append(dict(control_index=control_index,frame=frame,time_s=frame/24,image=str(path.resolve()),
                sha256=digest(path),render_elapsed_s=time.perf_counter()-started,
                bounding_box_ndc_extent=[projected.min(0).tolist(),projected.max(0).tolist()],
                native_positions=row['positions'],native_triangles=row['triangles'],
                geometry_sha256=hashlib.sha256(positions.tobytes()+triangles.tobytes()).hexdigest(),
                phi_minus_initial_mm=state['phi_minus_initial_m']['median']*1000,
                mesh_minus_phi_mm=state['mesh_minus_phi_m']['median']*1000,
                maximum_wall_vertex_intrusion_mm=state['mesh']['maximum_vertex_wall_intrusion_m']*1000))
            bpy.data.objects.remove(obj,do_unlink=True);bpy.data.meshes.remove(mesh)
    if any(digest(p)!=sha for p,sha in hashes.items()):raise ValueError('Audited inputs changed during render')
    report=dict(complete=True,accepted=False,originals_unchanged=True,frames=rows,dependency_sha256=hashes,
        simulation_fps=24,render_stride=2,render_samples=4,render_device='CPU',fixed_seed=0,width=480,height=270,
        camera_position=list(camera.location),camera_rotation=list(camera.rotation_euler),ortho_scale=camera_data.ortho_scale,
        elapsed_s=time.perf_counter()-start,
        scope='Actual native Blender renders of unchanged mesh coordinates/triangles; no clipping, mesh correction, particle projection or foam. Opaque blue diagnostic shader is NOT water optical acceptance. Gold wire box marks analytic closed-wall positions and intended0.9m height; not rendered collider/physical fluid. External engine work exists, so offline render costs do not establish isolated performance or gameFPS.')
    with (args.output/'frames.json').open('x') as stream:json.dump(report,stream,indent=2)
    print('NATIVE_FLAT_CONTROL_RENDER_COMPLETE',len(rows),report['elapsed_s'],flush=True)


if __name__=='__main__':main()
