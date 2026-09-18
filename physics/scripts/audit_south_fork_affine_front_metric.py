"""Check moving-front pressure geometry on the protected original local predictors.

Uses their exact states/planes, NOT a spatially varying inlet or a river update.
All preceding records are preserved; full gameplay acceptance stays false.
"""
import argparse
from dataclasses import replace
from fractions import Fraction as F
import json
import hashlib
import subprocess
import sys
from pathlib import Path

import numpy as np

from audit_south_fork_affine_front_predictor import digest, exact, magnitude
from exact_rational_json import json_default
from south_fork_registered_mesh import RegisteredMeshSampler
from subcell_affine_dry_fan import AffineDryFan, Radical, _clip
from subcell_affine_front_metric import front_metric
from subcell_exact_geometry import SourceFragment

ROOT=Path(__file__).resolve().parents[2]


def git_blob(path,revision):
    return subprocess.run(['git','show',revision+':'+path.relative_to(ROOT).as_posix()],
                          cwd=ROOT,check=True,capture_output=True).stdout


def verify_protected(protected,historical):
    """Keep prior hashes immutable; verify explicitly named historical tools.

    Only non-imported Python audit/preparation tools may resolve from Git.
    Measured inputs, water arrays and code loaded for this computation MUST
    match current bytes. Changed tools are reported, never silently rehashed.
    """
    requested={str(Path(p).resolve()):rev for p,rev in historical.items()}
    known={str(Path(p).resolve()):sha for p,sha in protected.items()}
    if not requested.keys()<=known.keys():raise ValueError('Historical tool is absent from protected provenance')
    imported={str(Path(m.__file__).resolve()) for m in tuple(sys.modules.values())
              if getattr(m,'__file__',None)}
    current={};records=[]
    for name,expected in known.items():
        path=Path(name);value=digest(path);current[name]=value
        if name in requested:
            if path.suffix!='.py' or path.parent!=ROOT/'physics/scripts' or name in imported:
                raise ValueError('Historical exception cannot replace source data or loaded physics code')
            revision=requested[name]
            if not revision or any(c not in '0123456789abcdef' for c in revision) or len(revision)!=40:
                raise ValueError('Explicit full historical Git commit required')
            blob=git_blob(path,revision)
            if hashlib.sha256(blob).hexdigest()!=expected:
                raise ValueError('Historical bytes do not match the original report')
            records.append(dict(path=name,revision=revision,recorded_sha256=expected,
                                current_sha256=value,current_matches_recorded=value==expected,
                                used_for_this_computation=False))
        elif value!=expected:raise ValueError('Protected source changed: '+name)
    return current,records


