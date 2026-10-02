"""Actual explicit-wall meshes and native primary contact; no simulation edits."""
import argparse
import ctypes
import hashlib
import json
from pathlib import Path
import sys
import time
import bpy
import manta
import numpy as np
from mathutils.bvhtree import BVHTree
sys.path.insert(0,str(Path(__file__).resolve().parent))
from audit_water_feature_padded_eddy import read_fields
from audit_water_feature_eddy_field_mesh import mesh_measure
from audit_water_feature_mesh_contact import topology,contact
from water_feature_geometry import world_coordinates
from water_feature_field_surface import regularize_exact_mesh,interface_residuals
from water_feature_native_field_mesh import extract
from probe_water_feature_native_transport import actual_space
from probe_water_feature_solver_stages import cleanup,vector_data_address,grid_array


def digest(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def primary(domain,root,shape,origin,h,solids,frame):
    obj=domain.evaluated_get(bpy.context.evaluated_depsgraph_get());ps=next(p for p in obj.particle_systems if p.name.lower()=='liquid');count=len(ps.particles)
    if count<=0:raise ValueError('Actual primary particles missing')
    p=np.empty(count*3,np.float32);v=np.empty(count*3,np.float32)
    ps.particles.foreach_get('location',p);ps.particles.foreach_get('velocity',v);p=p.reshape(-1,3);v=v.reshape(-1,3)
    scope={};error=None;row=None
    try:
        scope['s99']=manta.Solver(name='owned_explicit_primary',gridSize=manta.vec3(*shape),dim=3)
        scope['pp_s99']=scope['s99'].create(manta.BasicParticleSystem,name='particles')
        scope['pVel_pp99']=scope['pp_s99'].create(manta.PdataVec3,name='particles_velocity')
        if manta.load(name=str(root/'cache'/'data'/f'fluid_data_{frame:04d}.vdb'),objects=[scope['pVel_pp99'],scope['pp_s99']],worldSize=6.75)!=1:raise ValueError('Native primary load failed')
        if scope['pp_s99'].pySize()!=count:raise ValueError('Native/display count differs')
        ptr=vector_data_address(scope['pp_s99'].getDataPointer(),count,16);payload=bytes((ctypes.c_ubyte*(count*16)).from_address(ptr))
        records=np.frombuffer(payload,dtype=np.dtype([('position','<f4',3),('flags','<i4')]))
        world=records['position']*h+origin
        ptr=vector_data_address(scope['pVel_pp99'].getDataPointer(),count,12)
        native_v=np.ctypeslib.as_array((ctypes.c_float*(count*3)).from_address(ptr)).copy().reshape(-1,3)
        np.testing.assert_allclose(world,p,atol=1e-6,rtol=1e-6);np.testing.assert_allclose(native_v/90,v,atol=1e-6,rtol=1e-6)
        unique,counts=np.unique(records['flags'],return_counts=True)
        row=dict(frame=frame,primary_count=count,native_display_match=True,
            maximum_position_component_error_m=float(np.abs(world-p).max()),maximum_raw_api_velocity_error=float(np.abs(native_v/90-v).max()),
            native_velocity_to_physical_mps=h*2.5,physical_speed_quantiles_mps=np.quantile(np.linalg.norm(native_v*h*2.5,axis=1),[0,.5,.95,1]).tolist(),
            primary_flags={str(int(a)):int(b) for a,b in zip(unique,counts)},all_primary_records_retained=True,
            actual_authored_contact={n:contact(world,s) for n,s in solids.items()},
            scope='All native primary centers at three frames, not sphere clearance or full collision/trajectory acceptance. Display-velocity comparison is raw normalized API units; physical speed is separately converted by cell/C01 clock.')
    except Exception as exc:error=f'{type(exc).__name__}: {exc}';exc.__traceback__=None
    finally:cleanup(scope,'99')
    if error:raise RuntimeError(error)
    return row


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('fields','columns','output'):parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    if args.output.exists():raise FileExistsError(args.output)
    audit=json.loads(args.fields.read_text());root=Path(audit['root']);source=root/'feature-mesh.blend'
    receipt=json.loads((root/'bake-mesh.json').read_text());proof=json.loads((root/'padding-preflight.json').read_text())
    if not audit['complete'] or not audit['explicit_wall_station_gate'] or not receipt['complete'] or receipt['accepted']:raise ValueError('Qualified unaccepted native control required')
    if Path(bpy.data.filepath).resolve()!=source.resolve():raise ValueError('Start Blender with exact mesh source')
    hashes={**audit['dependency_sha256'],**receipt['dependency_sha256'],**receipt['data_sha256'],**receipt['mesh_sha256']}
    for p in (Path(__file__),args.fields,args.columns,source,root/'bake-mesh.json'):hashes[str(p.resolve())]=digest(p)
    for name in ('audit_water_feature_padded_eddy.py','audit_water_feature_eddy_field_mesh.py','audit_water_feature_mesh_contact.py',
        'water_feature_geometry.py','water_feature_field_surface.py','water_feature_native_field_mesh.py',
        'probe_water_feature_native_transport.py','probe_water_feature_solver_stages.py','water_feature_stage_interfaces.py',
        'water_feature_triangulation.py','water_feature_polygon.py','water_feature_private_step.py','audit_water_feature_native_mac_extension.py'):
        p=Path(__file__).with_name(name);hashes[str(p.resolve())]=digest(p)
    if any(digest(p)!=sha for p,sha in hashes.items()):raise ValueError('Pinned evidence changed')
    columns=[[c['column'][0]+5,c['column'][1]+5] for c in json.loads(args.columns.read_text())['rows'][0]['derived_mesh']['columns']]
    if len(columns)!=54:raise ValueError('Full original54-column world cohort required')
    shape=tuple(audit['shape']);h=audit['cell_m'];origin=np.array(audit['origin_m']);scene=bpy.context.scene;domain=bpy.data.objects['Feature liquid']
    domain.modifiers[0].domain_settings.cache_directory=str(root/'cache');scene.frame_set(145);actual_space(shape)
    solids={};colliders=[]
    for name,entry in proof['all_physical_boundaries'].items():
        if entry['fluid_type']!='EFFECTOR':continue
        obj=bpy.data.objects[name].evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=obj.to_mesh()
        try:
            mesh.calc_loop_triangles();vertices=world_coordinates([v.co[:] for v in mesh.vertices],obj.matrix_world)
            triangles=np.array([t.vertices[:] for t in mesh.loop_triangles],np.int64)
            if topology(triangles)!=dict(boundary_edges=0,nonmanifold_edges=0):raise ValueError('Closed actual collider required')
            solids[name]=(vertices.min(0),vertices.max(0),BVHTree.FromPolygons(vertices.tolist(),triangles.tolist(),all_triangles=True))
            colliders.append(dict(name=name,geometry_sha256=hashlib.sha256(vertices.tobytes()+triangles.tobytes()).hexdigest(),hide_render=bpy.data.objects[name].hide_render))
        finally:obj.to_mesh_clear()
    if len(solids)!=8:raise ValueError('All eight physical solids including cutaway walls must be audited')
    args.output.mkdir();outputs={};rows=[];particles=[];started=time.perf_counter()
    for frame in range(145,192,2):
        fields=read_fields(root,frame,shape);scene.frame_set(frame);space,identifier=actual_space(shape)
        live={n:hashlib.sha256(grid_array(space[f'{n}_s{identifier}'],shape).tobytes()).hexdigest() for n in ('phi','phiTmp')}
        obj=domain.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=obj.to_mesh()
        try:
            mesh.calc_loop_triangles();positions=world_coordinates([v.co[:] for v in mesh.vertices],obj.matrix_world);triangles=np.array([t.vertices[:] for t in mesh.loop_triangles],np.int64)
        finally:obj.to_mesh_clear()
        native=mesh_measure(positions,triangles,fields,columns,origin,h,solids);native_arrays={}
        for name,a in (('positions',positions),('triangles',triangles)):
            p=args.output/f'native-{frame:04d}-{name}.npy';np.save(p,a,allow_pickle=False);outputs[str(p.resolve())]=digest(p);native_arrays[name]=str(p.resolve())
        for refinement in ((1,2,4) if frame in (145,169,191) else (2,)):
            prefix=args.output/f'field-{frame:04d}-r{refinement}';objpath=prefix.with_suffix('.obj')
            raw,triangles,extraction=extract(fields['phi'],fields['phi_obstacle'],refinement,objpath)
            fine,triangles,exact=regularize_exact_mesh(raw,triangles);base=fine.astype(float)/refinement+extraction['base_coordinate_offset_cells'];positions=origin+base*h
            info=mesh_measure(positions,triangles,fields,columns,origin,h,solids);arrays={}
            for name,a in (('positions',positions),('triangles',triangles)):
                p=Path(str(prefix)+'-'+name+'.npy');np.save(p,a,allow_pickle=False);outputs[str(p.resolve())]=digest(p);arrays[name]=str(p.resolve())
            outputs[str(objpath.resolve())]=digest(objpath)
            rows.append(dict(frame=frame,refinement=refinement,nominal_time_s=(frame-1)/24,derived_mesh=info,arrays=arrays,
                original_particle_mesh=native,native_arrays=native_arrays,proof=extraction,exact_cleanup=exact,
                field_residuals=interface_residuals(fields['phi'],fields['phi_obstacle'],base,triangles),
                geometry_closed_edge_gate=info['topology']==dict(boundary_edges=0,nonmanifold_edges=0) and info['exact_zero_area_triangles']==0,
                authored_sampled_contact_gate=all(c[k]['deepest_inside_m']==0 for c in info['authored_solid_contact'].values() for k in ('vertices','triangle_centers'))))
        if frame in (145,169,191):particles.append(primary(domain,root,shape,origin,h,solids,frame))
        if any(hashlib.sha256(grid_array(space[f'{n}_s{identifier}'],shape).tobytes()).hexdigest()!=sha for n,sha in live.items()):raise ValueError('Derived work changed live fields')
        print('EXPLICIT_MESH_FRAME',root.name,frame,flush=True)
    if any(digest(p)!=sha for p,sha in hashes.items()):raise ValueError('Native evidence changed during audit')
    report=dict(complete=True,accepted=False,originals_unchanged=True,dependency_sha256=hashes,outputs_sha256=outputs,
        controls=[dict(source_blend=str(source.resolve()),shape=list(shape),origin_m=origin.tolist(),cell_m=h,colliders=colliders)],
        rows=rows,primary_frames=particles,world_columns_preserved_by_integer_shift=[5,5],elapsed_s=time.perf_counter()-started,scope=__doc__,
        caveats='Closed/topology and vertex/centroid contact checks only,1um tolerance; no exhaustive triangle/self-intersection or pressure/mass/circulation/convergence/optical acceptance. All eight actual solids retained, including physically active cutaway walls. Extraction refinement is not CFD refinement.')
    with (args.output/'audit.json').open('x') as stream:json.dump(report,stream,indent=2)
    print('EXPLICIT_MESH_COMPLETE',root.name,len(rows),report['elapsed_s'],flush=True)


if __name__=='__main__':
    error=None
    try:main()
    except Exception as exc:error=f'{type(exc).__name__}: {exc}';exc.__traceback__=None
    if error:print('EXPLICIT_MESH_AUDIT_FAILED',error,flush=True);raise SystemExit(1)
