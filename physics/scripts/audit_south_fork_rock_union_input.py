"""Audit a fresh full-domain candidate cook; never infer settled acceptance."""
import argparse
import json
from pathlib import Path
import numpy as np
from south_fork_rock_union import sha

ROOT=Path(__file__).resolve().parents[2]


def validate_fresh_package(scenario,prior,bed,state,geometry,datum):
    for key in ('grid','boundaries','roughness','fixed_dt'):
        if scenario[key]!=prior[key]:raise ValueError('Changed retained physical setup: '+key)
    if not np.array_equal(bed,geometry['bed_navd88_m']-datum):
        raise ValueError('Flow bed differs from source union')
    h,u,v=(state[k] for k in ('depth','u','v'))
    if any(a.shape!=(80,80) or not np.isfinite(a).all() for a in (h,u,v)):
        raise ValueError('Invalid fresh state shape or values')
    if h.min()<0 or h.max()>10 or np.hypot(u,v).max()>20:
        raise ValueError('Fresh state exceeds retained depth/speed gate')
    expected=np.where(geometry['captured_water_mask'].astype(bool),
        np.maximum((geometry['captured_surface_navd88_m']-datum)-bed,0.),0.)
    if not np.array_equal(h,expected):raise ValueError('Initial water is not the declared fresh source-stage seed')
    for key,value in [('eta',bed+h),('hu',h*u),('hv',h*v),('wet',h>1.e-6)]:
        if not np.array_equal(state[key],value):raise ValueError('Inconsistent conserved initial field: '+key)


def audit(path,report):
    path=Path(path).resolve();report=Path(report).resolve()
    if report.exists():raise ValueError('Preserve earlier input audits')
    flow=json.loads(path.read_text())
    if not flow.get('initialization_is_fresh_not_restart') or 'restart' in flow or flow.get('initial_time_seconds',0)!=0:
        raise ValueError('New geometry requires an explicitly fresh cook')
    gp=ROOT/flow['geometry_manifest']
    if sha(gp)!=flow['geometry_manifest_sha256']:raise ValueError('Changed union geometry manifest')
    geometry=json.loads(gp.read_text());bp=ROOT/geometry['retained_flow_manifest']
    if sha(bp)!=geometry['retained_flow_manifest_sha256']:raise ValueError('Changed retained flow manifest')
    base=json.loads(bp.read_text())
    for key in ('packages','boundary_probes','dt_seconds','target_discharge_m3s'):
        if flow[key]!=base[key]:raise ValueError('Changed full-domain forcing/layout: '+key)
    if flow['packages']!=[r['name'] for r in geometry['regions']]:raise ValueError('Core order differs')
    datum=flow['vertical_datum_navd88_m'];total=0.;count=0;q=0.
    for name,record,original,core in zip(flow['packages'],flow['inputs'],base['inputs'],geometry['regions']):
        if name!=record['name'] or name!=original['name']:raise ValueError('Input identity order differs')
        for root,item in [(path.parent,record),(bp.parent,original)]:
            for file,digest in item['files'].items():
                if sha(root/name/file)!=digest:raise ValueError('Changed input dependency: '+name+'/'+file)
        cp=ROOT/core['geometry_file']
        if sha(cp)!=core['geometry_sha256']:raise ValueError('Changed physical core')
        scenario=json.loads((path.parent/name/'scenario.json').read_text())
        prior=json.loads((bp.parent/name/'scenario.json').read_text())
        bed=np.load(path.parent/name/'bed.npy',allow_pickle=False)
        with np.load(path.parent/name/'initial_state.npz',allow_pickle=False) as state,np.load(cp,allow_pickle=False) as source:
            validate_fresh_package(scenario,prior,bed,state,source,datum)
            total+=float(state['depth'].sum());count+=bed.size
        for boundary in scenario['boundaries']:
            if boundary['kind']!='discharge_profile':continue
            ghost=np.asarray(boundary['ghost_cells']);edge=boundary['edge']
            if ghost.shape!=(160,4) or not np.isfinite(ghost).all():raise ValueError('Invalid physical inlet profile')
            sign=1 if edge in ('west','south') else -1
            flux=sign*ghost[:80,1]*ghost[:80,2 if edge in ('west','east') else 3]
            if np.any(flux<0):raise ValueError('Reversed physical inlet')
            q+=float(flux.sum())
    if abs(q-flow['target_discharge_m3s'])>=1.e-12:raise ValueError('Changed imposed inlet discharge')
    result=dict(passed=True,manifest_sha256=sha(path),geometry_manifest_sha256=sha(gp),
        retained_flow_manifest_sha256=sha(bp),checked_cores=len(flow['packages']),checked_cells=count,
        fresh_source_stage_initial_volume_m3=total,imposed_inlet_discharge_m3s=q,
        original_domain_boundaries_and_roughness_unchanged=True,all_dependencies_hash_verified=True,
        source_union_bed_exact=True,no_evolved_state_transfer=True,
        hydraulic_settling_accepted=False,native_collision_accepted=False,playable_integrated=False)
    report.write_text(json.dumps(result,indent=2)+'\n');return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input',type=Path);parser.add_argument('--report',type=Path,required=True)
    args=parser.parse_args();print(json.dumps(audit(args.input,args.report),indent=2),flush=True)
