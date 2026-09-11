"""Reproduce registered replay inputs in an isolated native timing run.

Outputs are diagnostic artifacts, not a production cook or release qualification.
The original scenario and engine fields are never modified.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import time

import numpy as np


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--exe', type=Path, required=True)
    p.add_argument('--scenario', type=Path, required=True)
    p.add_argument('--engine-review', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--steps', type=int, default=600)
    p.add_argument('--dt', type=float, default=1/60)
    a = p.parse_args()
    assert a.steps > 0 and np.isfinite(a.dt) and a.dt > 0
    a.output.mkdir(parents=True, exist_ok=False)
    package = a.output/'scenario'
    shutil.copytree(a.scenario, package)
    data = json.loads((package/'scenario.json').read_text())
    manifest = json.loads((a.engine_review/'manifest.json').read_text())
    config = manifest['solver']
    assert config['runtime_replay_offline_config'] and config['spatial_order'] == 2
    band = next(b for b in manifest['bands'] if b['band_id'] == 'median_runnable')
    assert data['boundaries'] == band['runtime_boundaries'], 'Offline and live boundary data differ'
    assert not config.get('preserve_initial_mass', False)
    assert data['grid']['nx'] == 271 and data['grid']['ny'] == 161
    fields = a.engine_review/'median_runnable'
    for name in ('h','u','v','bed'):
        assert digest(fields/(name+'.npy')) == band['arrays'][name]['sha256'], name
    arrays = {name: np.load(fields/(name+'.npy')).astype(np.float64) for name in ('h','u','v','bed')}
    assert all(x.shape == (161,271) and np.isfinite(x).all() for x in arrays.values())
    h,u,v,bed = (arrays[n] for n in ('h','u','v','bed'))
    assert h.min() >= 0
    np.save(package/'bed.npy', bed)
    np.savez_compressed(package/'initial_state.npz', depth=h,u=u,v=v,eta=h+bed,
                        hu=h*u,hv=h*v,wet=h>config['dry_tolerance'])
    data['fixed_dt']=a.dt
    data['duration']=a.dt*a.steps
    data['roughness']=config['roughness_manning']
    (package/'scenario.json').write_text(json.dumps(data,indent=2))
    command=[str(a.exe.resolve()),'--scenario',str(package.resolve()),'--output',str((a.output/'solver').resolve()),
             '--steps',str(a.steps),'--frame-interval',str(a.steps),'--solver-mode','finite_volume',
             '--boundary-mode','scenario','--spatial-order','2','--flux-scheme',config['flux_scheme'],
             '--cfl',str(config['cfl']),'--dry-tolerance',str(config['dry_tolerance']),
             '--feature-strength-scale',str(config['feature_strength_scale']),
             '--roughness-scale',str(config['roughness_scale']),
             '--bed-slope-source-scale',str(config['bed_slope_source_scale']),
             '--no-preserve-initial-mass','--disable-fixture-calibrations',
             '--experimental-west-discharge',str(config['experimental_west_discharge_m3s'])]
    if config['experimental_west_supercritical_stage']:
        command.append('--experimental-west-supercritical-stage')
    started=time.perf_counter()
    run=subprocess.run(command,capture_output=True,text=True)
    elapsed=time.perf_counter()-started
    profiles=[json.loads(line.split(' ',1)[1]) for line in run.stderr.splitlines()
              if line.startswith('RAFTSIM_SOLVER_PROFILE ')]
    report=dict(command=command,returncode=run.returncode,wall_seconds=elapsed,stdout=run.stdout,
                stderr=run.stderr,profiles=profiles,executable_sha256=digest(a.exe),
                input_hashes={n:digest(fields/(n+'.npy')) for n in arrays},
                manifest_sha256=digest(a.engine_review/'manifest.json'),dt=a.dt,steps=a.steps,
                limitation='Isolated native fixed-timestep replay from float32 exported engine fields, not concurrent engine rendering or release qualification.')
    (a.output/'report.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))
    return run.returncode


if __name__ == '__main__':
    raise SystemExit(main())
