"""Native short-time wetting controls on two observed Azul sampling gaps.

Same encoded terrain at 2/1/0.5 m water sampling. Closed exterior boundaries,
zero initial velocity, no source discharge and no feature force: this tests
initial wetting only, not the full river's through-flow or navigability.
"""
import argparse
import copy
import gzip
import json
import os
from pathlib import Path
import shutil
import subprocess
import time

import numpy as np
from scipy.ndimage import label

from build_futaleufu_continuous_water_domain import (
    ROOT, PREFIX, LandscapeTriangles, FutaleufuBed, initial_fields, labels_at, sha)
from solver_face_discharge import SOLVER_FLAGS

CASES = dict(azul_3760=[[744777.,5199942.5],[744813.,5199956.5]],
             azul_5180=[[745459.,5199750.5],[745463.,5199756.5]])
TEMPLATE = ROOT/'unreal/Plugins/SEIYGECore/data/validation/milestone17/analytic_fixtures/fixtures/lake_at_rest_balance/scenario/scenario.json'


def save(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False)+'\n')


def summarize(h, u, v, endpoints, lower, spacing):
    if (h.ndim != 2 or u.shape != h.shape or v.shape != h.shape
            or not np.isfinite([h,u,v]).all() or np.min(h) < 0
            or np.max(h) > 10 or np.max(np.hypot(u,v)) > 20):
        raise ValueError('Native state violates existing finite/depth/speed bounds')
    components, count = label(h > .05)
    ids = labels_at(endpoints, components, [0,0], lower, spacing)
    return dict(wet_cells=int((h>.05).sum()), components=count, endpoint_components=ids.tolist(),
        connected=bool(ids[0]>0 and ids[0]==ids[1]), maximum_depth_m=float(h.max()),
        maximum_speed_mps=float(np.hypot(u,v).max()), volume_m3=float(h.sum()*spacing**2))


