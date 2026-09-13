"""Audit original dense seeds, native budgets and source-defined storage state.

Compact telemetry cannot establish exact per-exit trajectory/payload history.
Internal storage owners use the declared native coordinate precision, with a
separate survey-double comparison and unchanged physical exterior check.
This is not visual, sustained-discharge or performance acceptance.
"""
import json
import hashlib
from pathlib import Path
import numpy as np
from liquid_stage_journal import stage_groups
from liquid_dataset import resolve as resolve_dataset

from audit_liquid_native_compact import verify_summary
from audit_liquid_native_generation import verify_generation
from audit_liquid_native_handoff import read
from audit_liquid_particle_routes import storage_owners, verify_packet
from audit_liquid_native_neighbors import audit_record
from diagnose_liquid_first_rejection import decode as decode_rejection


def audit(directory, log_path=None):
    directory=Path(directory).resolve();repo=Path(__file__).resolve().parents[2]
    d=json.loads((directory/'stages.json').read_text());c=json.loads((directory/'capture.json').read_text())
    if 'native_physical_frame_model' in d and d['native_physical_frame_model'] not in ('double-float-demote-v1','double-float-residual-outer-v2'):
        raise ValueError('Unknown or null native storage-coordinate contract')
    if d.get('native_physical_frame_model')=='double-float-residual-outer-v2':
        sources=json.loads((directory/'boundary-sources.json').read_text())
        expected={'Shaders/Private/RaftSimLiquidPhysicalFrame.ush',
            'Shaders/Private/RaftSimLiquidParticleRouting.usf','Shaders/Private/RaftSimLiquidParticleExit.usf',
            'Source/RaftSimWaterDetail/Public/RaftSimLiquidParticleRoutingGPU.h',
            'Source/RaftSimWaterDetail/Private/RaftSimLiquidParticleRoutingGPU.cpp',
            'Source/RaftSimWaterDetail/Private/RaftSimLiquidParticleExitGPU.cpp',
            'Source/RaftSimEditor/Private/Materials/RaftSimEditorLiquidRegionalStageProbe.cpp'}
        if d.get('native_advection_velocity_halo_exchange', False):
            expected.update({'Source/RaftSimWaterDetail/Public/RaftSimLiquidHaloGPU.h',
                'Source/RaftSimWaterDetail/Private/RaftSimLiquidHaloGPU.cpp',
                'Shaders/Private/RaftSimLiquidHalo.usf'})
        if d.get('native_high_order_interface_requested', False):
            expected.update({'Shaders/Private/RaftSimLiquidInterfaceHighOrder.usf',
                'Source/RaftSimWaterDetail/Public/RaftSimLiquidInterfaceHighOrderGPU.h',
                'Source/RaftSimWaterDetail/Private/RaftSimLiquidInterfaceHighOrderGPU.cpp',
                'Source/RaftSimEditor/Private/Materials/RaftSimLiquidInterfaceRuntime.h'})
        if (not c.get('boundary_sources_unchanged') or sources.get('schema')!='raftsim.liquid_boundary_sources.v1' or
                set(sources['files_sha256'])!=expected):
            raise ValueError('Complete immutable residual boundary implementation snapshots required')
        for name,digest in sources['files_sha256'].items():
            if hashlib.sha256((directory/'boundary-sources'/name).read_bytes()).hexdigest()!=digest:
                raise ValueError('Residual boundary source snapshot changed')
    log=Path(log_path or directory.with_suffix('.log')).read_text(errors='replace')
    if (not c['complete'] or d['exchange_error'] or not d['native_transfer_packet_saved'] or
        not d.get('native_dense_requested') or not d['native_compact_handoff_requested'] or
        not d['parent_exterior_forcing_installed'] or not d['native_particle_retirement_requested'] or
        not d['native_emission_activated'] or d['native_emission_requested'] or d['native_empty_receiver_requested'] or
        '-RHIValidation' not in log or any(t in log for t in ('LogRHI: Error','Fatal error:','GPU Crashed'))):
        raise ValueError('Successful original dense native replay with parent forcing required')
    verify_generation(d)
    records=d['native_transfer_packet'];history=d['native_particle_handoff_history'];step=d['native_transfer_packet_step']
    if step>12 and not d.get('native_exact_exit_bed'):
        raise ValueError('Extended dense flow requires pointwise contact-terrain outlet bed, not midpoint rows')
    if [r['region_id'] for r in records]!=list(range(12)) or len(history)!=d['native_particle_handoff_count'] or step!=history[-1]['native_step']+1:
        raise ValueError('Complete continuous dense capture required')
    dataset=resolve_dataset(d)
    regions=[json.loads((dataset['regions']/f'region-{i:03d}.json').read_text()) for i in range(12)]
    planned={s:{e['owner']:e['native_rate_spawns']+e['native_event_spawns'] for e in g['entries']}
             for s,g in enumerate([g for g in stage_groups(d) if g['entries'][0]['first']][:step],1)}
    if len(planned)!=step:raise ValueError('Missing actual dense native birth plan')
    initial=[];initial_positions=[];volumes=[]
    for r,region in zip(records,regions):
        owner=r['region_id'];n=r['birth_particle_count'];expected=len(region['seed_parent_ids'])
        if n!=expected or r['expected_count']!=n or r['seed_parent_ids']!=region['seed_parent_ids'] or planned[1][owner]!=n:
            raise ValueError('Dense native burst omitted or substituted original wet seeds')
        ids=read(directory,r,'birth_identities',(n,4))
        if np.any(ids[:,0]!=owner) or not np.array_equal(np.sort(ids[:,1]),np.arange(n)) or not np.array_equal(ids[:,2],ids[:,1]):
            raise ValueError('Dense original birth identities differ')
        # Native parallel spawn compaction may reorder rows. Immutable birth
        # sequence, not storage order, identifies the original prepared seed.
        p=read(directory,r,'birth_positions',(n,4)).view('<f4')[:,:3][np.argsort(ids[:,1])]
        expected_p=np.asarray(region['positions_canonical_cm'],dtype='<f4').reshape(-1,3)*[1,-1,1]
        if not np.allclose(p,expected_p,atol=0.002,rtol=0):raise ValueError('Original dense water positions changed')
        if not np.isclose(d['prepared_spawn_rates'][owner],region['external_spawn_particles_per_second'],atol=1e-10,rtol=0):
            raise ValueError('Original prepared inlet rate changed')
        initial.append(n);initial_positions.append(p)
        volumes.append(float(np.float32(region['nominal_particle_volume_m3'])))
        if np.float32(r['particle_volume_m3'])!=volumes[-1]:raise ValueError('Dense native volume changed')
    if len(set(volumes))!=1:raise ValueError('Dense fixture requires equal particle volumes')
    live,exits=verify_summary(history,planned,sum(initial))
    if 'first_exit_rejection' in d and decode_rejection(d['first_exit_rejection'],d['simulation_generation'])['captured']:
        raise ValueError('Successful dense commits contradict retained GPU rejection')
    # Report the earliest failed transaction before downstream symptoms such as
    # escaped particles disappearing from a later neighbor list.
    neighbor_checks=[]
    if 'native_neighbor_view_refreshes' in d:
        if d['native_neighbor_view_refreshes']!=sum(g['entries'][0]['first'] for g in stage_groups(d)):
            raise ValueError('Native neighbor views were not refreshed for every birth step')
        neighbor_checks=[audit_record(directory,r) for r in d['native_transfer_packet'] if 'nq_cells' in r]
        if len(neighbor_checks)!=1:raise ValueError('Dense inlet-owner neighbor evidence missing')
    expected_births=np.array([sum(planned[s][o] for s in range(1,step+1)) for o in range(12)])
    keys=[];final_counts={};moved=0;max_displacement=0.;survey_storage_disagreements=0
    for r in records:
        owner=r['region_id'];n=r['particle_count'];nf=r['route_float_components'];ni=r['route_int_components']
        w=read(directory,r,'route_words',(nf+ni,r['particle_capacity']))
        p=read(directory,r,'positions',(n,4)).view('<f4');v=read(directory,r,'velocities',(n,4)).view('<f4')
        ids=read(directory,r,'identities',(n,4))
        owners,survey=storage_owners(p[:,:3],regions,d.get('native_physical_frame_model'))
        survey_storage_disagreements+=int(np.count_nonzero(owners!=survey))
        verify_packet(r,w,read(directory,r,'route_destinations',(n,4)),read(directory,r,'route_counts',(15,)),p,v,ids,owners)
        if np.any(owners!=owner) or n!=history[-1]['counts'][owner]+planned[step][owner]:raise ValueError('Actual dense destination differs from committed count/region')
        if np.any(ids[:,0]>=12) or np.any(ids[:,1]>=expected_births[ids[:,0]]) or np.any(ids[:,2]!=ids[:,1]):
            raise ValueError('Dense native identity outside actual birth namespace')
        keys.append((ids[:,0].astype(np.uint64)<<32)|ids[:,1]);final_counts[owner]=n
        for source in range(12):
            mask=(ids[:,0]==source)&(ids[:,1]<initial[source])
            displacement=np.linalg.norm(p[mask,:3]-initial_positions[source][ids[mask,1]],axis=1)
            moved+=int(np.count_nonzero(displacement>0));max_displacement=max(max_displacement,float(displacement.max(initial=0)))
        pos,start=r['route_position_offset'],r['route_step_start_offset']
        if not np.array_equal(w[pos:pos+3,:n],w[start:start+3,:n]):raise ValueError('Dense pre-advection origin missing')
        if n>d['native_dispatch_reservations'][owner]:raise ValueError('Dense native dispatch budget exceeded')
    keys=np.concatenate(keys);missing=int(expected_births.sum())-len(keys)
    if len(np.unique(keys))!=len(keys) or missing!=int(exits.sum()) or len(keys)!=live+sum(planned[step].values()):
        raise ValueError('Dense native identity population lost/duplicated water')
    if moved==0:raise ValueError('Original dense particles did not move')
    return dict(dense_native_state_verified=True,initial_particles=sum(initial),verified_new_births=int(expected_births.sum())-sum(initial),
                retired_particles=int(exits.sum()),surviving_particles=len(keys),following_step_counts=final_counts,
                initial_particles_moving=moved,max_initial_particle_displacement_cm=max_displacement,
                prepared_inflow_m3s=sum(d['prepared_spawn_rates'])*volumes[0],retained_history_bytes=304*len(history),
                native_neighbor_checks=neighbor_checks,
                pointwise_exit_bed_installed=bool(d.get('native_exact_exit_bed')),
                storage_owner_reference=d.get('native_physical_frame_model','survey-double-legacy'),
                survey_internal_storage_owner_disagreements=survey_storage_disagreements,
                survey_physical_outer_bounds_preserved=True,
                exact_per_exit_history_verified=False,sustained_flow_or_visual_performance_acceptance=False)


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory',type=Path);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists():raise FileExistsError(args.output)
    result=audit(args.directory)
    args.output.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='native_neighbor_checks'},indent=2))
