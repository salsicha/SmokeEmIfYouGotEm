"""Compare a dry-interior optimization against the saved baseline executable."""
from pathlib import Path
import json
import subprocess
import time
import numpy as np
ROOT=Path(__file__).resolve().parents[2]


def main():
    work=ROOT/'tmp/south-fork-survey-hydraulics/1m-mixed-inlet-conservative-edge'
    source=json.loads((work/'run_result.json').read_text())
    frames={};timings={}
    for name,binary in [('baseline','troublemaker-solver-release'),('dry_cull','troublemaker-solver-dry-cull-release')]:
        command=list(source['command']);command[0]=str(ROOT/f'tmp/{binary}/raftsim_water_solver.exe')
        output=ROOT/f'tmp/south-fork-dry-cull-benchmark/{name}'
        for key,value in [('--output',str(output)),('--steps','100'),('--frame-interval','100')]:
            command[command.index(key)+1]=value
        start=time.perf_counter();subprocess.run(command,check=True,capture_output=True,text=True)
        timings[name]=time.perf_counter()-start
        frames[name]=np.genfromtxt(output/'troublemaker_survey_candidate_1m/frames/frame_0001.csv',delimiter=',',names=True)
    equal=all(np.array_equal(frames['baseline'][k],frames['dry_cull'][k]) for k in frames['baseline'].dtype.names)
    report={'status':'offline_dry_culling_comparison','simulated_seconds':10.,'wall_seconds':timings,
        'speedup':timings['baseline']/timings['dry_cull'],'all_exported_fields_bitwise_equal':equal,
        'production_frame_rate_validated':False}
    (ROOT/'docs/reconstruction-review-2026-09-06/dry_culling_benchmark.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2))
    if not equal:raise SystemExit('Optimization changed exported physics fields')


if __name__=='__main__':main()
