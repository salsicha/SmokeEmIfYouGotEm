"""Audit a bounded continuation from actual retained records, not full history.

The independent CPU evolves the captured interior only to the GPU committed
instant using the original observed exterior bracket. No later interior reset,
clock snapping, ledger reset, state repair or gameplay/performance acceptance.
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import audit_live_temporal_evolution as temporal
from audit_captured_owner_trial import fields, state_statistics, bit_exact_state
from export_captured_owner_trial import pack_interval


def analyze(source, metadata, binary):
    _, retained=pack_interval(source)
    gpu=fields(metadata,binary,schema='raftsim.captured_owner_interval_diagnostic.v1')
    layout={'output_state':(16384,4,'float32'),'progress':(1,4,'float32'),
            'summary':(1,4,'uint32'),'diagnostics':(1,4,'uint32'),'boundary_volume':(512,4,'float32')}
    if set(gpu)!=set(layout):raise ValueError('Expected all five retained output records')
    for name,(n,c,dtype) in layout.items():
        if gpu[name].shape!=(n,c) or gpu[name].dtype!=np.dtype(dtype):
            raise ValueError('Invalid retained output '+name)
    before=np.asarray(source['summary'],dtype=np.int64)
    after=gpu['summary'][0].astype(np.int64);flags=gpu['diagnostics'][0]
    trials=int(after[0]-before[0]);accepted=int(after[1]-before[1])
    if not 0<=accepted<=trials<=16 or after[0]>4096 or after[3]!=before[3] or after[2] not in (0,1,2,4):
        raise ValueError('Counters reset, unknown status or bounded trial limit violated')
    initial_clock=np.asarray(source['progress'],dtype=np.float32).astype(float)
    clock=gpu['progress'][0].astype(float)
    start=float(initial_clock[0]+initial_clock[1]);end=float(clock[0]+clock[1]);target=retained['bracket'][1]
    if not np.isfinite(clock).all() or not start<=end<=target or clock[2]<0 or clock[3]<0:
        raise ValueError('Invalid retained clock continuation')
    completed=bool(after[2]==1)
    if completed!=(end==target and clock[2]==0) or bool(metadata['transaction_accepted'])!=completed:
        raise ValueError('Interval completion/clock disagreement')
    if completed and flags.tolist()!=[0,0,0,1]:raise ValueError('Completed interval has failure flags')
    state=gpu['output_state'].reshape(128,128,4)
    initial=np.asarray(source['state'],dtype=np.float32).reshape(128,128,4)
    ledger=gpu['boundary_volume'];initial_ledger=np.asarray(source['cumulative_boundary_volume'],dtype=np.float32).reshape(512,4)
    if not np.isfinite(ledger).all():raise ValueError('Nonfinite retained ledger')
    if accepted==0 and (end!=start or not bit_exact_state(state,initial) or not bit_exact_state(ledger,initial_ledger)):
        raise ValueError('Unaccepted continuation changed committed state, time or ledger')
    if accepted>0 and end<=start:raise ValueError('Accepted continuation failed to advance time')
    stats=state_statistics(state)
    delta=state.astype(float)-initial.astype(float)
    signs=np.r_[-np.ones(128),np.ones(128),-np.ones(128),np.ones(128)]
    ledger_delta=ledger.astype(float)-initial_ledger.astype(float)
    inventory=np.sum(delta,axis=(0,1))*.25
    outward=np.sum(signs[:,None]*ledger_delta,axis=0)*.5
    report=dict(schema='raftsim.captured_owner_interval_analysis.v1',scope=__doc__,
        interval_completed=completed,scene_accepted=False,normal_solver_promoted=False,
        full_history_qualified=False,cpu_completed=False,state_gates_passed=False,
        initial_summary=before.tolist(),summary=after.tolist(),additional_trials=trials,additional_accepted=accepted,
        diagnostics=flags.tolist(),initial_native_seconds=start,committed_native_seconds=end,
        requested_end_native_seconds=target,progress=clock.tolist(),state_statistics=stats,
        water_inventory_change_m3=float(inventory[0]),outward_water_delta_m3=float(outward[0]),
        float_water_balance_m3=float(inventory[0]+outward[0]),
        foam_inventory_change=float(inventory[3]),outward_foam_delta=float(outward[3]),
        float_foam_balance=float(inventory[3]+outward[3]))
    # Existing float-storage ledger diagnostic: report residual, never repair it
    # or silently invent a relaxed conservation gate. State accuracy still uses
    # the existing 1e-4 absolute and 2e-5 component-relative requirements.
    if stats['invalid_cells'] or np.any(state[...,3]!=0) or np.any(ledger[:,3]!=0):
        report['cpu_error']='Invalid or nonzero-foam output cannot use zero-foam CPU control'
        return report
    i=retained['interval']
    a,b=temporal.observations(dict(schema='raftsim.live_temporal_boundary_inputs.v1',
        first=source['observations'][i],second=source['observations'][i+1]))
    _,boundary=temporal.boundary_provider(a,b)
    def sample(elapsed,stage):return boundary(start-a['native_seconds']+elapsed,stage)
    try:
        # Independent double control chooses its own admissible RK2 steps; the
        # GPU replay itself retained the original proposed step and all counters.
        expected,cpu=temporal.bank.advance(initial[...,:3].astype(float),a['bed'],.5,end-start,
            max_trials=max(1,4096-int(before[0])),boundary_at_time=sample,
            breaking_model='hybrid_front',**temporal.KW)
    except (ValueError,FloatingPointError,temporal.bank.ReplayExhausted,temporal.bank.ReplayInvalidRate) as error:
        report.update(cpu_error=str(error),cpu_failure=getattr(error,'diagnostics',None))
        return report
    error=state[...,:3].astype(float)-expected
    relative=[float(np.linalg.norm(error[...,k])/np.linalg.norm(expected[...,k]))
              if np.any(expected[...,k]) else float(np.linalg.norm(error[...,k])) for k in range(3)]
    maximum=float(abs(error).max())
    report.update(cpu_completed=True,cpu_statistics=cpu,maximum_state_error=maximum,
        relative_state_errors=relative,state_gates_passed=bool(maximum<1e-4 and max(relative)<2e-5))
    return report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('capture',type=Path);parser.add_argument('--report',type=Path,required=True)
    args=parser.parse_args()
    if args.report.exists():raise FileExistsError(args.report)
    metadata_bytes=args.capture.read_bytes();metadata=json.loads(metadata_bytes)
    input_path=Path(metadata['input']);manifest_bytes=input_path.with_suffix('.json').read_bytes();manifest=json.loads(manifest_bytes)
    original=Path(manifest['source']).read_bytes();input_bytes=input_path.read_bytes();source=json.loads(original)
    sha=lambda data:hashlib.sha256(data).hexdigest()
    if (manifest['schema']!='raftsim.captured_owner_interval.v1' or sha(original)!=manifest['source_sha256']
        or sha(input_bytes)!=manifest['input_sha256'] or bytes(pack_interval(source)[0])!=input_bytes):
        raise ValueError('Actual retained input/source provenance mismatch')
    binary=Path(metadata['binary']).read_bytes();report=analyze(source,metadata,binary)
    report.update(source_sha256=sha(original),input_sha256=sha(input_bytes),
        capture_metadata_sha256=sha(metadata_bytes),capture_binary_sha256=sha(binary),manifest_sha256=sha(manifest_bytes),
        implementation_hashes={name:sha(Path(__file__).with_name(name).read_bytes()) for name in
            ('audit_captured_owner_interval.py','export_captured_owner_trial.py','audit_captured_owner_trial.py',
             'audit_live_temporal_evolution.py','total_depth_bank_replay.py','adaptive_hydrostatic_precision.py',
             'total_depth_nonlinear_pressure.py','pressure_cg_range_reference.py','breaking_front_reference.py')})
    with args.report.open('x') as stream:json.dump(report,stream,indent=2,allow_nan=False)
    print(json.dumps(report,indent=2,allow_nan=False))


if __name__=='__main__':main()
