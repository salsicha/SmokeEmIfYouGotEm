"""Audit uninterrupted editor-fixture throughput, never claim packaged-game FPS."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import numpy as np


def distribution(values):
    a=np.asarray(values,dtype=float)
    if a.ndim!=1 or not len(a) or not np.isfinite(a).all() or (a<0).any():
        raise ValueError('Finite nonnegative timing samples required')
    return dict(count=len(a),mean_ms=float(a.mean()),p50_ms=float(np.median(a)),
                p95_ms=float(np.percentile(a,95)),p99_ms=float(np.percentile(a,99)),max_ms=float(a.max()))


def summarize(capture,log_text):
    b=capture['benchmark']
    intervals=np.asarray(b['intervals_ms'],dtype=float)
    count=b['end_frame']-b['start_frame']
    errors=[line for line in log_text.splitlines() if re.search(r'\b(?:Error|Fatal):',line)]
    valid=(capture['complete'] and not capture['error'] and count>=480
           and len(intervals)==count and np.isfinite(intervals).all() and (intervals>0).all()
           and abs(intervals.sum()/1000-b['wall_seconds'])<1e-6
           and not b['blocking_readbacks_during_window'] and not b['image_exports_during_window']
           and not any(b['start_frame']<=c['frame']<b['end_frame'] for c in capture['captures'])
           and not errors)
    result=dict(uninterrupted_window_verified=bool(valid),engine_errors=errors,
                editor_fixture_frame_intervals=distribution(intervals),
                simulation_to_wall_ratio=b['simulation_seconds']/b['wall_seconds'],
                packaged_game_fps_measured=False,full_scene_performance_accepted=False)
    if capture['live_density_requested']:
        live=capture['live_density_result']
        result['copy_timing_includes_surface_foam']=bool(live.get('copy_timing_includes_surface_foam',False))
        result['copy_timing_includes_secondary_surface_cache']=bool(live.get('secondary_shared_render_surface',False))
        result['niagara_particle_update_cost_in_reconstruction_gpu_timing']=False
        # Timestamp warm-up exclusion is explicit and independent of the
        # Python frame window; these are reconstruction-only GPU intervals.
        samples=live['gpu_timing_samples']
        selected=[s for s in samples if s['update']>=240]
        updates=[s['update'] for s in samples]
        gpu_ok=(live['gpu_timing_available'] and not live['gpu_timing_waits_for_results']
                and live['diagnostics']==[0]*4 and not live['error'] and len(selected)>=400
                and len(set(updates))==len(updates) and all(s['ordered'] for s in samples)
                and live['gpu_timing_skipped_busy_slots']==0)
        result['gpu_timing_verified']=bool(gpu_ok)
        result['gpu_warmup_updates_excluded']=240
        result['gpu_timing_window_matches_python_window_exactly']=False
        if gpu_ok:
            for key in ('pack_density_ms','distance_ms','copy_ms','total_ms'):
                result[key]=distribution([s[key] for s in selected])
            if any(abs(s['total_ms']-sum(s[k] for k in ('pack_density_ms','distance_ms','copy_ms')))>1e-6 for s in samples):
                result['gpu_timing_verified']=False
    return result


def run(path):
    capture_path=path/'capture.json'
    log=path.with_suffix('.log')
    result=summarize(json.loads(capture_path.read_text()),log.read_text(errors='replace'))
    result.update(source=str(capture_path.resolve()),source_sha256=hashlib.sha256(capture_path.read_bytes()).hexdigest(),
                  log_sha256=hashlib.sha256(log.read_bytes()).hexdigest())
    destination=path/'benchmark_audit.json'
    if destination.exists():
        raise FileExistsError(destination)
    destination.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('path',type=Path)
    run(p.parse_args().path)
