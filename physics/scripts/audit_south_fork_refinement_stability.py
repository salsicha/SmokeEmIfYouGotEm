"""Record rejected fine-grid output and bounded follow-up tests without promotion."""
from pathlib import Path
import hashlib
import json
import numpy as np
from south_fork_survey_sanity import check_frame,require_sane_frames

ROOT=Path(__file__).resolve().parents[2]
WORK=ROOT/'tmp/south-fork-survey-hydraulics'
OUT=ROOT/'docs/reconstruction-review-2026-09-06'


def inspect(folder):
    manifest=json.loads((folder/'manifest.json').read_text())
    snapshots=[]
    for name in manifest['frames']:
        path=folder/name
        data=np.genfromtxt(path,delimiter=',',names=True)
        snapshots.append({'frame':name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
            **check_frame(data)})
    return {'output_dir':folder.relative_to(ROOT).as_posix(),
        'native_validation':json.loads((folder/'validation.json').read_text()),
        'snapshots':snapshots,'all_saved_frames_sane':all(f['passed'] for f in snapshots)}


def main():
    baseline=WORK/'refinement-bounded-diagnostic/troublemaker_survey_candidate_0.5m'
    report={'status':'refinement_rejected_followup_short_tests_only',
        'unbounded_original_run':{'status':'interrupted_after_more_than_78_cpu_minutes',
            'owned_solver_pid':15172,'result_accepted':False,
            'reason':'replaced by bounded progress-reporting diagnostic; no final output from original'},
        'cfl_038_dt_01_100seconds':inspect(baseline),
        'last_saved_sane_baseline_time_seconds':90.,'first_saved_failed_time_seconds':100.,
        'followup_tests':[],
        'long_term_stability_verified':False,'resolution_converged':False,'production_promoted':False}
    for label in ('small-step-diagnostic','strict-cfl-diagnostic'):
        work=WORK/('0.5m-mixed-inlet-'+label)
        result=json.loads((work/'run_result.json').read_text())
        registration=json.loads((work/'registration.json').read_text())
        report['followup_tests'].append({'label':label,'registration':registration,
            'runtime_seconds':result['runtime_seconds'],**inspect(ROOT/result['output_dir'])})
    # Exercise the same gate used by the engine exporter against the actual
    # failed artifact, not just a synthetic unit-test fixture.
    rejected=False
    try:require_sane_frames(baseline,json.loads((baseline/'manifest.json').read_text()))
    except ValueError:rejected=True
    report['failed_history_export_gate_rejected']=rejected
    (OUT/'half_metre_stability.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    if not rejected:raise RuntimeError('Failed hydraulic history passed the engine export gate')
    print(json.dumps({'baseline_rejected':not report['cfl_038_dt_01_100seconds']['all_saved_frames_sane'],
        'short_tests_sane':[r['all_saved_frames_sane'] for r in report['followup_tests']],
        'export_gate_rejected':rejected,'resolution_accepted':False},indent=2))


if __name__=='__main__':main()
