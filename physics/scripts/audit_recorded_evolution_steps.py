"""Diagnose individual GPU trials using independent CPU stage arithmetic.

By default each control starts from that trial's represented GPU input. Retained
controls can instead start from a source-matched independently evolved CPU
checkpoint and carry their own state between contiguous accepted trials. Both
modes use recorded attempted dt, including float encoding. This is diagnostic
fault isolation, not the default-dt full-history accuracy gate or permission to
reset gameplay state.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import audit_live_temporal_evolution as temporal
from audit_recorded_stages import read_records


def shoreline_model(metadata, source):
    limiter=source.get('shoreline_limiter','binary')
    if limiter not in ('binary','continuous','unscaled') or metadata.get('shoreline_limiter','binary')!=limiter:
        raise ValueError('Recorded/source shoreline model mismatch')
    summary=source.get('summary')
    if limiter!='binary' and summary is None:
        raise ValueError('Candidate source requires persisted model identity')
    if summary is not None and (len(summary)!=4 or summary[3]!={'binary':1,'continuous':3,'unscaled':5}[limiter]):
        raise ValueError('Source shoreline model differs from persisted mode')
    return limiter


def compare(metadata, binary, source, interval, *, retain_control=False, on_states=None, initial_control=None):
    limiter=shoreline_model(metadata,source)
    raw = source['observations']
    if type(interval) is not int or not 0 <= interval < len(raw)-1:
        raise ValueError('Interval outside observed source pairs')
    a, b = temporal.observations(dict(schema='raftsim.live_temporal_boundary_inputs.v1',
                                     first=raw[interval], second=raw[interval+1]))
    _, boundary = temporal.boundary_provider(a, b)
    if initial_control is not None and not retain_control:
        raise ValueError('Independent checkpoint requires retained control')
    rows = []; control = None if initial_control is None else initial_control.copy(); previous_end = None
    for trial, stages, gpu_final, *_ in read_records(metadata, binary):
        if trial['interval'] != interval: continue
        if initial_control is not None and not rows and (trial['trial']!=0 or trial['begin']!=a['native_seconds']):
            raise ValueError('Independent checkpoint must start at its exact first recorded trial')
        dt = trial['attempted_dt']; elapsed = trial['begin']-a['native_seconds']
        if not np.isfinite(dt) or dt <= 0: raise ValueError('Invalid recorded dt')
        if retain_control and (trial['accepted_dt'] != dt or trial['accepted'] != 1 or
                               (previous_end is not None and trial['begin'] != previous_end)):
            raise ValueError('Retained control requires contiguous accepted trials')
        captured = []
        original = temporal.bank.nonlinear_pressure_force
        def capture(*args, **kwargs):
            force, stats = original(*args, **kwargs)
            captured.append(dict(pairs=[v.copy() for v in args[4]],
                fraction=kwargs['dispersion_fraction'].copy(), force=force.copy(),
                hydro=np.concatenate((kwargs['mass_rate'][..., None], kwargs['momentum_rate']), axis=-1),
                pressure_stats=stats))
            return force, stats
        def rate(state, time):
            es, eb, trace = boundary(time, None)
            return temporal.bank.rate(state, a['bed'], a['cell_meters'], exterior=(es, eb),
                pressure_boundary=trace, breaking_model='hybrid_front', shoreline_limiter=limiter, **temporal.KW)[0]
        initial = stages[0]['state'][..., :3].astype(float) if control is None else control
        try:
            temporal.bank.nonlinear_pressure_force = capture
            first = rate(initial, elapsed)
            stage = initial+dt*first
            second = rate(stage, elapsed+dt)
        finally:
            temporal.bank.nonlinear_pressure_force = original
        final = .5*(initial+stage+dt*second)
        if retain_control: control = final; previous_end = trial['end']
        if on_states is not None: on_states(trial, initial, stage, final)
        error = abs(final-gpu_final[..., :3]); worst = np.unravel_index(error.argmax(), error.shape)
        stage_error = abs(stage-stages[1]['state'][..., :3])
        fraction_error = abs(captured[1]['fraction']-stages[1]['fraction'])
        fraction_worst = np.unravel_index(fraction_error.argmax(), fraction_error.shape)
        packed = captured[1]['pairs'][0].astype(np.uint32)+2*captured[1]['pairs'][1].astype(np.uint32)
        row = dict(trial=trial, input_state_max_error=float(abs(initial-stages[0]['state'][..., :3]).max()),
            first_fraction_max_error=float(abs(captured[0]['fraction']-stages[0]['fraction']).max()),
            euler_state_max_error=float(stage_error.max()),
            final_state_max_error=float(error.max()), worst_yxc=list(map(int, worst)),
            cpu=float(final[worst]), gpu=float(gpu_final[worst]),
            second_fraction_max_error=float(fraction_error.max()),
            second_fraction_worst_yx=list(map(int, fraction_worst)),
            second_graph_mismatches=int(np.sum(packed!=stages[1]['pairs'])))
        for name, cpu_stage, gpu_stage in zip(('first', 'second'), captured, stages):
            for field in ('hydro', 'force'):
                actual = gpu_stage['rate'][..., :3] if field == 'hydro' else gpu_stage['force']
                difference = abs(cpu_stage[field]-actual)
                at = np.unravel_index(difference.argmax(), difference.shape)
                row[name+'_'+field] = dict(maximum_error=float(difference.max()),
                    worst_yxc=list(map(int, at)), cpu=float(cpu_stage[field][at]), gpu=float(actual[at]))
            row[name+'_pressure_stats'] = cpu_stage['pressure_stats']
        rows.append(row); print(json.dumps(row), flush=True)
    if not rows: raise ValueError('Interval not captured')
    return rows


def checkpoint(path, source_bytes, interval):
    """Select a same-source, exact-time/origin independently evolved CPU state."""
    source=json.loads(source_bytes);raw=source['observations']
    if type(interval) is not int or not 0<=interval<len(raw)-1:raise ValueError('Invalid checkpoint interval')
    first=raw[interval];data=path.read_bytes()
    with np.load(path,allow_pickle=False) as archive:
        if archive['source_sha256'].item()!=hashlib.sha256(source_bytes).hexdigest():
            raise ValueError('Independent checkpoint belongs to another source')
        rows=json.loads(archive['checkpoints_json'].item())
        matches=[i for i,r in enumerate(rows) if r['native_seconds']==first['native_seconds']
                 and r['origin_meters']==[first['origin_x'],first['origin_y']]]
        if len(matches)!=1:raise ValueError('Exactly one independent time/origin checkpoint required')
        state=archive['checkpoint_'+str(matches[0])].copy()
    if (state.shape!=(first['ny'],first['nx'],3) or state.dtype!=np.float64 or not np.isfinite(state).all()
        or np.any(state[...,0]<0) or np.any(state[...,1:][state[...,0]==0]!=0)):
        raise ValueError('Invalid independent checkpoint state')
    return state,dict(path=str(path.resolve()),sha256=hashlib.sha256(data).hexdigest(),
        checkpoint=matches[0],native_seconds=first['native_seconds'],origin_meters=[first['origin_x'],first['origin_y']])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('trace', type=Path); parser.add_argument('--interval', type=int, required=True)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--retain-control', action='store_true',
                        help='Carry the CPU control between contiguous recorded steps; still diagnostic dt')
    parser.add_argument('--states', type=Path, help='Optional fresh NPZ of CPU inputs/stages/results')
    parser.add_argument('--initial-checkpoints',type=Path,
        help='Begin retained diagnostic from the independently evolved full-history endpoint, not the GPU input')
    args = parser.parse_args()
    if args.report.exists(): raise FileExistsError(args.report)
    if args.states is not None and args.states.exists(): raise FileExistsError(args.states)
    data = args.trace.read_bytes(); metadata = json.loads(data)
    if not metadata.get('completed') or not metadata.get('final_state_exact_to_live'):
        raise ValueError('Unqualified recorded trace')
    binary = Path(metadata['binary']).read_bytes(); source = Path(metadata['source']).read_bytes()
    states = {};initial=None;initial_provenance=None
    if args.initial_checkpoints:
        if not args.retain_control:raise ValueError('Independent checkpoint requires --retain-control')
        initial,initial_provenance=checkpoint(args.initial_checkpoints,source,args.interval)
    def save(trial, initial, stage, final):
        if args.states is not None:
            for name, value in [('input', initial), ('stage', stage), ('final', final)]:
                states[str(trial['trial'])+'_'+name] = value.copy()
    rows = compare(metadata, binary, json.loads(source), args.interval,
                   retain_control=args.retain_control, on_states=save,initial_control=initial)
    report = dict(schema='raftsim.recorded_evolution_steps.v1', scope=__doc__, trials=rows,
        source_sha256=hashlib.sha256(source).hexdigest(), trace_sha256=hashlib.sha256(data).hexdigest(),
        binary_sha256=hashlib.sha256(binary).hexdigest(),
        implementation_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        retain_control=args.retain_control,initial_independent_checkpoint=initial_provenance,
        shoreline_limiter=shoreline_model(metadata,json.loads(source)))
    report['implementation_hashes']={name:hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
        for name in ('audit_recorded_evolution_steps.py','audit_recorded_stages.py','audit_live_temporal_evolution.py',
            'total_depth_bank_replay.py','adaptive_hydrostatic_precision.py','continuous_shoreline_reconstruction.py','total_depth_nonlinear_pressure.py',
            'pressure_cg_range_reference.py','breaking_front_reference.py')}
    if args.states is not None:
        with args.states.open('xb') as stream:
            np.savez(stream, **states, source_sha256=np.array(report['source_sha256']))
        report['states'] = dict(path=str(args.states.resolve()),
            sha256=hashlib.sha256(args.states.read_bytes()).hexdigest())
    with args.report.open('x') as stream: json.dump(report, stream, indent=2, allow_nan=False)


if __name__ == '__main__': main()
