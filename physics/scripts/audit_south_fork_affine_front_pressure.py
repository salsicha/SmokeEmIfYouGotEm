"""Exercise shared moving-front pressure geometry on original South Fork cases.

Retains the original local predictors and their limitations. These are NOT
interacting fronts, a full varying inlet, a native solve or gameplay acceptance.
"""
import argparse
from dataclasses import replace
from fractions import Fraction as F
import json
from pathlib import Path
import sys

import numpy as np

from audit_south_fork_affine_front_predictor import digest, exact, magnitude
from exact_rational_json import json_default
from south_fork_registered_mesh import RegisteredMeshSampler
from subcell_affine_dry_fan import AffineDryFan, Radical, _clip
from subcell_affine_front_pressure import FrontPressureGeometry
from subcell_exact_geometry import SourceFragment


def temporal_check(fan, fragments, time, geometry):
    """Independent fourth-order time differences; unchanged 1e-10 work gate.

    Scale by gross matrix-time work, not pre-existing kinetic energy / tiny dt.
    Two successive Richardson-refined centered probes must pass. The analytic
    implementation never uses these differences to generate its time rate.
    """
    n=2*len(geometry.active);zero=fan.zero
    scale=sum((magnitude(geometry.metric_rate[i][j])+magnitude(geometry.divergence_geometry_rate[i][j])
               for i in range(n) for j in range(n)),zero)
    previous=None;history=[]
    for divisor in (128,256,512,1024,2048,4096,8192,16384):
        eps=time/divisor
        pairs=[FrontPressureGeometry(fan,fragments,time+sign*eps,outer_boundary='reflecting') for sign in (-1,1)]
        if any(p.active!=geometry.active for p in pairs):
            raise ValueError('Time probe crossed active pressure topology')
        central=[[(pairs[1].kinetic[i][j]-pairs[0].kinetic[i][j])/(2*eps) for j in range(n)] for i in range(n)]
        if previous is not None:
            error=sum((magnitude((4*central[i][j]-previous[i][j])/3-geometry.kinetic_rate[i][j])
                       for i in range(n) for j in range(n)),zero)
            ratio=error/scale if scale>0 else zero if error==0 else None
            passed=ratio is not None and ratio<=F(1,10**10)
            history.append(dict(divisor=divisor,absolute_matrix_error=error,scaled_error=ratio,passed=passed))
            if passed and len(history)>1 and history[-2]['passed']:break
        previous=central
    return dict(gross_matrix_time_work=scale,relative_gate=F(1,10**10),refinements=history,
                passed=len(history)>1 and history[-1]['passed'] and history[-2]['passed'])


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-report',required=True,type=Path)
    parser.add_argument('--source-sha256',required=True)
    parser.add_argument('--report',required=True,type=Path)
    args=parser.parse_args()
    if args.report.exists():raise FileExistsError(args.report)
    if digest(args.source_report)!=args.source_sha256:raise ValueError('Original metric report changed')
    source=json.loads(args.source_report.read_text())
    if source['schema']!='raftsim.south_fork.affine_front_metric.v1' or not source['local_metric_checks_passed']:
        raise ValueError('Qualified original moving-front metric record required')
    protected={**source['current_source_sha256'],**source['implementation_sha256'],
               str(args.source_report.resolve()):args.source_sha256}
    for path,value in protected.items():
        if digest(path)!=value:raise ValueError('Protected source changed: '+path)
    mesh_path,=[p for p in protected if p.endswith('troublemaker_registered_source.npz')]
    with np.load(mesh_path,allow_pickle=False) as mesh:sampler=RegisteredMeshSampler(mesh)
    rows=[]
    for record in source['records']:
        if record['status']!='local-uniform-state-predictor-only':
            rows.append(record);continue
        point,normal=tuple(map(exact,record['point'])),tuple(map(exact,record['normal']))
        depth=exact(record['local_depth']);gradient=tuple(map(exact,record['original_gradient']))
        old=record['whole']['volume'];d=exact(old['radicand'])
        fan=AffineDryFan(point,normal,depth,tuple(map(exact,record['local_velocity'])),
                         exact(record['original_bed']),gradient,d/(depth*sum(n*n for n in normal)))
        sid=record['source_id'];xyz=sampler.xyz[sampler.faces[sid]]
        fragment=SourceFragment(sid,tuple(tuple(F(float(v)) for v in p) for p in xyz),gradient)
        time=exact(record['time_increment'])
        coordinate=lambda p:sum(n*(x-o) for n,x,o in zip(normal,p,point))
        fragments=tuple(replace(fragment,polygon=_clip(fragment.polygon,coordinate,side)) for side in (False,True))
        geometry=FrontPressureGeometry(fan,fragments,time,outer_boundary='reflecting')
        if sum(geometry.volumes,fan.zero)!=Radical(d,exact(old['rational']),exact(old['radical_coefficient'])):
            raise ValueError('Coupled pressure geometry changed original volume')
        common=[f for f in geometry.faces if len(f['owners'])==2]
        if len(common)!=1 or common[0]['parameter_depth_integral']<=0:
            raise ValueError('Original initial-front split lacks a shared wet pressure column')
        n=2*len(geometry.active)
        if any(geometry.kinetic[i][j]!=geometry.kinetic[j][i] or
               geometry.kinetic_rate[i][j]!=geometry.kinetic_rate[j][i] for i in range(n) for j in range(n)):
            raise ValueError('Exact common pressure adjoint symmetry failed')
        temporal=temporal_check(fan,fragments,time,geometry)
        value=dict(active_original_parts=geometry.active,volumes=geometry.volumes,volume_rates=geometry.volume_rates,
                   divergence=geometry.divergence,divergence_rate=geometry.divergence_rate,
                   kinetic=geometry.kinetic,kinetic_rate=geometry.kinetic_rate,faces=geometry.faces,
                   temporal_check=temporal,outer_pressure_boundary='reflecting',accepted=False)
        rows.append(dict(record,common_front_pressure=value))
        print(json.dumps(dict(source_id=sid,active=len(geometry.active),time_check=temporal['passed'],
                              divisors=[r['divisor'] for r in temporal['refinements']])),flush=True)
    for path,value in protected.items():
        if digest(path)!=value:raise ValueError('Protected source changed during audit: '+path)
    scripts=Path(__file__).resolve().parent
    implementation={str(Path(m.__file__).resolve()):digest(m.__file__) for m in tuple(sys.modules.values())
                    if getattr(m,'__file__',None) and Path(m.__file__).resolve().parent==scripts}
    tested=[r for r in rows if 'common_front_pressure' in r]
    passed=bool(tested) and all(r['common_front_pressure']['temporal_check']['passed'] for r in tested)
    result=dict(schema='raftsim.south_fork.affine_front_pressure.v1',source_sha256=protected,
                historical_tool_versions=source['historical_tool_versions'],implementation_sha256=implementation,
                records=rows,local_coupling_checks_passed=passed,accepted=False,scope=__doc__)
    def serialize(value):return value.record() if isinstance(value,Radical) else json_default(value)
    with args.report.open('x') as stream:json.dump(result,stream,indent=2,allow_nan=False,default=serialize)
    return 0 if passed else 1


if __name__=='__main__':raise SystemExit(main())
