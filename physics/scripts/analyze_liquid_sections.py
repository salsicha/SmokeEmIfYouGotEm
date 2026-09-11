"""Actual rendered wet sections and grid flow, with explicit reference limits.

Full-width longitudinal sections, not a rectangular-channel jump calibration.
Disconnected wet intervals count toward area; highest crossings do not fill air.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from analyze_liquid_surface_exchange import sample_grid,wet_column_integrals,audit_surface_exchange
from south_fork_registered_mesh import RegisteredMeshSampler


def analyze(directory):
    root=Path(__file__).resolve().parents[2]
    cp=directory/'capture.json';capture=json.loads(cp.read_text())
    if not capture['complete'] or capture['error']:raise ValueError('Complete capture required')
    wp=Path(capture['window_manifest']);window=json.loads(wp.read_text())
    gp=root/window['source_geometry_manifest'];geometry=json.loads(gp.read_text());mp=root/geometry['mesh_path']
    if hashlib.sha256(mp.read_bytes()).hexdigest()!=window['source_geometry_sha256']:raise ValueError('Geometry changed')
    rp=root/window['source_hydraulic_directory']/'../registration.json';registration=json.loads(rp.read_text())
    rotation=np.column_stack([registration['downstream_unit'],registration['left_unit']])
    source=directory/'live_foam_active';sp=source/'surface.rgba16f';vp=source/'foam_velocity.rgba16f'
    surface=np.fromfile(sp,dtype='<f2').reshape(48,136,136,4).astype(float)
    flow=np.fromfile(vp,dtype='<f2').reshape(24,68,68,4).astype(float)[...,:3]
    with np.load(mp) as mesh:bed=RegisteredMeshSampler(mesh)
    y=(np.arange(80)+.5)*.25-10
    z=np.unique(np.r_[350.,1150.,350+(np.arange(48)+.5)*800/48,350+(np.arange(24)+.5)*800/24])
    zz,yy=np.meshgrid(z,y*100,indexing='ij');records=[]
    for x in range(-9,10,2):
        en=np.column_stack([np.full_like(y,x),y])@rotation.T
        floor=bed.sample(en[:,0],en[:,1])*100
        xyz=np.stack([np.full_like(zz,x*100),yy,zz],axis=-1)
        phi=sample_grid(surface,xyz)[...,0];velocity=sample_grid(flow,xyz)
        depth,q,top=wet_column_integrals(z,phi,velocity[...,0],floor)
        _,lateral,_=wet_column_integrals(z,phi,velocity[...,1],floor)
        area=float(depth.sum()*.25/100);width=float((depth>0).sum()*.25)
        discharge=float(q.sum()*.25/10000);left=float(lateral.sum()*.25/10000)
        speed=discharge/area if area else 0;hydraulic_depth=area/width if width else 0
        records.append(dict(station_m=x,wet_area_m2=area,wet_width_m=width,
            downstream_velocity_integral_m3_s=discharge,lateral_velocity_area_integral_m3_s=left,
            section_mean_downstream_m_s=speed,hydraulic_depth_m=hydraulic_depth,
            section_froude_proxy=abs(speed)/np.sqrt(9.8*hydraulic_depth) if hydraulic_depth else None,
            highest_surface_datum_quantiles_m=np.quantile(top[np.isfinite(top)]/100,[.1,.5,.9]).tolist()))
    bp=wp.parent/'grid_boundary_profile.json'
    exchange=audit_surface_exchange(dict(SDF=surface[...,0:1],Velocity=flow),json.loads(bp.read_text()))
    return dict(capture=str(directory),sections=records,boundary_exchange=exchange,
        submerged_bed_authority=geometry['submerged_bed_authority'],
        limitations=['Single actual captured instant, not a time-integrated mass budget',
        'Velocity integral uses the collocated field; not a measured physical discharge',
        'Section Froude is an aggregate proxy; oblique flow, disconnected water and nonhydrostatic effects preclude a jump-depth calibration'],
        physical_or_visual_acceptance=False,
        source_sha256={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (cp,wp,gp,mp,rp,sp,vp,bp)})


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('directory',type=Path)
    args=p.parse_args();result=analyze(args.directory)
    with (args.directory/'wet_sections.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
    print(json.dumps(result['sections'],indent=2))
