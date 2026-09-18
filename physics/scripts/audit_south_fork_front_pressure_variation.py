"""Original-case pressure-energy pullback, not a conservative force closure.

Reconstruct the original source geometry and check the saved exact unknowns
against both original pole equations and physical momentum. Then contract the
primitive derivatives with the original time rates in both momentum coordinates.
No previously solved unknown, source record or acceptance gate is replaced.
"""
import argparse
from dataclasses import replace
from fractions import Fraction as F
import json
from pathlib import Path
import sys
import time

import numpy as np

from audit_south_fork_affine_front_predictor import digest, exact
from audit_south_fork_moving_pressure_metric import number
from exact_rational_json import json_default
from south_fork_registered_mesh import RegisteredMeshSampler
from subcell_affine_dry_fan import AffineDryFan, Radical, _clip
from subcell_affine_front_pressure import FrontPressureGeometry
from subcell_exact_geometry import SourceFragment
from subcell_front_pressure_variation import FrontPressureVariation
from subcell_moving_pressure_metric import MovingPressureMetric


def numeric(value):
    if isinstance(value,Radical):return value
    return number(value)


def vector(value):return tuple(tuple(map(numeric,row)) for row in value)


def geometry(record,sampler):
    point,normal=tuple(map(exact,record['point'])),tuple(map(exact,record['normal']))
    depth=exact(record['local_depth']);gradient=tuple(map(exact,record['original_gradient']))
    d=exact(record['whole']['volume']['radicand'])
    fan=AffineDryFan(point,normal,depth,tuple(map(exact,record['local_velocity'])),
        exact(record['original_bed']),gradient,d/(depth*sum(n*n for n in normal)))
    sid=record['source_id'];xyz=sampler.xyz[sampler.faces[sid]]
    fragment=SourceFragment(sid,tuple(tuple(F(float(v)) for v in p) for p in xyz),gradient)
    coordinate=lambda p:sum(n*(x-o) for n,x,o in zip(normal,p,point))
    fragments=tuple(replace(fragment,polygon=_clip(fragment.polygon,coordinate,side)) for side in (False,True))
    return FrontPressureGeometry(fan,fragments,exact(record['time_increment']),outer_boundary='reflecting')


