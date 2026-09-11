"""Retain all successful and rejected bank-spike experiments without promotion."""
from pathlib import Path
import hashlib
import json
import math

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'tmp/south-fork-bank-spike-20260907'
OUTPUT=ROOT/'docs/reconstruction-review-2026-09-07/bank-spike-experiments.json'


def main():
    experiments=[]
    for path in sorted(BASE.glob('*/replay.json')):
        raw=json.loads(path.read_text())
        frames=raw.get('frames',[])
        if not frames:
            raise ValueError(f'Unfinished experiment: {path}')
        worst=max(frames,key=lambda f:f['sanity']['maximum_speed_mps'])
        flux=path.parent/'face-flux-audit/report.json'
        experiments.append({'name':path.parent.name,
            'evidence':path.relative_to(ROOT).as_posix(),
            'evidence_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
            'source_frame_sha256':raw['source_frame_sha256'],
            'binary_sha256':raw['binary_sha256'],
            'source_time_seconds':raw['source_time_seconds'],
            'end_time_seconds':frames[-1]['time_seconds'],
            'saved_frames':len(frames),
            'all_saved_frames_sane':raw['all_saved_frames_sane'],
            'maximum_saved_speed_mps':worst['sanity']['maximum_speed_mps'],
            'maximum_saved_depth_m':max(f['sanity']['maximum_depth_m'] for f in frames),
            'worst_speed_time_seconds':worst['time_seconds'],'worst_speed_cell':worst['peak'],
            'target_cell_maximum_speed_mps':max(math.hypot(f['target']['u'],f['target']['v']) for f in frames),
            'failed_saved_times_seconds':[f['time_seconds'] for f in frames if not f['sanity']['passed']],
            'face_flux_audit':json.loads(flux.read_text()) if flux.exists() else None})
    result={'scope':__doc__.strip(),'experiments':experiments,
        'engine_validation_in_this_report':False,'production_promoted':False,'resolution_converged':False,
        'long_duration_stability_accepted':False,
        'note':'Restart intervals, not one continuous history. One-second samples cannot bound unsaved peaks. Wall times are not comparable performance measurements.'}
    with OUTPUT.open('x',encoding='utf-8') as output:
        json.dump(result,output,indent=2,allow_nan=False)
    print(json.dumps([{k:e[k] for k in ('name','maximum_saved_speed_mps','all_saved_frames_sane')} for e in experiments],indent=2))


if __name__=='__main__':main()
