"""Bounded dense independent solve audit; never changes production/PCG policy."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import numpy as np
from total_depth_nonlinear_pressure import AccelerationSystem, nonlinear_pressure_force
from pressure_cg_range_reference import solve as range_solve


def read_cases(data):
    magic,version,count=struct.unpack_from('<III',data);at=12
    if magic!=0x52535046 or version!=1 or not 5<=count<=64:raise ValueError('Expected pressure fixture v1')
    for index in range(count):
        nx,ny,periodic,dx=struct.unpack_from('<IIIf',data,at);at+=16
        if not 1<=nx*ny<=1024:raise ValueError('Dense diagnostic limited to 1024 cells')
        fields=[]
        for k,components in enumerate((2,4,4,2,1,1,4,4,4,2)):
            length=nx*ny*components
            value=np.frombuffer(data,dtype='<u4' if k==5 else '<f4',count=length,offset=at);at+=length*4
            fields.append(value.reshape(ny,nx,components) if components>1 else value.reshape(ny,nx))
        yield index,fields,dx,bool(periodic)
    if at!=len(data):raise ValueError('Trailing fixture bytes')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('fixture',type=Path);parser.add_argument('--report',type=Path,required=True)
    args=parser.parse_args()
    if args.report.exists():raise FileExistsError(args.report)
    data=args.fixture.read_bytes();records=[]
    original=AccelerationSystem.solve
    for index,fields,dx,periodic in read_cases(data):
        geometry,state,rate,slope,fraction,packed,rhs,correction,pressure,expected_force=fields
        h=geometry[...,0].astype(float)
        if not np.any((h>0)&(h<=2.**-126)):continue
        velocity=np.divide(state[...,1:3].astype(float),h[...,None],out=np.zeros((*h.shape,2)),where=h[...,None]>0)
        solve_records=[];range_records=[]
        def direct(system,right,iterations=40,**kwargs):
            n=right.size;matrix=np.empty((n,n));basis=np.zeros_like(right)
            for j in range(n):
                basis.flat[j]=1;matrix[:,j]=system.apply(basis).ravel();basis.flat[j]=0
            result=np.linalg.solve(matrix,right.ravel()).reshape(right.shape)
            residual=system.apply(result)-right;norm=np.linalg.norm(right.ravel())
            relative=float(np.linalg.norm(residual.ravel())/(norm if norm else 1))
            solve_records.append(dict(maximum_rhs=float(abs(right).max()),
                symmetry_error=float(abs(matrix-matrix.T).max()),relative_residual=relative,
                maximum_residual=float(abs(residual).max())))
            for arithmetic in (np.float64,np.float32):
                ranged,stats=range_solve(system,right,arithmetic=arithmetic)
                delta=ranged-result
                range_records.append(dict(arithmetic=np.dtype(arithmetic).name,**stats,
                    maximum_solution_error=float(abs(delta).max()),
                    maximum_physical_solution_error=float(abs(np.sqrt(system.h)[...,None]*delta).max())))
            return result,dict(iterations=0,relative_residual=relative,method='dense_direct_diagnostic')
        try:
            AccelerationSystem.solve=direct
            force,_=nonlinear_pressure_force(h,geometry[...,1].astype(float),velocity,velocity*0,
                [(packed&1)!=0,(packed&2)!=0],dx,interpolation='depth_weighted',formulation='kinematic',
                mass_rate=rate[...,0].astype(float),momentum_rate=rate[...,1:3].astype(float),
                bed_slope=slope.astype(float),dispersion_fraction=fraction.astype(float))
        finally:AccelerationSystem.solve=original
        ranged_forces={}
        for arithmetic in (np.float64,np.float32):
            try:
                AccelerationSystem.solve=lambda system,right,**kwargs:range_solve(system,right,arithmetic=arithmetic,**kwargs)
                ranged,_=nonlinear_pressure_force(h,geometry[...,1].astype(float),velocity,velocity*0,
                    [(packed&1)!=0,(packed&2)!=0],dx,interpolation='depth_weighted',formulation='kinematic',
                    mass_rate=rate[...,0].astype(float),momentum_rate=rate[...,1:3].astype(float),
                    bed_slope=slope.astype(float),dispersion_fraction=fraction.astype(float))
                ranged_forces[np.dtype(arithmetic).name]=dict(maximum_error=float(abs(ranged-force).max()),
                    relative_error=float(np.linalg.norm((ranged-force).ravel())/np.linalg.norm(force.ravel())))
            finally:AccelerationSystem.solve=original
        delta=force-expected_force
        records.append(dict(case=index,minimum_positive_depth=float(h[h>0].min()),solves=solve_records,
            range_recurrence=range_records,range_force_comparison=ranged_forces,
            maximum_force_error_vs_iterative_fixture=float(abs(delta).max()),
            relative_force_error_vs_iterative_fixture=float(np.linalg.norm(delta.ravel())/np.linalg.norm(force.ravel())),
            maximum_dense_force=float(abs(force).max())))
    report=dict(schema='raftsim.pressure_dense_diagnostic.v1',scope=__doc__,scene_accepted=False,
        fixture_sha256=hashlib.sha256(data).hexdigest(),cases=records,
        implementation_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    with args.report.open('x') as output:json.dump(report,output,indent=2,allow_nan=False)
    print(json.dumps(report,indent=2,allow_nan=False))


if __name__=='__main__':main()
