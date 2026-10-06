"""Locate native field/primary/derived-mesh contact against authored solids.

Read-only mechanism audit; no particle projection, clipping, bake or solve.
"""
import argparse
import ctypes
import dis
import hashlib
import json
from pathlib import Path
import sys
import bpy
import manta
import numpy as np
import openvdb
from mathutils import Vector
from mathutils.bvhtree import BVHTree

sys.path.insert(0,str(Path(__file__).resolve().parent))
from probe_water_feature_native_transport import actual_space
from probe_water_feature_solver_stages import vector_data_address,cleanup
from water_feature_geometry import world_coordinates
from water_feature_field_surface import sample_centers
from water_feature_solid_clip import EDDY_SOLIDS
from audit_water_feature_mesh_contact import topology,interior_distance


def digest(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def contacts(points,solid,fields,origin,h):
    lo,hi,tree=solid
    ids=np.flatnonzero(np.all((points>lo+1e-6)&(points<hi-1e-6),axis=1))
    inside=[]
    for index in ids:
        depth=interior_distance(tree,points[index])
        if depth>0:inside.append((depth,int(index)))
    inside.sort(reverse=True);selected=inside[:12];rows=[]
    for depth,index in selected:
        p=points[index];nearest,normal,face,distance=tree.find_nearest(Vector(p))
        gp=(p-origin)/h
        supported=bool(np.all(gp>=.5)&np.all(gp<=np.array(fields['phi'].shape)-.5))
        cell=np.floor(gp).astype(int)
        rows.append(dict(index=index,world_m=p.tolist(),depth_inside_m=depth,
            nearest_authored_world_m=list(nearest),nearest_outward_normal=list(normal),nearest_face=face,
            supported_center_box=supported,
            field_values_cells={name:float(sample_centers(a,gp[None,:])[0]) for name,a in fields.items()
                if name!='flags'} if supported else None,
            containing_cell_flags=int(fields['flags'][tuple(cell)]) if supported else None))
    return dict(point_count=len(points),inside_count=len(inside),deepest_inside_m=inside[0][0] if inside else 0.,
                deepest_points=rows,scope='All contacts counted; deepest12 retained with actual coordinates, fields and nearest authored faces.')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--audit',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    if args.output.exists():raise FileExistsError(args.output)
    audit=json.loads(args.audit.read_text());control=audit['controls'][0];root=Path(control['source_blend']).parent
    if not audit['complete'] or audit['accepted'] or Path(bpy.data.filepath).resolve()!=Path(control['source_blend']).resolve():
        raise ValueError('Exact preserved native panel scene required')
    shape=tuple(control['shape']);origin=np.array(control['origin_m']);h=control['cell_m']
    hashes={str(p.resolve()):digest(p) for p in (Path(__file__),args.audit,Path(bpy.data.filepath))}
    for name in ('probe_water_feature_native_transport.py','probe_water_feature_solver_stages.py',
        'water_feature_geometry.py','water_feature_field_surface.py','water_feature_solid_clip.py',
        'audit_water_feature_mesh_contact.py','water_feature_triangulation.py','water_feature_polygon.py',
        'water_feature_private_step.py','audit_water_feature_native_mac_extension.py','water_feature_cache_stages.py'):
        p=Path(__file__).with_name(name);sha=digest(p)
        if audit['dependency_sha256'].get(str(p.resolve()),sha)!=sha:raise ValueError('Pinned helper changed')
        hashes[str(p.resolve())]=sha
    scene=bpy.context.scene;domain=bpy.data.objects['Feature liquid']
    domain.modifiers[0].domain_settings.cache_directory=str(root/'cache');scene.frame_set(145)
    space,identifier=actual_space(shape)
    compiled=[dict(name=name,instructions=[dict(offset=i.offset,opname=i.opname,argrepr=i.argrepr)
        for i in dis.get_instructions(space[f'{name}_{identifier}'])])
        for name in ('liquid_step','liquid_adaptive_step')]
    solids={}
    for name in EDDY_SOLIDS:
        obj=bpy.data.objects[name].evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=obj.to_mesh()
        try:
            mesh.calc_loop_triangles();v=world_coordinates([x.co[:] for x in mesh.vertices],obj.matrix_world)
            t=np.array([x.vertices[:] for x in mesh.loop_triangles],np.int64)
            if topology(t)!=dict(boundary_edges=0,nonmanifold_edges=0):raise ValueError('Closed actual collider required')
            solids[name]=(v.min(0),v.max(0),BVHTree.FromPolygons(v.tolist(),t.tolist(),all_triangles=True))
        finally:obj.to_mesh_clear()
    rows=[]
    for frame in (145,169,191):
        data=root/'cache'/'data'/f'fluid_data_{frame:04d}.vdb';sha=digest(data)
        if audit['dependency_sha256'][str(data.resolve())]!=sha:raise ValueError('Pinned DATA changed')
        hashes[str(data.resolve())]=sha;fields={}
        for name,dt in (('phi',np.float32),('phi_obstacle',np.float32),('phi_obstacle_inflow',np.float32),('flags',np.int32)):
            grid=openvdb.read(str(data),name);a=np.empty(shape,dt);grid.copyToArray(a);fields[name]=a
        scene.frame_set(frame);obj=domain.evaluated_get(bpy.context.evaluated_depsgraph_get())
        ps=next(p for p in obj.particle_systems if p.name.lower()=='liquid');count=len(ps.particles)
        displayed=np.empty(count*3,np.float32);ps.particles.foreach_get('location',displayed)
        scope={};error=None;positions=None;particle_flags=None
        try:
            scope['s99']=manta.Solver(name='owned_contact_field_audit',gridSize=manta.vec3(*shape),dim=3)
            scope['pp_s99']=scope['s99'].create(manta.BasicParticleSystem,name='particles')
            scope['pVel_pp99']=scope['pp_s99'].create(manta.PdataVec3,name='particles_velocity')
            if manta.load(name=str(data),objects=[scope['pVel_pp99'],scope['pp_s99']],worldSize=6)!=1:
                raise ValueError('Native typed primary load failed')
            if scope['pp_s99'].pySize()!=count:raise ValueError('Native/display primary count mismatch')
            ptr=vector_data_address(scope['pp_s99'].getDataPointer(),count,16)
            records=np.frombuffer(bytes((ctypes.c_ubyte*(count*16)).from_address(ptr)),
                dtype=np.dtype([('position','<f4',3),('flags','<i4')]))
            positions=records['position']*h+origin;particle_flags=records['flags'].copy()
            np.testing.assert_allclose(positions,displayed.reshape(-1,3),atol=1e-6,rtol=1e-6)
        except Exception as exc:error=f'{type(exc).__name__}: {exc}';exc.__traceback__=None
        finally:cleanup(scope,'99')
        if error:raise RuntimeError(error)
        derived=next(r for r in audit['rows'] if r['frame']==frame and r['refinement']==2)
        vertices=np.load(derived['arrays']['positions'],allow_pickle=False)
        triangles=np.load(derived['arrays']['triangles'],allow_pickle=False)
        for p in derived['arrays'].values():
            if digest(p)!=audit['outputs_sha256'][p]:raise ValueError('Pinned extraction changed')
            hashes[p]=digest(p)
        flags,counts=np.unique(particle_flags,return_counts=True)
        row=dict(frame=frame,native_display_positions_match=True,primary_flag_counts=dict(zip(map(str,flags),map(int,counts))),
            cohorts={name:{solid:contacts(points,s,fields,origin,h) for solid,s in solids.items()}
                for name,points in (('primary',positions),('field_vertices',vertices),
                                   ('field_triangle_centers',vertices[triangles].mean(1)))})
        rows.append(row);print('CONTACT_FIELD_FRAME',frame,row['primary_flag_counts'],flush=True)
        for cohort,items in row['cohorts'].items():
            for solid,c in items.items():
                if c['deepest_points']:
                    p=c['deepest_points'][0]
                    print('CONTACT_FIELD_WORST',frame,cohort,solid,p['world_m'],p['depth_inside_m'],p['field_values_cells'],flush=True)
    if any(digest(p)!=sha for p,sha in hashes.items()):raise ValueError('Read-only probe changed source')
    with args.output.open('x') as stream:json.dump(dict(complete=True,accepted=False,originals_unchanged=True,
        dependency_sha256=hashes,frames=rows,compiled_native_steps=compiled,
        scope=__doc__+'Deepest locations are a diagnostic selection, not a complete contact trajectory. No flags or points excluded, no acceptance.'),stream,indent=2)


if __name__=='__main__':
    error=None
    try:main()
    except Exception as exc:error=f'{type(exc).__name__}: {exc}';exc.__traceback__=None
    if error:print('CONTACT_FIELD_FAILED',error,flush=True);raise SystemExit(1)
