"""Audit GPU-carried simulation age independently of callback/tick counts."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import numpy as np


def compare(clock,actual_age,surface_age):
    clock=np.asarray(clock,dtype=float)
    if clock.ndim!=2 or clock.shape[1]!=4 or len(clock)<700:
        raise ValueError('Full bounded live GPU clock timeline required')
    age,delta,reset,tick=clock.T
    error=abs(age[-1]-actual_age)
    sum_error=abs(delta.sum()-(age[-1]-age[0]))
    paused=bool((delta[-32:]==0).all() and (age[-32:]==age[-1]).all())
    surface_error=float(np.max(abs(np.asarray(surface_age)-age[-1])))
    result=dict(records=len(age),first_age_seconds=float(age[0]),last_age_seconds=float(age[-1]),
        independent_actual_age_seconds=actual_age,final_age_error_seconds=float(error),
        integrated_delta_seconds=float(delta.sum()),telescoping_error_seconds=float(sum_error),
        positive_delta_records=int((delta>0).sum()),render_only_records=int((tick==0).sum()),
        maximum_delta_seconds=float(delta.max()),last_32_callbacks_paused=paused,
        surface_age_max_error_seconds=surface_error,reset_records=int(reset.sum()))
    result['gpu_clock_verified']=bool(np.isfinite(clock).all() and np.isfinite(surface_age).all()
        and np.isfinite(actual_age) and (np.diff(age)>=0).all() and (delta>=0).all()
        and (reset==0).all() and np.isin(tick,(0,1)).all() and 650<=(delta>0).sum()<=720
        and 0<=age[0]<.2 and age[-1]<2048 and error<=.00025 and sum_error<=1e-6
        and surface_error<=1e-6 and paused)
    return result


def audit(path):
    log=path.with_suffix('.log').read_text(errors='replace')
    ages=re.findall(r'LiquidFixture actual_age=([0-9.]+)',log)
    if not ages:raise ValueError('Independent simulation telemetry missing')
    source=path/'live_density'
    clock=np.fromfile(source/'clock.rgba32f',dtype='<f4').reshape(-1,4)
    surface=np.fromfile(source/'surface.rgba16f',dtype='<f2').reshape(-1,4).astype(float)
    result=compare(clock,float(ages[-1]),surface[:,2]+surface[:,3])
    capture=json.loads((path/'capture.json').read_text())
    report=json.loads((source/'report.json').read_text())
    errors=[line for line in log.splitlines() if re.search(r'\b(?:Error|Fatal):',line)]
    result.update(engine_errors=errors,source_sha256=hashlib.sha256((source/'clock.rgba32f').read_bytes()).hexdigest(),
        foam_evolution_implemented=bool(report.get('current_surface_foam',False)),physical_or_visual_acceptance=False)
    result['gpu_clock_verified'] &= bool(capture['complete'] and not capture['error'] and not errors
        and not report['error'] and report['diagnostics']==[0]*4 and len(clock)==report['gpu_update_count'])
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('path',type=Path)
    path=p.parse_args().path;result=audit(path);output=path/'clock_audit.json'
    if output.exists():raise FileExistsError(output)
    output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
    raise SystemExit(0 if result['gpu_clock_verified'] else 1)