def temporal_metric_check(fan, fragment, time, form):
    """Independent time differences at retained scales, unchanged 1e-10 gate.

    Scale by the independently accumulated absolute local moment-time work;
    no pre-existing moment/time denominator and no float floor.
    Two consecutive scales must pass, including all three metric moments.
    """
    scales=form['depth_moment_rate_scales']
    history=[]
    for divisor in (256,512,1024,2048,4096,8192,16384):
        eps=time/divisor
        a=front_metric(fan,fragment,time-eps)['depth_moments'][1:]
        b=front_metric(fan,fragment,time+eps)['depth_moments'][1:]
        error=tuple(magnitude((y-x)/(2*eps)-r) for x,y,r in zip(a,b,form['depth_moment_rates']))
        ratios=tuple(e/s if s>0 else fan.zero if e==0 else None for e,s in zip(error,scales))
        passed=all(r is not None and r<=F(1,10**10) for r in ratios)
        history.append(dict(divisor=divisor,absolute_errors=error,scaled_errors=ratios,passed=passed))
        if passed and len(history)>1 and history[-2]['passed']:break
    return dict(scales=scales,refinements=history,relative_gate=F(1,10**10),
                passed=passed and len(history)>1 and history[-2]['passed'])


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-report',required=True,type=Path)
    parser.add_argument('--source-sha256',required=True)
    parser.add_argument('--report',required=True,type=Path)
    parser.add_argument('--historical-tool',action='append',default=[],metavar='PATH=COMMIT')
    args=parser.parse_args()
    if args.report.exists():raise FileExistsError(args.report)
    if digest(args.source_report)!=args.source_sha256:raise ValueError('Original predictor report changed')
    source=json.loads(args.source_report.read_text())
    if source['schema']!='raftsim.south_fork.affine_front_predictor.v1' or not source['local_rate_controls_passed']:
        raise ValueError('Qualified local predictor/rate record required')
    protected={**source['source_sha256'],**source['predictor_sha256'],
               str(args.source_report.resolve()):args.source_sha256}
    historical={}
    for item in args.historical_tool:
        path,revision=item.rsplit('=',1)
        if path in historical:raise ValueError('Duplicate historical tool')
        historical[path]=revision
    current,historical_records=verify_protected(protected,historical)
    mesh_path,=[p for p in protected if p.endswith('troublemaker_registered_source.npz')]
    with np.load(mesh_path,allow_pickle=False) as mesh:sampler=RegisteredMeshSampler(mesh)
    rows=[]
    for record in source['records']:
        if record['status']!='local-uniform-state-predictor-only':
            rows.append(record);continue
        point,normal=tuple(map(exact,record['point'])),tuple(map(exact,record['normal']))
        depth=exact(record['local_depth']);gradient=tuple(map(exact,record['original_gradient']))
        # Recover the exact recorded gravity from its quadratic field instead
        # of silently swapping binary 9.81 for the different rational 981/100.
        old=record['whole']['volume'];d=exact(old['radicand'])
        gravity=d/(depth*sum(n*n for n in normal))
        fan=AffineDryFan(point,normal,depth,tuple(map(exact,record['local_velocity'])),
                         exact(record['original_bed']),gradient,gravity)
        sid=record['source_id'];xyz=sampler.xyz[sampler.faces[sid]]
        fragment=SourceFragment(sid,tuple(tuple(F(float(v)) for v in p) for p in xyz),gradient)
        time=exact(record['time_increment']);form=front_metric(fan,fragment,time)
        if form['depth_moments'][1]!=Radical(d,exact(old['rational']),exact(old['radical_coefficient'])):
            raise ValueError('Recorded predictor volume changed')
        old_rate=record['boundary_rates']['volume_rate']
        if form['depth_moment_rates'][0]!=Radical(exact(old_rate['radicand']),
                exact(old_rate['rational']),exact(old_rate['radical_coefficient'])):
            raise ValueError('Metric mass rate differs from independent original boundary fluxes')
        coordinate=lambda p:sum(n*(x-o) for n,x,o in zip(normal,p,point))
        parts=[front_metric(fan,replace(fragment,polygon=_clip(fragment.polygon,coordinate,side)),time)
               for side in (False,True)]
        for key in ('depth_moments','depth_moment_rates','depth_moment_rate_scales'):
            if tuple(a+b for a,b in zip(parts[0][key],parts[1][key]))!=form[key]:
                raise ValueError('Original source metric partition is not exact')
        for key in ('gram','gram_rate'):
            if any(parts[0][key][i][j]+parts[1][key][i][j]!=form[key][i][j] for i in range(3) for j in range(3)):
                raise ValueError('Original source matrix partition is not exact')
        temporal=temporal_metric_check(fan,fragment,time,form)
        rows.append(dict(record,moving_front_metric=form,wet_side_metric=parts[0],dry_side_metric=parts[1],
                         metric_temporal_check=temporal,exact_metric_partition_passed=True,
                         exact_boundary_mass_rate_passed=True))
        print(json.dumps(dict(source_id=sid,metric_partition=True,time_check=temporal['passed'],
                              divisors=[r['divisor'] for r in temporal['refinements']])),flush=True)
    for path,value in current.items():
        if digest(path)!=value:raise ValueError('Protected source changed during audit: '+path)
    tested=[r for r in rows if 'moving_front_metric' in r]
    passed=bool(tested) and all(r['metric_temporal_check']['passed'] for r in tested)
    result=dict(schema='raftsim.south_fork.affine_front_metric.v1',source_sha256=protected,
                current_source_sha256=current,historical_tool_versions=historical_records,
                implementation_sha256={str(p.resolve()):digest(p) for p in
                    (Path(__file__),Path(__file__).with_name('subcell_affine_front_metric.py'))},
                records=rows,local_metric_checks_passed=passed,accepted=False,scope=__doc__,
                source_water_unchanged=True)
    def serialize(value):return value.record() if isinstance(value,Radical) else json_default(value)
    with args.report.open('x') as stream:json.dump(result,stream,indent=2,allow_nan=False,default=serialize)
    return 0 if passed else 1


if __name__=='__main__':raise SystemExit(main())
