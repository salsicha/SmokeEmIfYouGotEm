"""Actual192-frame wall coverage and paired-volume inputs; no cache edits."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import time
import numpy as np
import openvdb
sys.path.insert(0,str(Path(__file__).resolve().parent))
from water_feature_field_surface import sample_centers
from water_feature_cell_volume import reconstructed_volume,reconstructed_volume_bounds
from water_feature_plane_flux import partial_face_flux
from water_feature_cache_stages import decode_configuration,interval_clock


def digest(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    if args.output.exists():raise FileExistsError(args.output)
    root=args.root.resolve();proof=json.loads((root/'padding-preflight.json').read_text());bake=json.loads((root/'bake-data.json').read_text())
    if not proof['explicit_wall_control'] or not bake['baked_data'] or bake['data_frames']!=192:raise ValueError('Completed explicit wall scene required')
    shape=tuple(proof['shape']);h=proof['cell_m'];origin=np.array(proof['origin_m']);started=time.perf_counter();hashes=dict(proof['dependency_sha256'])
    if shape!=(90,31,42) or h!=.075:raise ValueError('Matched allocated shape required')
    for p in (Path(__file__),root/'padding-preflight.json',root/'bake-data.json',root/'setup.json',root/'domain-settings.json',root/'feature.blend'):
        hashes[str(p.resolve())]=digest(p)
    for name in ('water_feature_field_surface.py','water_feature_cell_volume.py','water_feature_plane_flux.py','water_feature_cache_stages.py'):
        p=Path(__file__).with_name(name);hashes[str(p.resolve())]=digest(p)
    for folder in ('data','config'):
        for p in (root/'cache'/folder).rglob('*'):
            if p.is_file():hashes[str(p.resolve())]=digest(p)
    if any(digest(p)!=s for p,s in hashes.items()):raise ValueError('Pinned evidence changed')
    points=np.array([[4.05,0,0],[4.05,-.8,.75],[4.05,.8,.75],[0,0,.9],[6,0,.9]])
    base=(points-origin)/h;normals=np.array([[0,0,1],[0,1,0],[0,-1,0],[1,0,0],[-1,0,0]])
    allpoints=points[:,None,:]+np.array([-.025,0,.025])[None,:,None]*normals[:,None,:]
    stations=[];rows=[]
    for frame in range(1,193):
        path=root/'cache'/'data'/f'fluid_data_{frame:04d}.vdb';grid=openvdb.read(str(path),'phi_obstacle')
        if tuple(grid.metadata['file_base_resolution'])!=shape:raise ValueError('Actual native allocation differs')
        obs=np.empty(shape,np.float32);grid.copyToArray(obs)
        if not np.isfinite(obs).all():raise ValueError('Nonfinite obstacle field')
        values=sample_centers(obs,(allpoints.reshape(-1,3)-origin)/h).reshape(5,3)
        stations.append(dict(frame=frame,values_cells=values.tolist(),maximum_surface_error_m=float(np.abs(values[:,1]).max()*h),
            signs_at_minus_plus_25mm_correct=bool(np.all(values[:,0]<0)&np.all(values[:,2]>0))))
        if frame not in (1,24,48,72,96,120,144,168,192):continue
        phi=np.empty(shape,np.float32);openvdb.read(str(path),'phi').copyToArray(phi)
        vel=np.empty((*shape,3),np.float32);openvdb.read(str(path),'velocity').copyToArray(vel)
        if not np.isfinite(phi).all() or not np.isfinite(vel).all():raise ValueError('Nonfinite actual liquid field')
        config=decode_configuration((root/'cache'/'config'/f'config_{frame:04d}.uni').read_bytes())
        if config['resolution']!=list(shape):raise ValueError('Configuration shape differs')
        volumes=[reconstructed_volume(phi,obs,(h,h,h),n) for n in ((8,16) if frame>=144 else (8,))]
        sections=[]
        for oldx in (8,28,42,55,73):
            x=oldx+5;p=(phi[x-1].astype(float)+phi[x])/2;o=(obs[x-1].astype(float)+obs[x])/2
            estimates=[partial_face_flux(p,o,vel[x,:,:,0].astype(float)*h*2.5,(h,h),n) for n in (16,32)]
            for e in estimates:
                e['signed_positive_x_flux_m3s']=e.pop('signed_downward_flux_m3s');e['mean_x_velocity_mps']=e.pop('mean_downward_velocity_mps')
                e['positive_x_only_flux_m3s']=e.pop('downward_only_flux_m3s');e['negative_x_only_flux_m3s']=e.pop('upward_only_flux_m3s')
            sections.append(dict(native_x_face_index=x,world_x_m=float(origin[0]+x*h),estimates=estimates))
        rows.append(dict(frame=frame,nominal_time_s=(frame-1)/24,native_cache_time_s=config['time_total_native']/2.5,
            reconstructed_volume=volumes,reconstructed_volume_bounds=reconstructed_volume_bounds(phi,obs,(h,h,h),16) if frame>=144 else None,
            sections=sections))
        print('EXPLICIT_NATIVE_FIELDS_FRAME',root.name,frame,[v['volume_m3'] for v in volumes],flush=True)
    wallgate=all(r['maximum_surface_error_m']<1e-5 and r['signs_at_minus_plus_25mm_correct'] for r in stations)
    before=decode_configuration((root/'cache'/'config'/'config_0144.uni').read_bytes());after=decode_configuration((root/'cache'/'config'/'config_0192.uni').read_bytes())
    if any(digest(p)!=sha for p,sha in hashes.items()):raise ValueError('Source changed during audit')
    report=dict(complete=True,accepted=False,originals_unchanged=True,dependency_sha256=hashes,root=str(root),source_blend=str(root/'feature.blend'),
        shape=list(shape),origin_m=origin.tolist(),cell_m=h,wall_stations_m=points.tolist(),station_offsets_into_fluid_m=[-.025,0,.025],
        wall_frames=stations,explicit_wall_station_gate=wallgate,maximum_wall_surface_error_m=max(r['maximum_surface_error_m'] for r in stations),
        frames=rows,physical_mac_velocity_scale=h*2.5,clock=interval_clock(before,after,48,24),elapsed_s=time.perf_counter()-started,
        scope=__doc__,caveats='Actual cached Blender-voxelized surfaces at five fixed planar stations. Not exhaustive wall/corner contact, conserved mass, exact drain budget or pressure/spatial convergence. Stock mesh/secondary phases and complete feature acceptance remain separate.')
    with args.output.open('x') as stream:json.dump(report,stream,indent=2)
    print('EXPLICIT_NATIVE_FIELDS_COMPLETE',root.name,wallgate,report['maximum_wall_surface_error_m'],flush=True)


if __name__=='__main__':main()
