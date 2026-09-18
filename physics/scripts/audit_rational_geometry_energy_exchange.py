"""Original eight physical profiles: complete local energy-work identity only."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import time
import numpy as np
from audit_reconstructed_closed_energy import fixture
from smooth_rational_velocity_stage import make
from conservative_rational_stress import stress_stage_physical
from rational_geometry_energy_exchange import complete_local_work


def run(seed,n):
    source, bed = fixture(seed,'smooth',n)
    before = [a.copy() for a in (source,bed)]
    h, p, dx = source[...,0], source[...,1:], 16/n
    g = make(h,bed,dx)
    stage = stress_stage_physical(g,p,flux_scheme='donor-stress')
    start = time.perf_counter()
    work = complete_local_work(g,p,stage['depth_rate'],stage['physical_momentum_rate'])
    wall = time.perf_counter()-start
    if not all(np.array_equal(a,b) for a,b in zip((source,bed),before)):
        raise RuntimeError('Original source changed')
    keys = ('maximum_factor_value_error','maximum_forward_work_error',
            'maximum_reverse_gradient_error','maximum_graph_balance_error',
            'complete_local_balance_error','maximum_local_depth_nodes',
            'integrated_geometry_exchange','integrated_auxiliary_exchange',
            'integrated_energy_rate','coordinate_work_error')
    return dict(seed=seed,resolution=n,
        source_state_sha256=hashlib.sha256(source.tobytes()).hexdigest(),
        bed_sha256=hashlib.sha256(bed.tobytes()).hexdigest(),
        **{key:work[key] for key in keys}, shared_research_wall_seconds=wall,
        maximum_local_geometry_exchange=float(abs(work['geometry_exchange']).max()),
        original_stress_rate_error=abs(work['integrated_energy_rate']-stage['energy_rate']),
        complete_local_balance_gate_passed=work['complete_local_balance_error']<1e-10,
        energy_conservation_gate_passed=abs(work['integrated_energy_rate'])<1e-10,
        hydrodynamic_flux_or_dry_or_history_or_gameplay_accepted=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report',type=Path,required=True)
    args = parser.parse_args()
    if args.report.exists():raise FileExistsError(args.report)
    scripts = Path(__file__).resolve().parent
    files = sorted({Path(m.__file__).resolve() for m in tuple(sys.modules.values())
                    if getattr(m,'__file__',None) and Path(m.__file__).resolve().parent==scripts})
    hashes = lambda:{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    initial = hashes()
    records = []
    for n in (64,128):
        for seed in (2200,2202,2204,2206):
            r = run(seed,n)
            records.append(r)
            print(json.dumps(r),flush=True)
    if hashes()!=initial:raise RuntimeError('Implementation changed during audit')
    with args.report.open('x') as stream:
        json.dump(dict(scope=__doc__,records=records,implementation_hashes=initial),
                  stream,indent=2,allow_nan=False)


if __name__=='__main__':main()
