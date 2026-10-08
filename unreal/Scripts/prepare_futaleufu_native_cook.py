"""Production Cartesian packages with an explicit, conserved two-inlet budget.

Flows are construction choices, not local measurements. No imposed interior
velocity, feature calibration, bathymetry changes or relaxed native gates.
"""
import argparse
import copy
import json
from pathlib import Path
import shutil

import numpy as np

from prepare_futaleufu_hydraulic_ports import ROOT, SIZE, FACES, sha

TEMPLATE=ROOT/'unreal/Plugins/SEIYGECore/data/validation/milestone17/analytic_fixtures/fixtures/lake_at_rest_balance/scenario/scenario.json'


def discharge_profiles(faces, target):
    if isinstance(target,bool) or not np.isfinite(target) or target<=0 or not faces:
        raise ValueError('Positive explicit inlet discharge and nonempty faces required')
    denominator=0.
    for face in faces:
        h=np.asarray(face['depth'],float);t=np.asarray(face['tangent'],float);normal=np.asarray(face['inward'],float)
        if (h.ndim!=1 or not np.isfinite(h).all() or np.any(h<0) or t.shape!=(2,) or normal.shape!=(2,)
                or not np.isfinite([*t,*normal]).all() or abs(np.linalg.norm(t)-1)>1e-8
                or abs(np.linalg.norm(normal)-1)>1e-8 or np.dot(t,normal)<=0):
            raise ValueError('Finite positive-depth profiles, unit directions and inward flow required')
        denominator+=float(np.sum(h**(5/3))*np.dot(t,normal))
    if denominator<=0: raise ValueError('Inlet has no positive conveyance')
    result=[];carried=0.
    for face in faces:
        h=np.asarray(face['depth']);t=np.asarray(face['tangent'])
        speed=target*h**(2/3)/denominator
        if np.max(speed)>20.: raise ValueError('Authored inlet exceeds native speed gate; no velocity clipping')
        uv=speed[:,None]*t
        carried+=float(np.sum(h*(uv@face['inward'])))
        result.append(uv)
    if abs(carried-target)>1e-10*max(target,1): raise ValueError('Inlet profile fails exact discharge accounting')
    return result,carried


