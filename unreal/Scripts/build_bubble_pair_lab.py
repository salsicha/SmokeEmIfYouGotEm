"""Connected two-cavity water boundary for a reduced capillary-pair study.

Isolated solved profiles plus neighbor meniscus height: a volume-preserving
vertical shear, NOT a nonlinear three-dimensional equilibrium. Native shape
keys carry the audited migration. No overlapping full water volumes.
"""
import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import shutil
import sys
import time

import bpy
import numpy as np
from mathutils import Vector


def mesh_volume(vertices,faces):
    v=np.asarray(vertices)
    tris=np.array([(f[0],f[i],f[i+1]) for f in faces for i in range(1,len(f)-1)])
    return float(np.sum(v[tris[:,0]]*np.cross(v[tris[:,1]],v[tris[:,2]]))/6)


def geometry(equilibrium,distance,edge_steps=32,rings=96):
    model=equilibrium['model']
    rim=model['rim_radius_m']
    exterior=np.asarray(equilibrium['exterior_profile_rz_m'])[::-1]
    cavity=np.asarray(equilibrium['cavity_profile_rz_m'])
    arc=np.concatenate(([0.],np.cumsum(np.linalg.norm(np.diff(cavity,axis=0),axis=1))))
    samples=np.linspace(0.,arc[-1],rings+1)
    cav=np.column_stack([np.interp(samples,arc,cavity[:,j]) for j in (0,1)])[::-1]
    half=.012
    n=4*edge_steps
    all_vertices,all_faces,films,gas_volumes=[],[],[],[]
    for sign in (-1,1):
        center=sign*distance/2
        corners=([[-half,-half],[0,-half],[0,half],[-half,half]] if sign<0
                 else [[0,-half],[half,-half],[half,half],[0,half]])
        # Uniform angular sampling within each rectangular sector avoids
        # undersampling the close symmetry edge as the pair approaches.
        corner_angles=np.unwrap([math.atan2(y,x-center) for x,y in corners]+[math.atan2(corners[0][1],corners[0][0]-center)])
        points=[]
        for edge in range(4):
            first,last=corners[edge],corners[(edge+1)%4]
            for angle in np.linspace(corner_angles[edge],corner_angles[edge+1],edge_steps,endpoint=False):
                if first[0]==last[0]:
                    radius=(first[0]-center)/math.cos(angle)
                    points.append([first[0],radius*math.sin(angle)])
                else:
                    radius=first[1]/math.sin(angle)
                    points.append([center+radius*math.cos(angle),first[1]])
            points[-edge_steps]=list(first)
        outer=np.array(points)
        vectors=outer-[center,0.]
        outer_radius=np.linalg.norm(vectors,axis=1)
        unit=vectors/outer_radius[:,None]
        def neighbor(xy):
            rr=np.linalg.norm(xy-[-center,0.],axis=1)
            if rr.min()<exterior[0,0] or rr.max()>exterior[-1,0]:
                raise ValueError('Neighbor field queried outside solved exterior')
            return np.interp(rr,exterior[:,0],exterior[:,1])
        vertices=[]
        for t in np.linspace(0.,1.,rings):
            rr=outer_radius**(1-t)*rim**t
            xy=unit*rr[:,None]+[center,0.]
            if t==0:
                xy=outer.copy()
            z=np.interp(rr,exterior[:,0],exterior[:,1])+neighbor(xy)
            vertices.extend(np.column_stack((xy,z)).tolist())
        start_cavity=(rings-1)*n
        for rr,z in cav[1:-1]:
            xy=unit*rr+[center,0.]
            vertices.extend(np.column_stack((xy,z+neighbor(xy))).tolist())
        total_rings=2*rings-1
        faces=[]
        cavity_faces=[]
        for ring in range(total_rings-1):
            lo,hi=ring*n,(ring+1)*n
            f=[(lo+j,lo+(j+1)%n,hi+(j+1)%n,hi+j) for j in range(n)]
            faces.extend(f)
            if lo>=start_cavity:
                cavity_faces.extend(f)
        pole=len(vertices)
        vertices.append([center,0.,model['cavity_bottom_z_m']+float(neighbor(np.array([[center,0.]]))[0])])
        f=[((total_rings-1)*n+j,(total_rings-1)*n+(j+1)%n,pole) for j in range(n)]
        faces.extend(f); cavity_faces.extend(f)
        bottom=len(vertices)
        vertices.extend(np.column_stack((outer,np.full(n,-.006))).tolist())
        for j in range(n):
            k=(j+1)%n
            if outer[j,0]==0 and outer[k,0]==0:
                continue
            faces.append((j,bottom+j,bottom+k,k))
        bottom_center=len(vertices)
        vertices.append([center,0.,-.006])
        faces.extend((bottom+(j+1)%n,bottom+j,bottom_center) for j in range(n))
        curvature=model['cap_curvature_radius_m']
        theta=math.asin(rim/curvature)
        base=model['rim_height_m']-math.sqrt(curvature**2-rim**2)
        film=[[center,0.,base+curvature+float(neighbor(np.array([[center,0.]]))[0])]]
        for angle in np.linspace(0.,theta,25)[1:]:
            xy=unit*(curvature*math.sin(angle))+[center,0.]
            film.extend(np.column_stack((xy,base+curvature*math.cos(angle)+neighbor(xy))).tolist())
        film_faces=[(0,1+j,1+(j+1)%n) for j in range(n)]
        for ring in range(23):
            lo,hi=1+ring*n,1+(ring+1)*n
            film_faces.extend((lo+j,hi+j,hi+(j+1)%n,lo+(j+1)%n) for j in range(n))
        gas_volumes.append(mesh_volume(film,film_faces)-mesh_volume(vertices,cavity_faces))
        films.append((film,film_faces))
        offset=len(all_vertices)
        all_vertices.extend(vertices)
        all_faces.extend(tuple(offset+i for i in face) for face in faces)
    shared,vertices,mapping={},[],[]
    for v in all_vertices:
        key=tuple(round(c,12) for c in v) if abs(v[0])<1e-14 else None
        if key is not None and key in shared:
            mapping.append(shared[key])
        else:
            index=len(vertices)
            vertices.append(v); mapping.append(index)
            if key is not None:
                shared[key]=index
    faces=[tuple(mapping[i] for i in f) for f in all_faces]
    edges=Counter(tuple(sorted((f[j],f[(j+1)%len(f)]))) for f in faces for j in range(len(f)))
    if set(edges.values())!={2}:
        raise RuntimeError('Pair water boundary has cracks or duplicate internal faces')
    if not np.isfinite(vertices).all():
        raise ValueError('Nonfinite water')
    return vertices,faces,films,gas_volumes


