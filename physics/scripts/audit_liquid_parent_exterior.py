"""Verify native parent-face inflow velocity and outlet pressure readbacks.

Face selection comes from global cell ownership, independently of the shader's
world-position/dot-product query. This is zero-particle boundary verification,
not flow conservation, river realism or gameplay performance acceptance.
"""
import argparse
import json
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[2]


def compare(region,parent,boundary,pressure):
    nx,ny,nz=region['computational_cells']
    if boundary.shape!=(nz,ny,nx,4) or pressure.shape!=(nz,ny,nx) or not np.isfinite(boundary).all() or not np.isfinite(pressure).all():
        raise ValueError('Complete finite native boundary and pressure volumes required')
    rows=np.asarray(parent['packed_vectors'],dtype=np.float32)
    px,py,pz=map(int,rows[5]);first,upper=region['cell_bounds_xy']
    z=(np.arange(nz,dtype=np.float32)+np.float32(.5))*rows[4,2]+rows[2,2]
    offsets=[8,8+py,8+2*py,8+2*py+px];vector_offset=8+2*(px+py)
    inlet=outlet=bad_boundary=bad_pressure=0;max_pressure_error=0.;examples=[];columns=0
    prescribed_inlet=np.zeros((nz,ny,nx),dtype=bool)
    prescribed_outlet=np.zeros((nz,ny,nx),dtype=bool)
    for y in range(ny):
        for x in range(nx):
            gx=x+first[0];gy=y+py-upper[1]
            face=column=None
            if 2<=gy<py+2 and (gx<2 or gx>=px+2):
                face=0 if gx<2 else 1;column=py+1-gy
            elif 2<=gx<px+2 and (gy<2 or gy>=py+2):
                face=3 if gy<2 else 2;column=gx-2
            if face is None: continue # includes true parent XY corners
            columns+=1;row=rows[offsets[face]+column]
            vector=rows[vector_offset+offsets[face]-8+column]*np.array([1,-1,1],dtype=np.float32)
            outgoing=row[2]<0
            active=(z>row[0]) & (True if outgoing else z<row[1])
            for k in np.flatnonzero(active):
                actual=boundary[k,y,x]
                wanted_type=3 if outgoing else 1
                mismatch=actual[3]!=wanted_type
                if not outgoing:
                    # The native boundary texture itself is half precision.
                    mismatch |= not np.array_equal(actual[:3].astype('<f2'),vector.astype('<f2'))
                    inlet+=1
                    prescribed_inlet[k,y,x]=True
                else:
                    outlet+=1
                    prescribed_outlet[k,y,x]=True
                    wanted=np.float32(980)*max(np.float32(row[1]-z[k]),np.float32(0))
                    error=abs(float(pressure[k,y,x])-float(wanted));max_pressure_error=max(max_pressure_error,error)
                    # GPU FMA versus separately rounded reference position:
                    # bound two float32 height ULPs at both operands, converted
                    # to pressure. This is not a tunable hydraulic tolerance.
                    tolerance=1960*(abs(float(np.spacing(z[k])))+abs(float(np.spacing(row[1]))))
                    if error>tolerance:
                        bad_pressure+=1
                        if len(examples)<12: examples.append(dict(kind='pressure',region=region['id'],xyz=[x,y,int(k)],actual=float(pressure[k,y,x]),expected=float(wanted),roundoff_bound=tolerance))
                if mismatch:
                    bad_boundary+=1
                    if len(examples)<12: examples.append(dict(kind='boundary',region=region['id'],xyz=[x,y,int(k)],face=face,column=column,actual=actual.tolist(),expected_type=wanted_type,expected_velocity=vector.astype('<f2').tolist()))
    return dict(region_id=region['id'],parent_face_columns=columns,inlet_cells=inlet,outlet_cells=outlet,
                boundary_mismatches=bad_boundary,pressure_mismatches=bad_pressure,
                unexpected_outlet_cells=int(((boundary[...,3]==3)&~prescribed_outlet).sum()),
                unforced_velocity_cells=int((np.any(boundary[...,:3]!=0,axis=-1)&~prescribed_inlet).sum()),
                unprescribed_pressure_cells=int(((pressure!=0)&~prescribed_outlet).sum()),
                maximum_pressure_error_cm2_per_s2=max_pressure_error,mismatch_examples=examples)


def audit(directory):
    directory=Path(directory);report=json.loads((directory/'stages.json').read_text())
    capture=json.loads((directory/'capture.json').read_text())
    required=('zero_water','parent_exterior_forcing_installed','boundary_readback_valid',
              'outlet_pressure_readback_valid','shared_boundary_exchange_enabled')
    if not capture['complete'] or not all(report.get(k) for k in required): raise ValueError('Successful native parent exterior capture required')
    boundaries={r['region_id']:r for r in report['boundary_readbacks']}
    pressures={r['region_id']:r for r in report['outlet_pressure_readbacks']}
    if sorted(boundaries)!=list(range(12)) or sorted(pressures)!=list(range(12)) or len(report['boundary_readbacks'])!=12 or len(report['outlet_pressure_readbacks'])!=12:
        raise ValueError('Exactly all twelve native owner readbacks required')
    states=ROOT/'tmp/south-fork-liquid-regional-state-20260910'
    parent=json.loads((ROOT/'tmp/south-fork-whole-rapid-liquid-float-seeds-20260910/grid_vector_boundary_profile.json').read_text())
    results=[]
    for rid in range(12):
        region=json.loads((states/f'region-{rid:03d}.json').read_text());nx,ny,nz=region['computational_cells']
        values=[]
        for item,dtype,channels in ((boundaries[rid],'<f2',4),(pressures[rid],'<f4',1)):
            path=directory/item['file']
            if path.resolve().parent!=directory.resolve() or item['voxel_count']!=nx*ny*nz: raise ValueError('Invalid native readback path/extent')
            raw=np.fromfile(path,dtype=dtype)
            if raw.size!=nx*ny*nz*channels: raise ValueError('Partial native exterior readback')
            values.append(raw.reshape((nz,ny,nx,4) if channels==4 else (nz,ny,nx)))
        results.append(compare(region,parent,*values))
    checks=('boundary_mismatches','pressure_mismatches','unexpected_outlet_cells','unforced_velocity_cells','unprescribed_pressure_cells')
    accepted=all(all(r[key]==0 for key in checks) for r in results)
    accepted &= sum(r['inlet_cells'] for r in results)>0 and sum(r['outlet_cells'] for r in results)>0
    return dict(parent_inflow_and_outlet_pressure_verified=bool(accepted),regions=results,
                inlet_cells=sum(r['inlet_cells'] for r in results),outlet_cells=sum(r['outlet_cells'] for r in results),
                wet_flux_conservation_verified=False,visual_or_performance_acceptance=False,
                pressure_tolerance='two float32 height ULPs per operand times gravity; boundary values exact native half')


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('capture');parser.add_argument('--output',required=True)
    args=parser.parse_args();output=Path(args.output)
    if output.exists(): raise FileExistsError('Retain previous exterior evidence')
    result=audit(args.capture);output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='regions'},indent=2))
    raise SystemExit(0 if result['parent_inflow_and_outlet_pressure_verified'] else 1)
