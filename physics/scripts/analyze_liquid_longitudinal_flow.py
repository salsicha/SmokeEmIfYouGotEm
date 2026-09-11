"""Longitudinal strip of actual GPU water and registered bed, not river acceptance.

The surface velocity is not depth averaged and the bed may be inferred. No
Froude/hydraulic-jump claim is made from the surface-only velocity samples.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from liquid_current_surface_foam import sample
from south_fork_registered_mesh import RegisteredMeshSampler


def top_crossings(surface):
    surface=np.asarray(surface,dtype=float)
    if surface.ndim!=4 or surface.shape[-1]!=4 or not np.isfinite(surface).all():
        raise ValueError('Finite ZYX RGBA surface required')
    phi=surface[...,0]
    cross=(phi[:-1]<0)&(phi[1:]>=0)
    height=np.where(cross,np.arange(len(phi)-1)[:,None,None],-1).max(axis=0)
    y,x=np.nonzero(height>=0);z=height[y,x]
    fraction=-phi[z,y,x]/(phi[z+1,y,x]-phi[z,y,x])
    return np.stack(((x+.5)/phi.shape[2],(y+.5)/phi.shape[1],
                     (z+.5+fraction)/phi.shape[0]),axis=-1)


def analyze(directory,lateral,half_width=1.):
    root=Path(__file__).resolve().parents[2]
    capture_path=directory/'capture.json';capture=json.loads(capture_path.read_text())
    if not capture['complete'] or capture['error'] or not np.isfinite(lateral) or not 0<half_width<=4:
        raise ValueError('Complete capture and bounded strip required')
    window_path=Path(capture['window_manifest']);window=json.loads(window_path.read_text())
    geometry_path=root/window['source_geometry_manifest'];geometry=json.loads(geometry_path.read_text())
    mesh_path=root/geometry['mesh_path']
    if hashlib.sha256(mesh_path.read_bytes()).hexdigest()!=window['source_geometry_sha256']:
        raise ValueError('Captured terrain identity changed')
    registration_path=root/window['source_hydraulic_directory']/'../registration.json'
    registration=json.loads(registration_path.read_text())
    rotation=np.column_stack([registration['downstream_unit'],registration['left_unit']])
    if not np.allclose(rotation.T@rotation,np.eye(2),atol=1e-9) or np.linalg.det(rotation)<0:
        raise ValueError('Invalid hydraulic coordinate frame')
    active=directory/'live_foam_active'
    surface_path=active/'surface.rgba16f';velocity_path=active/'foam_velocity.rgba16f'
    surface=np.fromfile(surface_path,dtype='<f2').reshape(48,136,136,4).astype(float)
    velocity=np.fromfile(velocity_path,dtype='<f2').reshape(24,68,68,4).astype(float)
    if not np.isfinite(velocity).all():raise ValueError('Finite captured velocity required')
    unit=top_crossings(surface);xy=(unit[:,:2]-.5)*22.3125
    eta=unit[:,2]*8+window['local_origin_engine_cm'][2]/100
    en=xy@rotation.T
    with np.load(mesh_path) as mesh:bed=RegisteredMeshSampler(mesh).sample(en[:,0],en[:,1])
    flow=sample(velocity,unit)[:,:3]/100
    coverage=sample(surface,unit)[:,1]
    strip=abs(xy[:,1]-lateral)<half_width
    if not strip.any():raise ValueError('Strip has no water surface crossings')
    records=[]
    for station in range(-9,10):
        selected=strip&(abs(xy[:,0]-station)<.5)
        if not selected.any():raise ValueError(f'No top crossing at station {station}')
        values=np.column_stack([bed,eta,eta-bed,flow,coverage])[selected]
        if not np.isfinite(values).all():raise ValueError('Missing registered bed or water value')
        records.append(dict(station_m=station,columns=int(selected.sum()),
            quantiles=np.quantile(values,[.1,.5,.9],axis=0).tolist(),
            upstream_surface_velocity_fraction=float((flow[selected,0]<0).mean())))
    files=[capture_path,window_path,geometry_path,mesh_path,registration_path,surface_path,velocity_path]
    return dict(schema='raftsim.liquid_longitudinal_flow.v1',
        simulation_seconds=capture['simulation_steps']/60,lateral_centre_m=lateral,
        strip_half_width_m=half_width,quantile_probabilities=[.1,.5,.9],
        columns=['bed_datum_m','surface_datum_m','bed_clearance_m','surface_downstream_m_s',
                 'surface_left_m_s','surface_up_m_s','surface_coverage'],stations=records,
        submerged_bed_authority=geometry['submerged_bed_authority'],
        limitations=['Highest upward SDF crossing omits overhangs and interior circulation',
                     'Surface velocity is not depth averaged; no hydraulic-jump or discharge acceptance',
                     'One instant and one selected strip, not full-rapid or photographic acceptance'],
        source_sha256={str(p.resolve().relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files})


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory',type=Path);parser.add_argument('--lateral',type=float,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();result=analyze(args.directory,args.lateral)
    with args.output.open('x') as stream:json.dump(result,stream,indent=2);stream.write('\n')
    print(json.dumps(result,indent=2))
