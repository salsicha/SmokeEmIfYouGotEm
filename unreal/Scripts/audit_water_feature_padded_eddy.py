"""Matched actual native padded/unpadded eddy: fields, meshes and solid contact.

Field extraction remains a separate derived geometry diagnostic, not accepted
liquid or a cache overwrite. All measured failures are retained.
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
from mathutils.bvhtree import BVHTree

sys.path.insert(0,str(Path(__file__).resolve().parent))
from audit_water_feature_eddy_field_mesh import mesh_measure
from audit_water_feature_mesh_contact import topology
from water_feature_cache_stages import decode_configuration,interval_clock
from water_feature_geometry import world_coordinates
from water_feature_field_surface import regularize_exact_mesh,sample_centers,interface_residuals
from water_feature_native_field_mesh import extract
from water_feature_solid_clip import EDDY_SOLIDS
from probe_water_feature_native_transport import actual_space


def digest(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def read_fields(root,frame,shape):
    arrays={}
    for name,dt in (('phi',np.float32),('phi_obstacle',np.float32),('phi_obstacle_inflow',np.float32),('flags',np.int32)):
        g=openvdb.read(str(root/'cache'/'data'/f'fluid_data_{frame:04d}.vdb'),name)
        if tuple(g.metadata['file_base_resolution'])!=shape:raise ValueError('Unexpected native grid shape')
        a=np.empty(shape,dt);g.copyToArray(a)
        if not np.isfinite(a).all():raise ValueError('Nonfinite cached grid')
        arrays[name]=a
    return arrays


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate',type=Path,required=True)
    parser.add_argument('--reference',type=Path,required=True)
    parser.add_argument('--columns',type=Path,required=True)
    parser.add_argument('--panel',choices=('original','padded'),required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    if args.output.exists():raise FileExistsError(args.output)
    candidate=args.candidate.resolve().parent
    receipt=json.loads((candidate/'bake-mesh.json').read_text())
    if not receipt['complete'] or receipt['accepted'] or Path(receipt['blend']).resolve()!=args.candidate.resolve():
        raise ValueError('Complete native candidate required')
    prior=json.loads(args.columns.read_text())
    columns=[r['column'] for r in prior['rows'][0]['original_particle_mesh']['columns']]
    if len(columns)!=54:raise ValueError('Preserve complete54-column cohort')
    hashes={**receipt['dependency_sha256'],**receipt['data_sha256'],**receipt['mesh_sha256']}
    for p in (Path(__file__),args.candidate,args.reference,args.columns,candidate/'bake-mesh.json'):
        hashes[str(p.resolve())]=digest(p)
    for name in ('audit_water_feature_eddy_field_mesh.py','audit_water_feature_mesh_contact.py',
        'water_feature_cache_stages.py','water_feature_geometry.py','water_feature_field_surface.py',
        'water_feature_native_field_mesh.py','water_feature_solid_clip.py','probe_water_feature_native_transport.py',
        'probe_water_feature_solver_stages.py','water_feature_stage_interfaces.py','water_feature_triangulation.py',
        'water_feature_polygon.py','water_feature_private_step.py','audit_water_feature_native_mac_extension.py'):
        p=Path(__file__).with_name(name);hashes[str(p.resolve())]=digest(p)
    # Preserve every original base/mesh file, not just the animation selection.
    for p in (args.reference.parent/'cache').rglob('*'):
        if p.is_file():hashes[str(p.resolve())]=digest(p)
    if any(digest(p)!=sha for p,sha in hashes.items()):raise ValueError('Pinned evidence changed before audit')
    args.output.mkdir();started=time.perf_counter();rows=[];outputs={};controls=[]
    for panel,path,shape in (('original',args.reference,(80,21,39)),('padded',args.candidate,(80,21,42))):
        if panel!=args.panel:continue
        # Loading another blend after importing manta invalidates inherited
        # bindings in this build. Start Blender with this exact -b scene.
        if Path(bpy.data.filepath).resolve()!=path.resolve():raise ValueError('Start with exact native panel blend')
        scene=bpy.context.scene;domain=bpy.data.objects['Feature liquid'];state=domain.modifiers[0].domain_settings
        root=path.resolve().parent;state.cache_directory=str(root/'cache');scene.frame_set(145)
        space,identifier=actual_space(shape)
        if state.simulation_method!='FLIP' or state.time_scale!=1 or (state.timesteps_min,state.timesteps_max)!=(2,8):
            raise ValueError('Actual baseline physics changed')
        origin=np.asarray(domain.matrix_world.translation)-np.array(shape)*.075/2
        solids={};colliders=[]
        for name in EDDY_SOLIDS:
            obj=bpy.data.objects[name].evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=obj.to_mesh()
            try:
                mesh.calc_loop_triangles();vertices=world_coordinates([v.co[:] for v in mesh.vertices],obj.matrix_world)
                triangles=np.array([t.vertices[:] for t in mesh.loop_triangles],np.int64)
                if topology(triangles)!=dict(boundary_edges=0,nonmanifold_edges=0):raise ValueError('Closed collider required')
                solids[name]=(vertices.min(0),vertices.max(0),BVHTree.FromPolygons(vertices.tolist(),triangles.tolist(),all_triangles=True))
                colliders.append(dict(name=name,geometry_sha256=hashlib.sha256(vertices.tobytes()+triangles.tobytes()).hexdigest()))
            finally:obj.to_mesh_clear()
        # Full192-frame bed-field coverage. A zero crossing is not itself a
        # velocity, particle-contact or hydraulic-convergence qualification.
        bed=[]
        for frame in range(1,193):
            arrays=read_fields(root,frame,shape)
            positions=(np.array([[4.05,0,0],[4.05,0,-.025],[4.05,0,.025]])-origin)/.075
            indices=np.floor(positions).astype(int)
            bed.append(dict(frame=frame,world_points_m=[[4.05,0,0],[4.05,0,-.025],[4.05,0,.025]],
                cached_fields_cells={k:sample_centers(a,positions).tolist() for k,a in arrays.items() if k!='flags'},
                containing_cell_flags=arrays['flags'][indices[:,0],indices[:,1],indices[:,2]].tolist(),
                center_column_obstacle_cells=arrays['phi_obstacle'][54,10,:12].tolist(),
                center_column_flags=arrays['flags'][54,10,:12].tolist()))
        before=decode_configuration((root/'cache'/'config'/'config_0144.uni').read_bytes())
        after=decode_configuration((root/'cache'/'config'/'config_0192.uni').read_bytes())
        clock=interval_clock(before,after,48,24)
        controls.append(dict(panel=panel,source_blend=str(path.resolve()),shape=list(shape),origin_m=origin.tolist(),
            cell_m=.075,colliders=colliders,bed_frames=bed,clock=clock))
        for frame in range(145,192,2):
            fields=read_fields(root,frame,shape);scene.frame_set(frame)
            native=domain.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=native.to_mesh()
            try:
                mesh.calc_loop_triangles();vertices=world_coordinates([v.co[:] for v in mesh.vertices],native.matrix_world)
                triangles=np.array([t.vertices[:] for t in mesh.loop_triangles],np.int64)
            finally:native.to_mesh_clear()
            # Existing measure helper's ray spans39 cells: both physical free
            # surfaces lie inside that interval, even with padded lower origin.
            old=mesh_measure(vertices,triangles,fields,columns,origin,.075,solids)
            # Preserve original particle mesh arrays for truly matched rendering.
            native_arrays={}
            for name,a in (('positions',vertices),('triangles',triangles)):
                p=args.output/f'{panel}-{frame:04d}-particle-{name}.npy';np.save(p,a,allow_pickle=False)
                outputs[str(p.resolve())]=digest(p);native_arrays[name]=str(p.resolve())
            for refinement in ((1,2,4) if frame in (145,169,191) else (2,)):
                prefix=args.output/f'{panel}-{frame:04d}-r{refinement}';obj=prefix.with_suffix('.obj')
                raw,triangles,proof=extract(fields['phi'],fields['phi_obstacle'],refinement,obj)
                fine,triangles,clean=regularize_exact_mesh(raw,triangles)
                base=fine.astype(float)/refinement+proof['base_coordinate_offset_cells']
                vertices=origin+base*.075;info=mesh_measure(vertices,triangles,fields,columns,origin,.075,solids)
                arrays={}
                for name,a in (('positions',vertices),('triangles',triangles)):
                    p=Path(str(prefix)+'-'+name+'.npy');np.save(p,a,allow_pickle=False)
                    outputs[str(p.resolve())]=digest(p);arrays[name]=str(p.resolve())
                outputs[str(obj.resolve())]=digest(obj)
                rows.append(dict(panel=panel,frame=frame,refinement=refinement,
                    nominal_time_s=(frame-1)/24,original_particle_mesh=old,native_arrays=native_arrays,
                    derived_mesh=info,arrays=arrays,proof=proof,exact_cleanup=clean,
                    field_residuals=interface_residuals(fields['phi'],fields['phi_obstacle'],base,triangles),
                    geometry_closed_edge_gate=info['topology']==dict(boundary_edges=0,nonmanifold_edges=0)
                        and info['exact_zero_area_triangles']==0,
                    authored_sampled_contact_gate=all(c[k]['deepest_inside_m']==0 for c in info['authored_solid_contact'].values()
                        for k in ('vertices','triangle_centers'))))
            print('PADDED_EDDY_AUDIT_FRAME',panel,frame,flush=True)
    if any(digest(p)!=sha for p,sha in hashes.items()):raise ValueError('Preserved source changed during audit')
    report=dict(complete=True,accepted=False,originals_unchanged=True,dependency_sha256=hashes,outputs_sha256=outputs,
        controls=controls,rows=rows,elapsed_s=time.perf_counter()-started,scope=__doc__,
        caveats='VDB fields are authoritative baked fields; live playback solver grids are NOT claimed loaded. Mesh refinement is NOT fluid convergence. Contact samples are vertices and centroids only, not exhaustive triangle intersection. No foam/froth, water optics, mass/trajectory/game acceptance.')
    with (args.output/'audit.json').open('x') as stream:json.dump(report,stream,indent=2)
    print('PADDED_EDDY_AUDIT_COMPLETE',len(rows),report['elapsed_s'],flush=True)


if __name__=='__main__':
    error=None
    try:main()
    except Exception as exc:error=f'{type(exc).__name__}: {exc}';exc.__traceback__=None
    if error:print('PADDED_EDDY_AUDIT_FAILED',error,flush=True);raise SystemExit(1)
