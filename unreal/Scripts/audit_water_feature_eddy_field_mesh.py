"""Copied-field eddy extraction versus unchanged native particle meshes.

This is a derived diagnostic, not a replacement simulation/cache or acceptance.
Native phi_obstacle is audited separately from actual authored collider geometry.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import time
import bpy
import numpy as np
import openvdb
from mathutils import Vector
from mathutils.bvhtree import BVHTree

sys.path.insert(0,str(Path(__file__).resolve().parent))
from water_feature_native_field_mesh import extract
from water_feature_field_surface import regularize_exact_mesh,interface_residuals
from water_feature_stage_interfaces import column_interface
from water_feature_cache_stages import decode_configuration
from water_feature_geometry import world_coordinates
from audit_water_feature_mesh_contact import topology,contact
from water_feature_solid_clip import EDDY_SOLIDS
from probe_water_feature_native_transport import actual_space
from probe_water_feature_solver_stages import grid_array


def digest(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def mesh_measure(vertices,triangles,fields,columns,origin,h,solids):
    xyz=vertices[triangles];cross=np.cross(xyz[:,1]-xyz[:,0],xyz[:,2]-xyz[:,0])
    tree=BVHTree.FromPolygons(vertices.tolist(),triangles.tolist(),all_triangles=True)
    samples=[]
    for column in columns:
        interface=column_interface(fields['phi'],fields['flags'],column,h)
        point=origin+np.array([column[0]+.5,column[1]+.5,39])*h
        hit,normal,face,distance=tree.ray_cast(Vector(point),Vector((0.,0.,-1.)),39*h)
        usable=interface['status']=='supported' and hit is not None and normal.z>0
        samples.append(dict(column=column,interface=interface,
            mesh_first_upward_ray_hit_m=list(hit) if hit is not None and normal.z>0 else None,
            mesh_minus_phi_vertical_m=float(hit.z-origin[2]-interface['crossings'][0]['relative_height_m']) if usable else None,
            scope='First downward BVH hit; rounded float32 ray, not material-velocity qualification. Missing/ambiguous support retained.'))
    gaps=[abs(s['mesh_minus_phi_vertical_m']) for s in samples if s['mesh_minus_phi_vertical_m'] is not None]
    return dict(vertex_count=len(vertices),triangle_count=len(triangles),topology=topology(triangles),
        exact_zero_area_triangles=int(np.count_nonzero(np.linalg.norm(cross,axis=1)==0)),
        reconstructed_signed_volume_m3=float(np.einsum('ij,ij->i',xyz[:,0],np.cross(xyz[:,1],xyz[:,2])).sum()/6),
        signed_volume_requires_closed_consistent_nonselfintersecting_surface=True,
        bounds_m=[vertices.min(0).tolist(),vertices.max(0).tolist()],columns=samples,
        supported_columns=len(gaps),mesh_phi_absolute_vertical_gap_quantiles_m=np.quantile(gaps,[0,.5,.95,1]).tolist() if gaps else None,
        authored_solid_contact={name:dict(vertices=contact(vertices,solid),triangle_centers=contact(xyz.mean(1),solid))
            for name,solid in solids.items()},
        contact_scope='Closed authored collider oblique-ray parity at vertices/centroids only,1um tolerance; not exhaustive triangle collision or phase qualification.')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--controls',type=Path,required=True)
    parser.add_argument('--temporal',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    if args.output.exists():raise FileExistsError(args.output)
    root=Path(bpy.data.filepath).resolve().parent;shape=(80,21,39);h=.075
    if root.name!='eddy-temporal-resume-v6-m2':raise ValueError('Preserved standard native temporal eddy required')
    control=json.loads(args.controls.read_text());temporal=json.loads(args.temporal.read_text())
    if not control['complete'] or not temporal['complete'] or control['accepted'] or temporal['accepted']:
        raise ValueError('Unaccepted complete diagnostic controls required')
    hashes={**control['dependency_sha256'],**control['outputs_sha256'],**temporal['dependency_sha256']}
    for path in (args.controls,args.temporal,Path(__file__),root/'feature.blend',root/'setup.json',root/'native-temporal-resume.json'):
        hashes[str(path.resolve())]=digest(path)
    for name in ('water_feature_native_field_mesh.py','water_feature_field_surface.py','water_feature_stage_interfaces.py',
            'water_feature_cache_stages.py','water_feature_geometry.py','audit_water_feature_mesh_contact.py',
            'water_feature_solid_clip.py','water_feature_triangulation.py','water_feature_polygon.py',
            'probe_water_feature_native_transport.py','probe_water_feature_solver_stages.py'):
        path=Path(__file__).with_name(name);sha=digest(path)
        if str(path.resolve()) in hashes and hashes[str(path.resolve())]!=sha:raise ValueError('Pinned helper changed')
        hashes[str(path.resolve())]=sha
    if any(digest(p)!=s for p,s in hashes.items()):raise ValueError('Preserved evidence changed before extraction')
    resume=json.loads((root/'native-temporal-resume.json').read_text())
    for relative,sha in resume['output_cache_sha256'].items():
        if digest(root/relative)!=sha:raise ValueError('Native cache changed: '+relative)
        hashes[str((root/relative).resolve())]=sha
    scene=bpy.context.scene;domain=bpy.data.objects['Feature liquid'];state=domain.modifiers[0].domain_settings
    state.cache_directory=str(root/'cache');scene.frame_set(193)
    if state.simulation_method!='FLIP' or state.timesteps_min!=2 or state.timesteps_max!=8 or state.time_scale!=1:
        raise ValueError('Do not change actual native solver or timing')
    actual,identifier=actual_space(shape)
    origin=np.asarray(domain.matrix_world.translation,dtype=float)-np.array(shape)*h/2
    columns=[s['column'] for s in temporal['controls'][0]['frames'][0]['columns']]
    if len(columns)!=54:raise ValueError('Preserve complete earlier column cohort')
    solids={};colliders=[]
    for name in EDDY_SOLIDS:
        obj=bpy.data.objects[name].evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=obj.to_mesh()
        try:
            mesh.calc_loop_triangles()
            vertices=world_coordinates([v.co[:] for v in mesh.vertices],obj.matrix_world)
            triangles=np.array([t.vertices[:] for t in mesh.loop_triangles],np.int64)
            if topology(triangles)!=dict(boundary_edges=0,nonmanifold_edges=0):raise ValueError('Closed actual collider required')
            solids[name]=(vertices.min(0),vertices.max(0),BVHTree.FromPolygons(vertices.tolist(),triangles.tolist(),all_triangles=True))
            colliders.append(dict(name=name,geometry_sha256=hashlib.sha256(vertices.tobytes()+triangles.tobytes()).hexdigest()))
        finally:obj.to_mesh_clear()
    args.output.mkdir();rows=[];started=time.perf_counter();outputs={}
    for frame in range(193,240,2):
        fields={};vdb=root/'cache'/'data'/f'fluid_data_{frame:04d}.vdb'
        for name,dtype in (('phi',np.float32),('phi_obstacle',np.float32),('flags',np.int32)):
            grid=openvdb.read(str(vdb),name)
            if tuple(grid.metadata['file_base_resolution'])!=shape:raise ValueError('Native field shape changed')
            array=np.empty(shape,dtype);grid.copyToArray(array)
            if not np.isfinite(array).all():raise ValueError('Nonfinite field')
            fields[name]=array
        spacing=grid.transform.voxelSize()
        clock=decode_configuration((root/'cache'/'config'/f'config_{frame:04d}.uni').read_bytes())
        if clock['resolution']!=list(shape):raise ValueError('Unchanged isotropic domain required')
        scene.frame_set(frame)
        actual,identifier=actual_space(shape)
        live_before={name:hashlib.sha256(grid_array(actual[f'{name}_s{identifier}'],shape).tobytes()).hexdigest()
            for name in ('phi','phiTmp')}
        native=domain.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=native.to_mesh()
        try:
            mesh.calc_loop_triangles()
            old_vertices=world_coordinates([v.co[:] for v in mesh.vertices],native.matrix_world)
            old_triangles=np.array([t.vertices[:] for t in mesh.loop_triangles],np.int64)
        finally:native.to_mesh_clear()
        old=mesh_measure(old_vertices,old_triangles,fields,columns,origin,h,solids)
        # Refinement control at the first/middle/last declared animation frames.
        for refinement in ((1,2,4) if frame in (193,217,239) else (2,)):
            prefix=args.output/f'frame-{frame:04d}-r{refinement}';obj=prefix.with_suffix('.obj')
            raw,triangles,proof=extract(fields['phi'],fields['phi_obstacle'],refinement,obj)
            fine,triangles,exact=regularize_exact_mesh(raw,triangles)
            base=fine.astype(float)/refinement+proof['base_coordinate_offset_cells']
            vertices=origin+base*h
            info=mesh_measure(vertices,triangles,fields,columns,origin,h,solids)
            residuals=interface_residuals(fields['phi'],fields['phi_obstacle'],base,triangles)
            arrays={}
            for name,array in (('positions',vertices),('triangles',triangles)):
                path=Path(str(prefix)+'-'+name+'.npy');np.save(path,array,allow_pickle=False)
                outputs[str(path.resolve())]=digest(path);arrays[name]=str(path.resolve())
            outputs[str(obj.resolve())]=digest(obj)
            rows.append(dict(frame=frame,refinement=refinement,nominal_time_s=(frame-1)/24,
                native_cache_time_s=clock['time_total_native']/2.5,native_vdb_spacing_m=list(spacing),
                original_particle_mesh=old,derived_mesh=info,fields=residuals,proof=proof,exact_cleanup=exact,
                arrays=arrays,raw_native_obj=str(obj.resolve()),
                geometry_closed_edge_gate=(not info['topology']['boundary_edges'] and not info['topology']['nonmanifold_edges']
                    and not info['exact_zero_area_triangles']),
                authored_sampled_contact_gate=all(c[k]['deepest_inside_m']==0 for c in info['authored_solid_contact'].values()
                    for k in ('vertices','triangle_centers'))))
            print('EDDY_FIELD_MESH_FRAME',frame,refinement,info['topology'],info['mesh_phi_absolute_vertical_gap_quantiles_m'],flush=True)
        if any(hashlib.sha256(grid_array(actual[f'{name}_s{identifier}'],shape).tobytes()).hexdigest()!=sha
                for name,sha in live_before.items()):raise ValueError('Extraction mutated actual host phi')
    if any(digest(p)!=s for p,s in hashes.items()):raise ValueError('Preserved source changed during extraction')
    report=dict(complete=True,accepted=False,originals_unchanged=True,dependency_sha256=hashes,outputs_sha256=outputs,
        source_blend=str((root/'feature.blend').resolve()),source_vdbs_unchanged=True,rows=rows,
        native_actual_phi_same_frame_unchanged=True,actual_domain_origin_m=origin.tolist(),cell_m=h,
        original_nominal_domain_origin_m=[0,-.7875,-.1125],colliders=colliders,
        controls_geometry_qualification_passed=control['geometry_qualification_passed'],
        source_evolution_clock=temporal['controls'][0]['clock'],elapsed_s=time.perf_counter()-started,
        scope='Actual unchanged native moving FLIP eddy. Copied phi/obstacle zero-interface extraction, no new evolution or particle-radius change. Exact duplicate merge/zero-area removal only; all failures retained. Refinement is meshing, NOT fluid spatial convergence. No foam/froth, velocity/mass/collision/optical/game acceptance.')
    with (args.output/'eddy-field-mesh.json').open('x') as stream:json.dump(report,stream,indent=2)
    print('EDDY_FIELD_MESH_AUDIT_COMPLETE',len(rows),report['elapsed_s'],flush=True)


if __name__=='__main__':
    error=None
    try:main()
    except Exception as exc:error=f'{type(exc).__name__}: {exc}';exc.__traceback__=None
    if error:print('EDDY_FIELD_MESH_AUDIT_FAILED',error,flush=True);raise SystemExit(1)
