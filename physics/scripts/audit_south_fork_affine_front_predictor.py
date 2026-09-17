"""Exercise the finite-time LOCAL predictor on recorded original front planes.

Each predictor freezes ONE original conditional interface depth/velocity and
extends those uniformly on its local half-plane. This deliberately differs
from the spatially varying inlet: no river state is updated or accepted.
"""
import argparse
from dataclasses import replace
from fractions import Fraction as F
import hashlib
import json
from pathlib import Path

import numpy as np

from exact_rational_json import decode_fraction, json_default
from subcell_affine_dry_fan import AffineDryFan, Radical, _clip
from subcell_exact_geometry import SourceFragment
from subcell_inlet_sweep_geometry import InletSweep


def digest(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def exact(value):
    return decode_fraction(value) if isinstance(value,(str,dict)) else F(value)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-report',required=True,type=Path)
    parser.add_argument('--source-sha256',required=True)
    parser.add_argument('--report',required=True,type=Path)
    args=parser.parse_args()
    if args.report.exists():raise FileExistsError(args.report)
    if digest(args.source_report)!=args.source_sha256:raise ValueError('Original trace report hash changed')
    source=json.loads(args.source_report.read_text())
    if source['schema']!='raftsim.south_fork.inlet_sweep_geometry.v1' or source.get('initial_water_context_cells')!=256:
        raise ValueError('Complete original surrounding-water audit required')
    for path,value in source['source_sha256'].items():
        if digest(path)!=value:raise ValueError('Changed original source: '+path)
    mesh_path,=[Path(p) for p in source['source_sha256'] if p.endswith('troublemaker_registered_source.npz')]
    # Validate every reported original triangle against the protected actual mesh.
    from south_fork_registered_mesh import RegisteredMeshSampler
    with np.load(mesh_path,allow_pickle=False) as mesh:
        sampler=RegisteredMeshSampler(mesh)
    fragments={}
    for item in source['registered_lateral_front_provenance']:
        sid=item['source_id'];xyz=sampler.xyz[sampler.faces[sid]]
        if not np.array_equal(xyz,np.asarray(item['original_xyz'])):raise ValueError('Original triangle changed')
        points=tuple(tuple(F(float(v)) for v in p) for p in xyz)
        a,b=(tuple(p[j]-points[0][j] for j in range(3)) for p in points[1:])
        determinant=a[0]*b[1]-a[1]*b[0]
        gradient=((a[2]*b[1]-b[2]*a[1])/determinant,(a[0]*b[2]-b[0]*a[2])/determinant)
        fragments[sid]=SourceFragment(sid,points,gradient)
    rows=[]
    for record in source['records']:
        if 'original_patch_dry_front_transfers' not in record:
            rows.append(dict(donor=record['donor'],receiver=record['receiver'],status='original-branch-unsupported'))
            continue
        checked=record['original_patch_dry_front_transfers']
        if not checked['initial_dry_support_verified'] or not checked['initial_support']['complete_initial_state']:
            raise ValueError('Missing original initial dry-state prerequisite')
        sweep=InletSweep(tuple(tuple(exact(x) for x in p) for p in record['original_inlet_xyz']),
                         tuple(map(exact,record['constant_inlet_velocity_mps'])),
                         exact(record['primary_height_scale']),exact(record['time_root']))
        r=sweep.time_root/2;tau=r**3;point,depth=sweep.point(r,0)
        owner,=[t for t in checked['transfers'] if exact(t['entry_time_interval'][0])<=tau<exact(t['entry_time_interval'][1])]
        if owner['wet_source']!=owner['dry_source']:
            rows.append(dict(donor=record['donor'],receiver=record['receiver'],status='different-source-traces-require-junction-solver'))
            continue
        sid=owner['wet_source'][1];fragment=fragments[sid]
        sign=1 if sweep.delta[0]*sweep.velocity[1]-sweep.delta[1]*sweep.velocity[0]>0 else -1
        normal=(-sign*sweep.velocity[1],sign*sweep.velocity[0])
        bed=fragment.polygon[0][2]+sum(g*(x-a) for g,x,a in zip(fragment.gradient,point,fragment.polygon[0]))
        fan=AffineDryFan(point,normal,depth,sweep.velocity,bed,fragment.gradient,sweep.gravity)
        coordinate=lambda p:sum(n*(x-o) for n,x,o in zip(normal,p,point))
        parts=[replace(fragment,polygon=_clip(fragment.polygon,coordinate,side)) for side in (False,True)]
        if any(p.area<=0 for p in parts):raise ValueError('Local source does not contain both interface traces')
        dt=sweep.time_root**3/10
        before=fan.integrate(fragment,0,energy_datum=bed)
        whole=fan.integrate(fragment,dt,energy_datum=bed)
        wet,dry=[fan.integrate(p,dt,energy_datum=bed) for p in parts]
        if dry['volume']<=0:raise ValueError('Positive finite-time dry-side receipt not established')
        for key in ('volume','energy_per_density'):
            if wet[key]+dry[key]!=whole[key]:raise ValueError('Exact source budget partition failed')
        if any(wet['momentum'][j]+dry['momentum'][j]!=whole['momentum'][j] for j in range(2)):
            raise ValueError('Exact source momentum partition failed')
        row=dict(donor=record['donor'],receiver=record['receiver'],source_id=sid,
                 original_patch_cell=owner['wet_source'][0],point=point,normal=normal,
                 local_depth=depth,local_velocity=sweep.velocity,original_bed=bed,
                 original_gradient=fragment.gradient,time_increment=dt,
                 original_authority=next(p['authority_codes'] for p in source['registered_lateral_front_provenance'] if p['source_id']==sid),
                 before=before,whole=whole,wet_side=wet,dry_side=dry,
                 exact_partition_passed=True,status='local-uniform-state-predictor-only',
                 actual_inlet_or_river_step_accepted=False)
        rows.append(row)
        print(json.dumps(dict(source_id=sid,cell=row['original_patch_cell'],positive_dry_receipt=True,
                              exact_partition_passed=True)),flush=True)
    files=[args.source_report,Path(__file__),Path(__file__).with_name('subcell_affine_dry_fan.py')]
    hashes={str(p.resolve()):digest(p) for p in files}
    for path,value in source['source_sha256'].items():
        if digest(path)!=value:raise ValueError('Source changed during local predictor audit')
    result=dict(schema='raftsim.south_fork.affine_front_predictor.v1',source_sha256=source['source_sha256'],
                predictor_sha256=hashes,records=rows,accepted=False,source_water_unchanged=True,
                scope=__doc__,boundary_note='Original triangle boundaries exchange mass, momentum and energy. Sum of wet/dry budgets equals the full local solution, not a closed-triangle time conservation claim. Adjacent slope junctions, spatial gradients of inlet state, multi-stream interactions and dispersive coupling remain unresolved.')
    def serialize(value):return value.record() if isinstance(value,Radical) else json_default(value)
    payload=json.dumps(result,indent=2,allow_nan=False,default=serialize)
    with args.report.open('x') as stream:stream.write(payload)


if __name__=='__main__':main()
