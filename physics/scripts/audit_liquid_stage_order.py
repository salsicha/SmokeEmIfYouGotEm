"""Audit per-step reconstruction scheduling and actual GPU simulation clocks."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import numpy as np


def compare(capture, report, clock, actual_age, errors=()):
    clock=np.asarray(clock,dtype=float)
    if clock.ndim!=2 or clock.shape[1]!=4 or len(clock)<2 or not np.isfinite(clock).all():
        raise ValueError('Finite GPU clock timeline required')
    frames=capture.get('simulation_steps',0)
    substeps=capture.get('simulation_substeps_per_frame',1)
    if not isinstance(frames,int) or not 720<=frames<=3600 or substeps not in (1,2) or frames*substeps>=4000:
        raise ValueError('Known bounded simulation schedule required')
    expected=(frames-6)*substeps
    ages,delta,reset,tick=clock.T
    max_delta=float(delta.max())
    dispatches=bool(report.get('secondary_first_stage_events')==expected and
        report.get('reconstruction_before_secondary_updates')==expected and
        report.get('updates_with_simulation_tick')==expected)
    clock_ok=bool(len(clock)==report.get('gpu_update_count') and
        abs(ages[0]-.1)<=.00025 and abs(ages[-1]-actual_age)<=.00025 and
        abs(actual_age-frames/60)<=.002 and np.all(np.diff(ages)>=0) and
        np.all(delta>=0) and np.all(reset==0) and np.isin(tick,(0,1)).all() and
        abs(delta.sum()-(ages[-1]-ages[0]))<=1e-6 and
        int((delta>0).sum())==expected and max_delta<=1/(60*substeps)+.001 and
        np.all(delta[-32:]==0) and np.all(ages[-32:]==ages[-1]))
    clean=bool(capture.get('complete') and not capture.get('error') and not report.get('error') and
        not errors and capture.get('secondary_current_surface_compiled') and
        report.get('current_surface_before_secondary') and report.get('diagnostics')==[0,0,0,0])
    batched=bool(substeps==2 and report.get('max_secondary_steps_per_graph',0)>=2)
    return dict(expected_simulation_updates=expected,first_stage_dispatches=report.get('secondary_first_stage_events'),
        reconstructed_updates=report.get('reconstruction_before_secondary_updates'),
        actual_gpu_positive_time_steps=int((delta>0).sum()),maximum_gpu_delta_seconds=max_delta,
        maximum_expected_delta_with_clock_quantization=1/(60*substeps)+.001,
        final_gpu_age_seconds=float(ages[-1]),independent_actual_age_seconds=actual_age,
        exact_dispatch_coverage=dispatches,gpu_per_step_clock_verified=clock_ok,
        multiple_steps_in_one_graph_observed=batched,
        scheduling_verified=bool(clean and dispatches and clock_ok),
        batched_graph_history_exercised=bool(clean and dispatches and clock_ok and batched),
        physical_visual_or_all_scene_acceptance=False)


def audit(directory):
    capture=json.loads((directory/'capture.json').read_text())
    source=directory/'live_density'
    report=json.loads((source/'report.json').read_text())
    raw=(source/'clock.rgba32f').read_bytes()
    clock=np.frombuffer(raw,dtype='<f4').reshape(-1,4)
    log=directory.with_suffix('.log').read_text(errors='replace')
    ages=re.findall(r'LiquidFixture actual_age=([0-9.]+)',log)
    if not ages:raise ValueError('Independent actual simulation age absent')
    errors=[line for line in log.splitlines() if 'Error:' in line or 'Fatal error:' in line]
    result=compare(capture,report,clock,float(ages[-1]),errors)
    result.update(engine_errors=errors,clock_sha256=hashlib.sha256(raw).hexdigest(),
                  rhi_validation_requested='-RHIValidation' in log)
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('directory',type=Path)
    directory=parser.parse_args().directory;output=directory/'stage_order_audit.json'
    if output.exists():raise FileExistsError(output)
    result=audit(directory);output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2));raise SystemExit(0 if result['scheduling_verified'] else 1)
