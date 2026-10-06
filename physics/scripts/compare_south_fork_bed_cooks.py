"""Audit equal-age full-domain bed comparisons; never infer visual acceptance."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[2]
CHANGED={'core_0628','core_0629','core_0630','core_0631'}


def sha(path):
    with Path(path).open('rb') as source:return hashlib.file_digest(source,'sha256').hexdigest()


def require(value,message):
    if not value:raise ValueError(message)


def same_physical_settings(old,new):
    require({k:v for k,v in old.items() if k!='metadata'}==
            {k:v for k,v in new.items() if k!='metadata'},'Changed physical scenario or numerical settings')


def compare(old_cook,new_cook,step):
    cooks=[Path(old_cook).resolve(),Path(new_cook).resolve()]
    manifests=[];inputs=[];frames=[];evidence=[]
    for cook in cooks:
        manifest_path=Path((cook/'input_manifest_path.txt').read_text().strip())
        if not manifest_path.is_absolute():manifest_path=ROOT/manifest_path
        require(sha(manifest_path)==sha(cook/'input_manifest.json'),'Changed cook input manifest')
        manifest=json.loads(manifest_path.read_text());manifests.append(manifest);inputs.append(manifest_path.parent)
        require(manifest['initialization_is_fresh_not_restart'] is True,'Fresh initialization required')
        record=json.loads((cook/f'frame_{step:06d}/complete.json').read_text())
        require(record['step']==step and record['snapshot'],'Incomplete snapshot')
        states={s:{name:np.load(cook/f'frame_{s:06d}/{name}.npy',mmap_mode='r',allow_pickle=False)
                   for name in ('h','u','v')} for s in (0,step)}
        for arrays in states.values():
            require(all(np.isfinite(a).all() for a in arrays.values()),'Nonfinite state')
            require(np.min(arrays['h'])>=0,'Negative depth')
        frames.append(states)
        evidence.append(dict(cook=str(cook),input_sha256=sha(manifest_path),time_seconds=record['time_seconds'],
            arrays={name:sha(cook/f'frame_{step:06d}/{name}.npy') for name in ('h','u','v')}))
        for row in manifest['inputs']:
            for name,digest in row['files'].items():
                require(sha(manifest_path.parent/row['name']/name)==digest,'Changed input: '+row['name']+'/'+name)
    old,new=manifests
    for key in ('dt_seconds','boundary_probes','target_discharge_m3s','authored_combined_inlet_discharge_m3s',
                'inferred_outlet_stage_relative_datum_m','vertical_datum_navd88_m','initial_velocity_method'):
        require(old[key]==new[key],'Different forcing: '+key)
    require(old['terrain_union']['cap_sha256']==new['terrain_union']['cap_sha256'],'Different rock solid')
    require(abs(evidence[0]['time_seconds']-evidence[1]['time_seconds'])<1.e-9,'Different source ages')
    require(new['packages'][:len(old['packages'])]==old['packages'],'Reordered or missing original cores')
    changed=[];bed_cells=0;seed_changes={k:0 for k in ('h','u','v')};state_changes={k:0 for k in seed_changes}
    for i,name in enumerate(old['packages']):
        scenarios=[json.loads((base/name/'scenario.json').read_text()) for base in inputs]
        same_physical_settings(*scenarios)
        ny,nx=scenarios[0]['grid']['ny'],scenarios[0]['grid']['nx']
        require(all(arr['h'].shape==(len(m['packages'])*ny,nx) for m,states in zip(manifests,frames)
                    for arr in states.values()),'Unexpected native stacked dimensions')
        beds=[np.load(base/name/'bed.npy',allow_pickle=False) for base in inputs]
        count=int(np.count_nonzero(beds[0]!=beds[1]))
        if count:changed.append(name);bed_cells+=count
        region=np.s_[i*ny:(i+1)*ny,:]
        for k in seed_changes:
            seed_changes[k]+=int(np.count_nonzero(frames[0][0][k][region]!=frames[1][0][k][region]))
            state_changes[k]+=int(np.count_nonzero(frames[0][step][k][region]!=frames[1][step][k][region]))
    require(set(changed)==CHANGED,'Bed changes outside the declared inferred-control revision')
    added=[]
    for i,name in enumerate(new['packages'][len(old['packages']):],start=len(old['packages'])):
        scenario=json.loads((inputs[1]/name/'scenario.json').read_text())
        require(name.startswith('context_') and all(b['kind']=='bank' for b in scenario['boundaries']),
                'Added physical boundary or non-context tile')
        ny=scenario['grid']['ny'];region=np.s_[i*ny:(i+1)*ny,:]
        for arrays in frames[1].values():
            require(all(np.all(a[region]==0.) for a in arrays.values()),'Added context contains water or motion')
        added.append(name)
    return dict(schema='raftsim.equal_age_bed_comparison.v1',passed=True,source=evidence,
        original_cores=len(old['packages']),revised_cores=len(new['packages']),changed_bed_cores=changed,
        changed_bed_cells=bed_cells,added_context_exactly_dry_at_initial_and_comparison=added,
        identical_common_physical_scenarios=True,identical_discharge_outlet_and_timestep=True,
        changed_initial_cells=seed_changes,changed_evolved_cells=state_changes,
        context_interior_wetness_between_snapshots_not_measured=True,
        solver_binary_identity_not_checked=True,settling_accepted=False,visual_accepted=False,
        normal_map_integrated=False)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('old_cook',type=Path);p.add_argument('new_cook',type=Path);p.add_argument('step',type=int)
    p.add_argument('--report',type=Path,required=True);a=p.parse_args()
    require(a.step>0,'Positive completed comparison step required')
    destination=a.report.resolve()
    require(destination.is_relative_to(ROOT/'tmp') and not destination.exists(),'Fresh project tmp report required')
    result=compare(a.old_cook,a.new_cook,a.step)
    with destination.open('x') as stream:json.dump(result,stream,indent=2);stream.write('\n')
    print(json.dumps(result,indent=2))
