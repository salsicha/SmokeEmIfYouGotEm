"""Run the ORIGINAL short evolution/energy probes with smooth pressure geometry.

Reuses the existing audit functions unchanged, with explicit geometry/stage
bindings in this process only. Same synthetic source h,u, poles, CG, spatial
sizes, horizons and time resolutions. This is a different research model,
not the original captured-source river solver or gameplay qualification.
"""
import argparse
import hashlib
import json
from pathlib import Path
import audit_positive_rational_stage as instantaneous
import audit_positive_rational_evolution as evolution
from smooth_rational_velocity_stage import make,stage,rk2_step


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report',type=Path,required=True);args=parser.parse_args()
    if args.report.exists():raise FileExistsError(args.report)
    instantaneous.make=make;instantaneous.stage=stage
    evolution.make=make;evolution.rk2_step=rk2_step
    stages=[];trajectories=[]
    for n in (64,128):
        for seed in range(2200,2208):
            r=instantaneous.run(seed,n);stages.append(r)
            print(json.dumps(dict(event='smooth_stage',**r)),flush=True)
    for seed in range(2200,2208):
        r=evolution.run(seed);trajectories.append(r)
        print(json.dumps(dict(event='smooth_evolution_complete',seed=seed,ratios=r['temporal_ratios'])),flush=True)
    report=dict(scope=__doc__,stages=stages,trajectories=trajectories,
        dry_pressure_or_full_history_or_gameplay_accepted=False,
        implementation_hashes={name:hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
            for name in ('audit_smooth_rational_evolution.py','smooth_rational_velocity_stage.py',
                'smooth_pressure_geometry.py','smooth_pressure_reverse.py','reverse_rational_depth_gradient.py',
                'continuous_extremum_transport.py','audit_positive_rational_stage.py','audit_positive_rational_evolution.py')})
    with args.report.open('x') as stream:json.dump(report,stream,indent=2,allow_nan=False)


if __name__=='__main__':main()