def run(solver, output):
    solver, output = Path(solver).resolve(), Path(output).resolve()
    if output.exists() or shutil.disk_usage(ROOT).free < 41*1024**3:
        raise ValueError('Fresh output with preserved disk reserve required')
    if sha(solver) != '356f1af32946d69b7ccd55c2cd8390da4ea2095bf2c32a915316e7d8b9ab1dc8':
        raise ValueError('Use the regression-verified seed-ownership solver')
    terrain = LandscapeTriangles(ROOT/'tmp/futaleufu-context-terrain-v1')
    if terrain.manifest_sha256 != '503529a38131b108df9e6de3eb17a9b86967fafdb4a937e9a9d40f43e336d39d':
        raise ValueError('Resolution controls bind the inspected terrain snapshot')
    bed = FutaleufuBed(ROOT/'tmp/futaleufu-continuous-source-window-v2',
        PREFIX/'hydrology/channel_profile_2026_10_v2',
        PREFIX/'hydrography/confluence_network_2026_10_v1/network.json',depth_m=1.8)
    pins = {ROOT/p:h for p,h in terrain.manifest['evidence_source']['sources_sha256'].items()}
    pins.update({p:sha(p) for p in (solver, TEMPLATE, Path(__file__),
        Path(__file__).with_name('build_futaleufu_continuous_water_domain.py'),
        ROOT/'unreal/Plugins/SEIYGECore/python/scripts/solver_face_discharge.py')})
    def verify():
        terrain.verify_unchanged()
        if any(sha(p)!=digest for p,digest in pins.items()):
            raise ValueError('Bound control source or binary changed')
    verify()
    output.mkdir(parents=True)
    save(output/'launch.json', dict(scope=__doc__, steps=200, fixed_dt=.01,
        sources_sha256={str(p.relative_to(ROOT)):h for p,h in pins.items()}))
    runs = []
    try:
        for name, raw_endpoints in CASES.items():
            endpoints = np.asarray(raw_endpoints)
            lower = terrain.origin+np.floor((endpoints.min(axis=0)-20-terrain.origin)/2)*2
            upper = terrain.origin+np.ceil((endpoints.max(axis=0)+20-terrain.origin)/2)*2
            for spacing in (2.,1.,.5):
                case = output/(name+'_'+str(spacing).replace('.','p')+'m')
                package = case/'scenario'; package.mkdir(parents=True)
                x,y = np.meshgrid(np.arange(lower[0]+spacing/2,upper[0],spacing),
                    np.arange(lower[1]+spacing/2,upper[1],spacing))
                xy = np.stack((x,y),axis=-1)
                encoded = terrain.sample(xy)
                inferred = bed.sample(xy.reshape(-1,2))
                h, _ = initial_fields(encoded, inferred['reference_m'].reshape(encoded.shape),
                    inferred['bed_owned'].reshape(encoded.shape))
                ground = encoded-150.; zero = np.zeros_like(h)
                np.save(package/'bed.npy',ground)
                np.savez_compressed(package/'initial_state.npz',depth=h,eta=ground+h,
                    u=zero,v=zero,hu=zero,hv=zero,wet=h>1.e-6)
                save(package/'features.json',dict(features=[])); save(package/'probes.json',dict(probes=[]))
                scenario = copy.deepcopy(json.loads(TEMPLATE.read_text()))
                scenario['metadata'].update(scenario_id=name,scenario_type='real_world',fixture_kind=None,
                    river_id='futaleufu_river_chile',description=__doc__,generator=Path(__file__).name)
                scenario['grid'] = dict(nx=h.shape[1],ny=h.shape[0],dx=spacing,dy=spacing,
                    origin_x=lower[0]-terrain.origin[0]+spacing/2,origin_y=lower[1]-terrain.origin[1]+spacing/2)
                scenario.update(fixed_dt=.01,duration=2.,roughness=.045,feature_count=0,probe_count=0)
                scenario['boundaries'] = [dict(edge=e,kind='bank') for e in ('west','east','south','north')]
                save(package/'scenario.json',scenario)
                package_hashes = {p.name:sha(p) for p in package.iterdir()}
                command = [str(solver),'--scenario',str(package),'--output',str(case/'native'),
                    *SOLVER_FLAGS,'--steps','200','--frame-interval','20','--feature-strength-scale','0',
                    '--no-preserve-initial-mass','--stream-output','--progress']
                start = time.monotonic()
                with (case/'native.log').open('w') as log:
                    result = subprocess.run(command,stdout=log,stderr=subprocess.STDOUT,timeout=120,
                        env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1'))
                if result.returncode:
                    raise RuntimeError('Native control failed: '+str(case))
                native = case/'native'/name
                manifest = json.loads((native/'manifest.json').read_text())
                if len(manifest['frames']) != 11:
                    raise ValueError('Incomplete actual native frame series')
                frames = []
                for number, relative in enumerate(manifest['frames']):
                    with gzip.open(native/relative,'rt') as stream:
                        values = np.genfromtxt(stream,delimiter=',',names=True)
                    if len(values) != h.size or not np.isfinite(np.column_stack([values[k] for k in values.dtype.names])).all():
                        raise ValueError('Incomplete or nonfinite actual native capture')
                    expected_row,expected_col = np.indices(h.shape)
                    if not np.array_equal(values['row'],expected_row.ravel()) or not np.array_equal(values['col'],expected_col.ravel()):
                        raise ValueError('Native cell ordering differs')
                    actual = {k:values[k].reshape(h.shape) for k in ('h','u','v')}
                    row = summarize(**actual,endpoints=endpoints,lower=lower,spacing=spacing)
                    row.update(step=number*20, nominal_time_seconds=number*.2, file=relative,sha256=sha(native/relative))
                    if number == 0 and (not np.array_equal(actual['h'],h) or np.any(actual['u']) or np.any(actual['v'])):
                        raise ValueError('Native initialization differs from terrain-bound controls')
                    frames.append(row)
                drift = max(abs(f['volume_m3']-frames[0]['volume_m3']) for f in frames)
                if drift > 1e-8*max(1.,frames[0]['volume_m3']):
                    raise ValueError('Closed-domain native mass conservation failed')
                verify()
                if any(sha(package/p)!=digest for p,digest in package_hashes.items()):
                    raise ValueError('Native control inputs changed')
                record = dict(case=name,spacing_m=spacing,shape=list(h.shape),endpoints_m=endpoints.tolist(),
                    lower_m=lower.tolist(),upper_m=upper.tolist(),frames=frames,maximum_volume_drift_m3=drift,
                    native_exit_code=0,wall_seconds=time.monotonic()-start,source_inputs_unchanged=True,
                    package_files_sha256=package_hashes,command=command,terrain_modified=False,
                    through_flow_accepted=False,engine_accepted=False)
                save(case/'result.json',record);runs.append(record)
                print(json.dumps(dict(case=name,spacing_m=spacing,initial_connected=frames[0]['connected'],
                    final_connected=frames[-1]['connected'],speed=frames[-1]['maximum_speed_mps'],mass_drift_m3=drift)),flush=True)
        save(output/'completion.json',dict(runs=runs,scope=__doc__,full_river_accepted=False))
    except Exception as error:
        save(output/'failure.json',dict(error=repr(error),completed_runs=len(runs)))
        raise


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--solver',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args();run(args.solver,args.out)
