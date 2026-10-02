"""Paired reconstructed volume/section-flux checks, not a conservation claim.

Native padded FLIP controls differ ONLY in fractional-cell boundary handling.
Velocity conversion follows the separately verified native80-cell mapping.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import time
import numpy as np
import openvdb

sys.path.insert(0,str(Path(__file__).resolve().parent))
from water_feature_cell_volume import reconstructed_volume,reconstructed_volume_bounds
from water_feature_plane_flux import partial_face_flux
from water_feature_stage_interfaces import column_interface
from water_feature_cache_stages import decode_configuration,interval_clock


def digest(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reference-root',type=Path,required=True);parser.add_argument('--candidate-root',type=Path,required=True)
    parser.add_argument('--columns',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    if args.output.exists():raise FileExistsError(args.output)
    columns_report=json.loads(args.columns.read_text());columns=[r['column'] for r in columns_report['rows'][0]['derived_mesh']['columns']]
    if len(columns)!=54:raise ValueError('Retain complete54-column cohort')
    hashes={str(p.resolve()):digest(p) for p in (Path(__file__),args.columns)}
    for name in ('water_feature_cell_volume.py','water_feature_plane_flux.py','water_feature_stage_interfaces.py','water_feature_cache_stages.py'):
        p=Path(__file__).with_name(name);hashes[str(p.resolve())]=digest(p)
    frames=(1,24,48,72,96,120,144,168,192);shape=(80,21,42);h=.075;controls=[];start=time.perf_counter()
    for label,root in (('standard_padded',args.reference_root.resolve()),('fractional_padded',args.candidate_root.resolve())):
        setup=json.loads((root/'setup.json').read_text());bake=json.loads((root/'bake-data.json').read_text())
        proof=json.loads((root/'padding-preflight.json').read_text())
        if setup['fractional_obstacles']!=(label=='fractional_padded') or bake['data_frames']!=192 or not bake['baked_data']:
            raise ValueError('Complete matched native padded controls required')
        for p in (root/'setup.json',root/'bake-data.json',root/'padding-preflight.json',root/'domain-settings.json'):
            hashes[str(p.resolve())]=digest(p)
        rows=[];origin=np.array(proof['origin_m'])
        for frame in frames:
            data=root/'cache'/'data'/f'fluid_data_{frame:04d}.vdb';config=root/'cache'/'config'/f'config_{frame:04d}.uni'
            hashes[str(data)]=digest(data);hashes[str(config)]=digest(config);arrays={}
            clock=decode_configuration(config.read_bytes())
            if clock['resolution']!=list(shape):raise ValueError('Native allocation changed')
            for name,dt,vector in (('phi',np.float32,False),('phi_obstacle',np.float32,False),
                ('phi_obstacle_inflow',np.float32,False),('flags',np.int32,False),('velocity',np.float32,True)):
                g=openvdb.read(str(data),name)
                if tuple(g.metadata['file_base_resolution'])!=shape:raise ValueError('Native cached shape changed')
                a=np.empty((*shape,3) if vector else shape,dt);g.copyToArray(a)
                if not np.isfinite(a).all():raise ValueError('Nonfinite native array')
                arrays[name]=a
            phi,obs=arrays['phi'],arrays['phi_obstacle']
            volumes=[reconstructed_volume(phi,obs,(h,h,h),n) for n in ((8,16) if frame>=144 else (8,))]
            bounds=reconstructed_volume_bounds(phi,obs,(h,h,h),16) if frame in (144,168,192) else None
            sections=[]
            for x in (8,28,42,55,73):
                # Native x velocity lies on the lower x face. Neighbor-center
                # averages put phi/obstacle on that SAME physical face.
                face_phi=(phi[x-1].astype(float)+phi[x])/2
                face_obs=(obs[x-1].astype(float)+obs[x])/2
                velocity=arrays['velocity'][x,:,:,0].astype(float)/80
                estimates=[partial_face_flux(face_phi,face_obs,velocity,(h,h),n) for n in (16,32)]
                for estimate in estimates:
                    estimate['signed_positive_x_flux_m3s']=estimate.pop('signed_downward_flux_m3s')
                    estimate['positive_x_only_flux_m3s']=estimate.pop('downward_only_flux_m3s')
                    estimate['negative_x_only_flux_m3s']=estimate.pop('upward_only_flux_m3s')
                    estimate['mean_x_velocity_mps']=estimate.pop('mean_downward_velocity_mps')
                sections.append(dict(native_x_face_index=x,world_x_m=float(origin[0]+x*h),estimates=estimates,
                    liquid_adjacent_centers=int(np.count_nonzero((phi[x-1]<0)&(phi[x]<0)&(obs[x-1]>=0)&(obs[x]>=0)))))
            interfaces=[dict(column=c,**column_interface(phi,arrays['flags'],c,h)) for c in columns]
            row=dict(frame=frame,nominal_time_s=(frame-1)/24,native_cache_time_s=clock['time_total_native']/2.5,
                reconstructed_volume=volumes,reconstructed_volume_bounds=bounds,sections=sections,interfaces=interfaces,
                floor_obstacle_center_column=obs[54,10,:12].tolist(),floor_flags=arrays['flags'][54,10,:12].tolist())
            rows.append(row);print('PADDED_FRACTION_VOLUME',label,frame,[v['volume_m3'] for v in volumes],flush=True)
        clock=interval_clock(decode_configuration((root/'cache'/'config'/'config_0144.uni').read_bytes()),
            decode_configuration((root/'cache'/'config'/'config_0192.uni').read_bytes()),48,24)
        controls.append(dict(label=label,root=str(root),origin_m=origin.tolist(),shape=list(shape),cell_m=h,
            nominal_inlet_velocity_mps=setup['inlet_velocity_mps'],nominal_tailwater_m=setup['nominal_tailwater_m'],
            clock=clock,frames=rows))
    if controls[0]['origin_m']!=controls[1]['origin_m']:raise ValueError('Paired world-grid origins differ')
    if any(digest(p)!=sha for p,sha in hashes.items()):raise ValueError('Preserved inputs changed during volume/flux audit')
    report=dict(complete=True,accepted=False,originals_unchanged=True,dependency_sha256=hashes,controls=controls,
        elapsed_s=time.perf_counter()-start,scope=__doc__,
        caveats='Volumes/bounds belong to reconstructed trilinear fields, not physical conserved mass. Section integration is a diagnostic, not exact source/outflow budget. Every requested interface status retained. Quadrature refinement is not CFD resolution convergence. Native default fractional clearance/closed-border changes require independent acceptance; no volume correction or changed source.')
    with args.output.open('x') as stream:json.dump(report,stream,indent=2)


if __name__=='__main__':main()
