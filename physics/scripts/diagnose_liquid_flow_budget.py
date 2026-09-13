"""Account compact native water storage up to the FIRST failed transaction.

The supplied timestep is the diagnostic runner's requested advance, not measured
game FPS or independently measured GPU simulation time. No per-exit trajectory,
physical discharge calibration, steady-flow or visual acceptance is claimed.
"""
import argparse
import json
from pathlib import Path
import numpy as np
from audit_liquid_native_compact import verify_summary
from audit_liquid_native_generation import verify_generation
from liquid_stage_journal import stage_groups
from liquid_dataset import resolve


def budget(history,planned,initial,volume,dt):
    if (type(initial) is not int or initial<=0 or not np.isfinite([volume,dt]).all() or
            volume<=0 or not 0<dt<=1):
        raise ValueError('Positive initial population, particle volume and requested timestep required')
    failed=next((i for i,h in enumerate(history) if h['control'][0]!=1),len(history))
    prefix=history[:failed]
    live,exits=verify_summary(prefix,planned,initial)
    bins=[];width=max(1,round(1/dt));running=initial
    for offset in range(0,len(prefix),width):
        rows=prefix[offset:offset+width]
        incoming=sum(sum(planned[h['native_step']].values()) for h in rows)
        outgoing=sum(h['control'][3] for h in rows)
        after=int(sum(rows[-1]['counts']))
        if after!=running+incoming-outgoing:raise ValueError('Bin storage accounting mismatch')
        duration=len(rows)*dt
        bins.append(dict(first_native_step=rows[0]['native_step'],last_native_step=rows[-1]['native_step'],
            requested_duration_seconds=duration,births=incoming,exits=outgoing,
            nominal_inflow_m3_s=incoming*volume/duration,nominal_outflow_m3_s=outgoing*volume/duration,
            nominal_storage_change_m3=(after-running)*volume))
        running=after
    births=sum(sum(planned[h['native_step']].values()) for h in prefix)
    return dict(schema='raftsim.liquid_compact_storage_diagnosis.v1',
        initial_particles=initial,verified_compact_commits=len(prefix),recorded_commits=len(history),
        first_failed_native_step=history[failed]['native_step'] if failed<len(history) else None,
        first_failed_control=history[failed]['control'] if failed<len(history) else None,
        verified_births=births,approved_exit_count=int(exits.sum()),survivors_after_last_verified_commit=live,
        nominal_particle_volume_m3=volume,nominal_storage_change_m3=(live-initial)*volume,
        requested_step_seconds=dt,requested_verified_duration_seconds=len(prefix)*dt,
        approved_exits_by_owner_face=exits.tolist(),intervals=bins,
        full_recorded_commit_sequence_verified=failed==len(history),
        exact_per_exit_trajectory_verified=False,measured_gpu_timestep=False,
        physical_discharge_or_steady_flow_acceptance=False,visual_or_performance_acceptance=False)


def diagnose(directory,dt):
    directory=Path(directory);d=json.loads((directory/'stages.json').read_text())
    verify_generation(d)
    package=resolve(d)
    regions=[json.loads((package['regions']/f'region-{i:03d}.json').read_text()) for i in range(12)]
    volumes={r['nominal_particle_volume_m3'] for r in regions}
    if len(volumes)!=1:raise ValueError('One nominal particle volume required')
    groups=[g for g in stage_groups(d) if g['entries'][0]['first']]
    planned={step:{e['owner']:e['native_rate_spawns']+e['native_event_spawns'] for e in group['entries']}
        for step,group in enumerate(groups,1)}
    initial=sum(len(r['seed_parent_ids']) for r in regions)
    for region,record in zip(regions,d['native_transfer_packet'],strict=True):
        if (region['seed_parent_ids']!=record['seed_parent_ids'] or
                np.float32(region['nominal_particle_volume_m3'])!=np.float32(record['particle_volume_m3'])):
            raise ValueError('Native seed identity or particle volume differs from prepared budget')
    if sum(planned[1].values())!=initial:raise ValueError('Initial population differs from original regional seeds')
    result=budget(d['native_particle_handoff_history'],planned,initial,volumes.pop(),dt)
    result.update(native_dataset=d.get('native_dataset'),simulation_generation=d['simulation_generation'])
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('directory',type=Path)
    p.add_argument('--requested-step-seconds',type=float,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    if a.output.exists():raise FileExistsError(a.output)
    r=diagnose(a.directory,a.requested_step_seconds)
    a.output.write_text(json.dumps(r,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:v for k,v in r.items() if k not in ('approved_exits_by_owner_face','native_dataset')},indent=2))