def build(ports_folder, output, azul_m3s, mainstem_m3s):
    ports_folder,output=[Path(p).resolve() for p in (ports_folder,output)]
    output.relative_to(ROOT)
    if output.exists(): raise ValueError('Fresh native package directory required')
    if shutil.disk_usage(ROOT).free<42*1024**3: raise ValueError('Preserve 40 GiB reserve and construction allowance')
    source_path=ports_folder/'manifest.json';m=json.loads(source_path.read_text())
    if (m.get('schema')!='raftsim.futaleufu_hydraulic_ports.v1' or m['errors']
            or not m['common_original_route_components'] or m['removed_positive_depth_interior_cells']
            or m['spacing_m']!=1 or m['tile_cells']!=[SIZE,SIZE] or m['rows_increase']!='north'):
        raise ValueError('Accepted geometric ports with complete original route required')
    flows=dict(rio_azul=azul_m3s,upstream_mainstem=mainstem_m3s)
    if any(isinstance(q,bool) or not np.isfinite(q) or q<=0 for q in flows.values()):
        raise ValueError('Explicit positive finite two-inlet flow budget required')
    pins={ROOT/p:h for p,h in m['sources_sha256'].items()}
    for p in (source_path,TEMPLATE,Path(__file__).resolve()):pins[p]=sha(p)
    def verify():
        for p,h in pins.items():
            if sha(p)!=h: raise ValueError('Changed native package input: '+str(p))
    verify()
    rows=sorted(m['tiles'],key=lambda r:r['chunk']);keys=[tuple(r['chunk']) for r in rows]
    if len(set(keys))!=len(keys): raise ValueError('Duplicate hydraulic tiles')
    arrays={}
    for index,row in zip(keys,rows):
        path=ports_folder/row['file'];pins[path]=row['sha256']
        if sha(path)!=pins[path]:raise ValueError('Changed water tile')
        with np.load(path,allow_pickle=False) as z:arrays[index]={k:z[k].copy() for k in z.files}
    boundaries={};inlet_receipts={}
    for name,q in flows.items():
        port=next(p for p in m['ports'] if p['branch']==name)
        faces=[]
        for row in m['boundaries']:
            if row['branch']!=name:continue
            index=tuple(row['tile']);sl,neighbor,_,_=FACES[row['edge']]
            a=arrays[index]
            faces.append(dict(key=(index,row['edge']),depth=a['initial_depth_m'][sl],
                bed=a['bed_m'][sl]-150.,tangent=port['tangent_east_north'],inward=-np.array(neighbor)))
        velocities,carried=discharge_profiles(faces,q)
        for f,uv in zip(faces,velocities):
            ghost=np.c_[f['bed'],f['depth'],uv]
            boundaries[f['key']]=dict(kind='discharge_profile',ghost_cells=np.tile(ghost,(2,1)).tolist(),role='upstream',branch=name)
        inlet_receipts[name]=dict(target_m3s=q,profile_normal_discharge_m3s=carried,faces=len(faces),
            maximum_ghost_speed_mps=max(float(np.linalg.norm(v,axis=1).max()) for v in velocities))
    for row in m['boundaries']:
        if row['role']!='downstream':continue
        index=tuple(row['tile']);sl=FACES[row['edge']][0];a=arrays[index]
        stage=float(np.median(a['reference_stage_m'][sl][a['initial_depth_m'][sl]>0]))-150.
        boundaries[(index,row['edge'])]=dict(kind='outflow',stage=stage,role='downstream',branch=row['branch'])
    template=json.loads(TEMPLATE.read_text());origin=np.array(m['horizontal_origin_m']);output.mkdir(parents=True)
    names=[];inputs=[];probes=[]
    for ordinal,index in enumerate(keys):
        name='tile_%d_%d'%index;folder=output/name;folder.mkdir();names.append(name)
        a=arrays[index];h=a['initial_depth_m'];bed=a['bed_m']-150.;zero=np.zeros(h.shape)
        if h.shape!=(SIZE,SIZE) or not np.isfinite([h,bed]).all() or np.any(h<0) or h.max()>10:
            raise ValueError('Initial arrays fail native depth/finite gates')
        np.save(folder/'bed.npy',bed)
        np.savez_compressed(folder/'initial_state.npz',depth=h,eta=bed+h,u=zero,v=zero,hu=zero,hv=zero,wet=h>1e-6)
        (folder/'features.json').write_text('{"features":[]}\n');(folder/'probes.json').write_text('{"probes":[]}\n')
        sc=copy.deepcopy(template)
        sc['metadata']=dict(scenario_id=name,scenario_type='real_world',fixture_kind=None,river_id='futaleufu_river_chile',
            flow_band='explicit_inferred_construction',generator='prepare_futaleufu_native_cook.py',generator_version='20261008-v1',
            description='Full captured buffered three-arm river, encoded Landscape bed; cold start, not accepted',confidence_score=.3,
            coordinate_reference_system='Unrotated EPSG:32718 relative to '+str(origin.tolist())+'; EGM2008 minus 150 m',
            provenance=dict(ports_manifest_sha256=sha(source_path),measured_bathymetry=False,measured_discharge=False))
        sc['grid']=dict(nx=SIZE,ny=SIZE,dx=1.,dy=1.,origin_x=index[0]*SIZE+.5,origin_y=index[1]*SIZE+.5)
        sc.update(fixed_dt=.01,duration=600.,roughness=.045,feature_count=0,probe_count=0)
        sc['boundaries']=[]
        for edge in FACES:
            row=dict(edge=edge,kind='bank');bd=boundaries.get((index,edge))
            if bd:
                row.update({k:v for k,v in bd.items() if k not in ('role','branch')})
                probes.append(dict(tile_index=ordinal,edge=edge,role=bd['role'],branch=bd['branch']))
            sc['boundaries'].append(row)
        (folder/'scenario.json').write_text(json.dumps(sc,indent=2,allow_nan=False)+'\n')
        inputs.append(dict(name=name,files={f:sha(folder/f) for f in ('scenario.json','bed.npy','initial_state.npz','features.json','probes.json')}))
    verify()
    report=dict(schema='raftsim.cartesian_flow_cook.v1',dt_seconds=.01,packages=names,boundary_probes=probes,
        tile_indices=[list(k) for k in keys],grid=dict(cell_m=1.,tile_cells=SIZE),
        horizontal_origin_utm18s_m=origin.tolist(),vertical_datum_m=150.,
        sources_sha256={p.relative_to(ROOT).as_posix():h for p,h in pins.items()},inputs=inputs,
        inlet_budget=inlet_receipts,combined_inlet_discharge_m3s=float(sum(flows.values())),
        flow_basis='Explicit inferred construction split; not simultaneous local gauge observations',
        initial_state='Exact encoded-terrain initial depths, zero interior velocity, no feature calibration',
        measured_discharge=False,measured_bathymetry=False,settled_hydraulics=False,normal_map_integrated=False)
    (output/'manifest.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    print(json.dumps(dict(tiles=len(keys),cells=len(keys)*SIZE*SIZE,inlet_budget=inlet_receipts,
                         combined_inlet_discharge_m3s=sum(flows.values()))),flush=True)
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--ports',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--azul-m3s',type=float,required=True);p.add_argument('--mainstem-m3s',type=float,required=True)
    a=p.parse_args();build(a.ports,a.out,a.azul_m3s,a.mainstem_m3s)