def create_pair_animation(data,water_material=None,film_material=None):
    """Build the actual native rig; also testable in-memory without a render/cache."""
    objects=[]
    topology=None
    volumes=[]
    for row in data['frames']:
        water,faces,films,gas=geometry(data['equilibrium'],row['distance_m'])
        current=(faces,films[0][1],films[1][1])
        arrays=[water,films[0][0],films[1][0]]
        if topology is None:
            topology=current
            for name,coords,polygons,mat in zip(('Connected pair water','Left film','Right film'),arrays,current,(water_material,film_material,film_material)):
                mesh=bpy.data.meshes.new(name)
                mesh.from_pydata(coords,[],polygons); mesh.update()
                for polygon in mesh.polygons:
                    polygon.use_smooth=True
                obj=bpy.data.objects.new(name,mesh)
                bpy.context.collection.objects.link(obj)
                if mat is not None:
                    mesh.materials.append(mat)
                obj.shape_key_add(name='Basis')
                objects.append(obj)
        elif current!=topology:
            raise RuntimeError('Changing water connectivity during migration')
        for obj,coords in zip(objects,arrays):
            key=obj.shape_key_add(name=f'Physical pose {row["frame"]:04d}')
            key.data.foreach_set('co',np.array(coords,dtype=np.float32).ravel())
            for frame,value in ((row['frame']-1,0.),(row['frame'],1.),(row['frame']+1,0.)):
                key.value=value
                key.keyframe_insert('value',frame=frame)
        volumes.append(gas)
    for obj in objects:
        for layer in obj.data.shape_keys.animation_data.action.layers:
            for strip in layer.strips:
                for bag in strip.channelbags:
                    for curve in bag.fcurves:
                        for key in curve.keyframe_points:
                            key.interpolation='LINEAR'
    expected=data['equilibrium']['model']['nominal_gas_volume_m3']
    error=float(np.max(np.abs(np.array(volumes)/expected-1)))
    if error>.003:
        raise RuntimeError(f'Gas-volume tessellation error too large: {error}')
    return objects,volumes,error


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--migration',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args(sys.argv[sys.argv.index('--')+1:])
    data=json.loads(args.migration.read_text())
    if shutil.disk_usage(args.migration.parent).free<1024**3:
        raise RuntimeError('Need 1 GiB disk reserve')
    args.output.mkdir(parents=True,exist_ok=False)
    water_material=bpy.data.objects['Water with actual gas cavity'].data.materials[0]
    film_material=bpy.data.objects['Bubble film'].data.materials[0]
    for name in ('Water with actual gas cavity','Bubble film'):
        bpy.data.objects.remove(bpy.data.objects[name],do_unlink=True)
    scene=bpy.context.scene
    scene.render.fps=data['fps']
    scene.frame_start=1
    scene.frame_end=len(data['frames'])
    scene.camera.location=(.003,-.012,.009)
    scene.camera.rotation_euler=(Vector((0,0,-.0003))-scene.camera.location).to_track_quat('-Z','Y').to_euler()
    scene.camera.data.ortho_scale=.011
    scene.render.resolution_x,scene.render.resolution_y=800,450
    scene.cycles.samples=64
    objects,volumes,error=create_pair_animation(data,water_material,film_material)
    scene.frame_set(1)
    blend=(args.output/'feature.blend').resolve()
    bpy.ops.wm.save_as_mainfile(filepath=str(blend))
    (args.output/'migration.json').write_text(json.dumps(data,indent=2))
    setup=dict(case='bubble-pair-reference',blend=str(blend),fps=data['fps'],frames=len(data['frames']),
        model='Reference-condition reduced capillary attraction and connected superposed interfaces',
        inputs=data['inputs'],maximum_relative_gas_volume_mesh_error=error,
        gas_volume_per_frame_m3=volumes,water_boundary_closed_all_frames=True,
        physical_accuracy_accepted=False,visual_accuracy_accepted=False,
        limitations=data['scope']+' Neighboring height fields are superposed, not a nonlinear 3D solution. Viscosity is 44.15 mPa s, not ordinary water. Initial rise, contact and coalescence excluded.')
    (args.output/'setup.json').write_text(json.dumps(setup,indent=2))
    prefs=bpy.context.preferences.addons['cycles'].preferences
    prefs.compute_device_type='OPTIX'; prefs.get_devices()
    if not any(d.type=='OPTIX' for d in prefs.devices):
        raise RuntimeError('OptiX unavailable')
    for d in prefs.devices:
        d.use=d.type=='OPTIX'
    scene.cycles.device='GPU'
    rows=[]
    for frame in (1,6,12):
        if shutil.disk_usage(args.output).free<1024**3:
            raise RuntimeError('Disk reserve reached; preserve prepared scene')
        scene.frame_set(frame)
        scene.render.filepath=str((args.output/f'frame-{frame:04d}.png').resolve())
        start=time.monotonic()
        bpy.ops.render.render(write_still=True)
        rows.append(dict(frame=frame,image=scene.render.filepath,render_seconds=time.monotonic()-start,
                         sha256=hashlib.sha256(Path(scene.render.filepath).read_bytes()).hexdigest()))
    (args.output/'previews.json').write_text(json.dumps(rows,indent=2))
    print('PAIR_PREPARED',json.dumps(setup),flush=True)


if __name__=='__main__':
    main()
