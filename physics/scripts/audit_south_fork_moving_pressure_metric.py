"""Original two-pole physical/canonical map on qualified moving-front cases.

Exact reference solves and coordinate/energy identities only. This is not a
native iteration-budget pass, nonlinear force closure, river step or scene pass.
"""
import argparse
import json
from pathlib import Path
import sys
import time

from audit_south_fork_affine_front_predictor import digest, exact
from exact_rational_json import json_default
from subcell_affine_dry_fan import Radical
from subcell_moving_pressure_metric import MovingPressureMetric


def number(value):
    if isinstance(value,dict) and set(value)=={'rational','radical_coefficient','radicand'}:
        return Radical(exact(value['radicand']),exact(value['rational']),exact(value['radical_coefficient']))
    return exact(value)


def case(record):
    data=record['common_front_pressure']
    volumes=tuple(map(number,data['volumes']));rates=tuple(map(number,data['volume_rates']))
    matrix=lambda key:tuple(tuple(map(number,row)) for row in data[key])
    parts=(record['wet_side'],record['dry_side']);part_rates=(record['wet_side_rates'],record['dry_side_rates'])
    active=data['active_original_parts']
    if tuple(number(parts[i]['volume']) for i in active)!=volumes:
        raise ValueError('Original momentum owners disagree with pressure mass')
    if tuple(number(part_rates[i]['volume_rate']) for i in active)!=rates:
        raise ValueError('Original momentum owners disagree with pressure mass rate')
    p=tuple(tuple(map(number,parts[i]['momentum'])) for i in active)
    pd=tuple(tuple(map(number,part_rates[i]['momentum_rate'])) for i in active)
    metric=MovingPressureMetric(volumes,rates,matrix('kinetic'),matrix('kinetic_rate'))
    print(json.dumps(dict(source_id=record['source_id'],phase='metric-ready')),flush=True)
    result=metric.evaluate(p,pd)
    if metric.physical_momentum(result['canonical_velocity'])!=p:
        raise ValueError('Original physical/canonical momentum round trip failed')
    if not all(v['exact_residual_zero'] and v['exact_rate_residual_zero'] for v in result['poles']):
        raise ValueError('Original pressure pole or differentiated pole failed')
    return dict(physical_momentum=p,physical_momentum_rate=pd,**result,accepted=False)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-report',required=True,type=Path)
    parser.add_argument('--source-sha256',required=True)
    parser.add_argument('--report',required=True,type=Path)
    args=parser.parse_args()
    if args.report.exists():raise FileExistsError(args.report)
    if digest(args.source_report)!=args.source_sha256:raise ValueError('Qualified pressure geometry report changed')
    source=json.loads(args.source_report.read_text())
    if source['schema']!='raftsim.south_fork.affine_front_pressure.v1' or not source['local_coupling_checks_passed']:
        raise ValueError('Qualified original shared pressure geometry required')
    protected={**source['source_sha256'],**source['implementation_sha256'],str(args.source_report.resolve()):args.source_sha256}
    scripts=Path(__file__).resolve().parent
    implementation={str(Path(m.__file__).resolve()):digest(m.__file__) for m in tuple(sys.modules.values())
                    if getattr(m,'__file__',None) and Path(m.__file__).resolve().parent==scripts}
    for path,value in protected.items():
        if digest(path)!=value:raise ValueError('Protected source changed: '+path)
    for path in protected.keys() & implementation.keys():
        if protected[path]!=implementation[path]:raise ValueError('Imported source version changed: '+path)
    rows=[]
    for index,record in enumerate(source['records']):
        if 'common_front_pressure' not in record:
            rows.append(record);continue
        start=time.perf_counter()
        print(json.dumps(dict(index=index,source_id=record['source_id'],phase='begin')),flush=True)
        result=case(record)
        rows.append(dict(record,moving_physical_metric=result))
        print(json.dumps(dict(index=index,source_id=record['source_id'],phase='passed',seconds=time.perf_counter()-start)),flush=True)
    for path,value in {**protected,**implementation}.items():
        if digest(path)!=value:raise ValueError('Source or implementation changed during audit: '+path)
    tested=[r for r in rows if 'moving_physical_metric' in r]
    passed=bool(tested) and all(r['moving_physical_metric']['exact_original_momentum_and_rate_reconstruction'] for r in tested)
    result=dict(schema='raftsim.south_fork.moving_pressure_metric.v1',source_sha256=protected,
                implementation_sha256=implementation,records=rows,local_metric_identities_passed=passed,
                native_40cg_accepted=False,nonlinear_or_gameplay_accepted=False,scope=__doc__)
    def serialize(value):return value.record() if isinstance(value,Radical) else json_default(value)
    with args.report.open('x') as stream:json.dump(result,stream,indent=2,allow_nan=False,default=serialize)
    return 0 if passed else 1


if __name__=='__main__':raise SystemExit(main())