def check_case(g,record):
    prior=record['common_front_pressure'];saved=record['moving_physical_metric']
    if (prior['outer_pressure_boundary']!='reflecting' or tuple(prior['active_original_parts'])!=g.active
            or tuple(map(numeric,prior['volumes']))!=g.volumes
            or tuple(map(numeric,prior['volume_rates']))!=g.volume_rates):
        raise ValueError('Original pressure owners, boundary and volume rates must match')
    for key in ('divergence','divergence_rate','kinetic','kinetic_rate'):
        if vector(prior[key])!=tuple(map(tuple,getattr(g,key))):
            raise ValueError('Original reconstructed pressure geometry changed: '+key)
    if len(prior['faces'])!=len(g.faces):raise ValueError('Original pressure face count changed')
    for old,new in zip(prior['faces'],g.faces):
        if tuple(old['owners'])!=tuple(new['owners']):raise ValueError('Original face ownership changed')
        for key in ('first','last','column_normal','column_normal_rate'):
            if tuple(map(numeric,old[key]))!=tuple(new[key]):raise ValueError('Original face geometry changed: '+key)
    p=vector(saved['physical_momentum']);pd=vector(saved['physical_momentum_rate'])
    parts=(record['wet_side'],record['dry_side']);rates=(record['wet_side_rates'],record['dry_side_rates'])
    if p!=vector([parts[i]['momentum'] for i in g.active]) or pd!=vector([rates[i]['momentum_rate'] for i in g.active]):
        raise ValueError('Original physical momentum or rate changed')
    state=dict(canonical_velocity=vector(saved['canonical_velocity']),poles=[dict(
        length=numeric(p['length']),weight=numeric(p['weight']),auxiliary_velocity=vector(p['auxiliary_velocity']))
        for p in saved['poles']])
    metric=MovingPressureMetric(g.volumes,g.volume_rates,g.kinetic,g.kinetic_rate)
    variation=FrontPressureVariation(g,metric,p,solved_state=state)
    physical=variation.time_work(pd)
    canonical=variation.time_work(vector(saved['canonical_momentum_rate']),momentum_coordinate='canonical')
    if physical['energy_direction']!=numeric(saved['kinetic_energy_rate']) or canonical['energy_direction']!=physical['energy_direction']:
        raise ValueError('Original complete pressure time work changed')
    if (physical['momentum_work']!=numeric(saved['momentum_work']) or
            physical['depth_moment_work']+physical['face_column_work']!=numeric(saved['geometry_time_work']) or
            physical['bed_gradient_work']!=0):
        raise ValueError('Original pressure momentum/geometry work split changed')
    matrix_work=sum((a*b for a,b in zip(variation.mass_gradient,metric.mass_rate)),metric.zero)
    matrix_work+=sum((variation.kinetic_gradient[i][j]*g.kinetic_rate[i][j]
                     for i in range(len(metric.mass)) for j in range(len(metric.mass))),metric.zero)
    if matrix_work!=numeric(saved['geometry_time_work']):raise ValueError('Primitive and full matrix work disagree')
    names=('momentum_gradient','depth_moment_gradients','face_column_gradients','bed_gradient_gradients',
           'canonical_momentum_gradient','canonical_depth_moment_gradients',
           'canonical_face_column_gradients','canonical_bed_gradient_gradients')
    return dict(physical_time_work=physical,canonical_time_work=canonical,matrix_geometry_work=matrix_work,
                **{name:getattr(variation,name) for name in names},exact_original_case_pullback=True,
                native_or_conservative_force_or_wetting_or_gameplay_accepted=False)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-report',type=Path,required=True)
    parser.add_argument('--source-sha256',required=True)
    parser.add_argument('--report',type=Path,required=True)
    args=parser.parse_args()
    if args.report.exists():raise FileExistsError(args.report)
    if digest(args.source_report)!=args.source_sha256:raise ValueError('Qualified source report changed')
    source=json.loads(args.source_report.read_text())
    if source['schema']!='raftsim.south_fork.moving_pressure_metric.v1' or source['local_metric_identities_passed'] is not True:
        raise ValueError('Qualified original two-pole source report required')
    protected={**source['source_sha256'],**source['implementation_sha256'],str(args.source_report.resolve()):args.source_sha256}
    scripts=Path(__file__).resolve().parent
    implementation={str(Path(m.__file__).resolve()):digest(m.__file__) for m in tuple(sys.modules.values())
                    if getattr(m,'__file__',None) and Path(m.__file__).resolve().parent==scripts}
    for path,value in protected.items():
        if digest(path)!=value:raise ValueError('Protected source changed: '+path)
    for path in protected.keys() & implementation.keys():
        if protected[path]!=implementation[path]:raise ValueError('Imported source version changed: '+path)
    mesh_path,=[p for p in protected if p.endswith('troublemaker_registered_source.npz')]
    with np.load(mesh_path,allow_pickle=False) as mesh:sampler=RegisteredMeshSampler(mesh)
    rows=[]
    for index,record in enumerate(source['records']):
        if 'moving_physical_metric' not in record:
            rows.append(record);continue
        started=time.perf_counter()
        print(json.dumps(dict(index=index,source_id=record['source_id'],phase='begin')),flush=True)
        g=geometry(record,sampler)
        print(json.dumps(dict(index=index,source_id=record['source_id'],phase='geometry-ready')),flush=True)
        result=check_case(g,record)
        rows.append(dict(record,front_pressure_variation=result))
        print(json.dumps(dict(index=index,source_id=record['source_id'],phase='passed',seconds=time.perf_counter()-started)),flush=True)
    for path,value in {**protected,**implementation}.items():
        if digest(path)!=value:raise ValueError('Source or implementation changed during audit: '+path)
    tested=[r for r in rows if 'front_pressure_variation' in r]
    passed=bool(tested) and all(r['front_pressure_variation']['exact_original_case_pullback'] for r in tested)
    result=dict(schema='raftsim.south_fork.front_pressure_variation.v1',source_sha256=protected,
        implementation_sha256=implementation,records=rows,local_variation_checks_passed=passed,
        native_or_conservative_force_or_wetting_or_gameplay_accepted=False,scope=__doc__)
    def serialize(value):return value.record() if isinstance(value,Radical) else json_default(value)
    with args.report.open('x') as stream:json.dump(result,stream,indent=2,allow_nan=False,default=serialize)
    return 0 if passed else 1


if __name__=='__main__':raise SystemExit(main())
