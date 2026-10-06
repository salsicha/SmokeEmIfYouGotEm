"""Independent equal-frame-span native evolution/mesh comparison, not foam acceptance."""
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
from water_feature_temporal_metrics import step_clock,paired_column_differences
from water_feature_stage_interfaces import column_interface
from water_feature_cache_stages import decode_configuration
from water_feature_geometry import world_coordinates
from audit_water_feature_mesh_contact import topology


def digest(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def quantiles(values):
    return np.quantile(values,[0,.5,.95,1]).tolist() if values else None


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--receipts',type=Path,nargs=3,required=True)
    parser.add_argument('--reference',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    if args.output.exists():raise FileExistsError(args.output)
    started=time.perf_counter()
    ref=json.loads(args.reference.read_text())
    columns=[row['column'] for row in ref['rows']]
    if not ref['complete'] or ref['accepted'] or len(columns)!=54 or len(set(map(tuple,columns)))!=54:
        raise ValueError('Exact earlier 54-column cohort required')
    hashes={str(args.reference.resolve()):digest(args.reference)}
    controls=[];original_hashes=None;code=None
    for receipt,subdivision in zip(args.receipts,(1,2,4)):
        r=json.loads(receipt.read_text());root=Path(r['output'])
        if (not all(r[k] for k in ('complete','originals_unchanged','executed_modules_unchanged'))
            or r['accepted'] or r['subdivision']!=subdivision or r['first_frame']!=193 or r['last_frame']!=240
            or r['fps']!=24 or r['time_scale']!=1. or len(r['seed_fields_verified'])!=11
            or not all(row['native_vdb_bitexact'] for row in r['seed_fields_verified'])):
            raise ValueError('Complete matched native control with explicit seed verification required')
        if original_hashes is None:original_hashes,code=r['original_input_sha256'],r['source_code_sha256']
        if r['original_input_sha256']!=original_hashes or r['source_code_sha256']!=code:
            raise ValueError('Seed/source version changed between controls')
        dependencies={**r['original_input_sha256'],**r['source_code_sha256'],**r['arrays']}
        dependencies.update({str(root/relative):sha for relative,sha in r['output_cache_sha256'].items()})
        dependencies[str(receipt.resolve())]=digest(receipt)
        dependencies[str(root/'feature.blend')]=digest(root/'feature.blend')
        dependencies[str(root/'setup.json')]=digest(root/'setup.json')
        for path,sha in dependencies.items():
            if digest(path)!=sha:raise ValueError('Dependency changed: '+path)
        hashes.update(dependencies)
        clock=step_clock(r['steps'],193,240,subdivision)
        configs=[decode_configuration((root/'cache'/'config'/f'config_{f:04d}.uni').read_bytes()) for f in range(192,241)]
        cached_span=(configs[-1]['time_total_native']-configs[0]['time_total_native'])/2.5
        if any(c['resolution']!=[80,21,39] for c in configs) or abs(cached_span-2.)>1e-4:
            raise ValueError('Invalid actual cache frame span or geometry')
        clock.update(cache_clock_span_s=cached_span,nominal_frame_span_s=2.,
            integrator_minus_cache_clock_s=clock['integrated_duration_s']-cached_span)
        bpy.ops.wm.open_mainfile(filepath=str(root/'feature.blend'))
        obj=bpy.data.objects['Feature liquid'];state=obj.modifiers[0].domain_settings
        if not state.has_cache_baked_mesh or state.simulation_method!='FLIP' or state.timesteps_min!=2*subdivision or state.timesteps_max!=8*subdivision:
            raise ValueError('Saved native control settings mismatch')
        frames=[]
        for frame in (193,194,204,216,228,240):
            bpy.context.scene.frame_set(frame)
            native=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=native.to_mesh()
            try:
                mesh.calc_loop_triangles()
                vertices=world_coordinates([v.co[:] for v in mesh.vertices],native.matrix_world)
                triangles=np.array([t.vertices[:] for t in mesh.loop_triangles],np.int64)
                if len(vertices)<=8 or not np.isfinite(vertices).all():raise ValueError('Missing/nonfinite native mesh')
                xyz=vertices[triangles];cross=np.cross(xyz[:,1]-xyz[:,0],xyz[:,2]-xyz[:,0])
                mesh_info=dict(vertices=len(vertices),triangles=len(triangles),topology=topology(triangles),
                    zero_area_triangles=int(np.count_nonzero(np.linalg.norm(cross,axis=1)==0)),
                    signed_volume_m3=float(np.sum(np.einsum('ij,ij->i',xyz[:,0],np.cross(xyz[:,1],xyz[:,2])))/6),
                    geometry_sha256=hashlib.sha256(vertices.tobytes()+triangles.tobytes()).hexdigest())
                tree=BVHTree.FromPolygons(vertices.tolist(),triangles.tolist(),all_triangles=True)
            finally:native.to_mesh_clear()
            fields={}
            for name,dtype in (('phi',np.float32),('flags',np.int32),('velocity',np.float32)):
                fields[name]=np.empty((80,21,39,3) if name=='velocity' else (80,21,39),dtype)
                openvdb.read(str(root/'cache'/'data'/f'fluid_data_{frame:04d}.vdb'),name).copyToArray(fields[name])
                if not np.isfinite(fields[name]).all():raise ValueError('Nonfinite native field')
            h=.075;origin=np.asarray(native.matrix_world.translation)-np.array([80,21,39])*h/2
            samples=[]
            for column in columns:
                interface=column_interface(fields['phi'],fields['flags'],column,h)
                point=origin+np.array([column[0]+.5,column[1]+.5,39])*h
                hit,normal,face,distance=tree.ray_cast(Vector(point),Vector((0.,0.,-1.)),39*h)
                supported=interface['status']=='supported' and hit is not None and normal.z>0
                samples.append(dict(column=column,interface=interface,
                    mesh_first_upward_ray_hit_m=list(hit) if hit is not None and normal.z>0 else None,
                    mesh_minus_phi_vertical_m=(hit.z-origin[2]-interface['crossings'][0]['relative_height_m']) if supported else None,
                    ray_scope='First downward ray hit only, not normal/material-velocity qualification; detached droplets/overhangs may intervene'))
            frames.append(dict(frame=frame,mesh=mesh_info,columns=samples,
                mesh_phi_absolute_vertical_gap_quantiles_m=quantiles([abs(s['mesh_minus_phi_vertical_m']) for s in samples if s['mesh_minus_phi_vertical_m'] is not None])))
        controls.append(dict(subdivision=subdivision,clock=clock,frames=frames,
            data_bake_seconds=r['data_bake_seconds'],mesh_bake_seconds=r['mesh_bake_seconds']))
        print('TEMPORAL_CONTROL_AUDITED',subdivision,clock['step_count'],clock['integrated_duration_s'],flush=True)
    comparisons=[]
    for left,right in ((0,1),(1,2)):
        for a,b in zip(controls[left]['frames'],controls[right]['frames']):
            rows=paired_column_differences(a['columns'],b['columns'])
            comparisons.append(dict(frame=a['frame'],subdivisions=[controls[left]['subdivision'],controls[right]['subdivision']],
                rows=rows,absolute_vertical_difference_quantiles_m=quantiles([abs(r['vertical_difference_m']) for r in rows if r['supported']]),
                supported_columns=sum(r['supported'] for r in rows)))
    for name in ('audit_water_feature_temporal_resume.py','water_feature_temporal_metrics.py',
        'test_water_feature_temporal_metrics.py','water_feature_stage_interfaces.py','water_feature_cache_stages.py',
        'water_feature_geometry.py','audit_water_feature_mesh_contact.py'):
        path=Path(__file__).with_name(name).resolve();hashes[str(path)]=digest(path)
    if any(digest(path)!=sha for path,sha in hashes.items()):raise ValueError('Input changed during audit')
    report=dict(complete=True,accepted=False,originals_unchanged=True,dependency_sha256=hashes,
        controls=controls,comparisons=comparisons,elapsed_s=time.perf_counter()-started,
        limitations='Equal 48-frame span with actual host emissions/obstacles and native mesh; nominal clock and observed integrator dt sums reported separately. Same spatial grid and serialized seed; no proof of uninterrupted-bake identity or spatial convergence. Vertical phi columns and first native mesh ray hits are diagnostics, not material motion/foam. Missing/ambiguous columns retained. No collision, shoreline, optical, foam-phase or gameFPS acceptance claimed.')
    with args.output.open('x') as stream:json.dump(report,stream,indent=2)
    print('NATIVE_TEMPORAL_AUDIT_COMPLETE',args.output,len(hashes),report['elapsed_s'],flush=True)


if __name__=='__main__':
    error=None
    try:main()
    except Exception as exc:
        error=f'{type(exc).__name__}: {exc}';exc.__traceback__=None
    if error:
        print('NATIVE_TEMPORAL_AUDIT_FAILED',error,flush=True);raise SystemExit(1)
