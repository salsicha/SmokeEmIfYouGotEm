"""Reproducible CPU double-reference fixtures for the actual GPU pressure path.

Inputs are explicitly quantized to float32 FIRST, then the CPU reference solves
that represented state with its actual reconstructed FV graph and rounded FV
rates. Source quantization loss is recorded, never called scene acceptance.
Output is a fresh binary artifact plus a source/hash manifest; no input changes.
"""
import argparse
import hashlib
import json
import struct
from pathlib import Path
import numpy as np
import total_depth_bank_replay as bank
from audit_detail_wave_regime import read_snapshot
from breaking_front_reference import dispersion_fraction
from total_depth_nonlinear_pressure import nonlinear_pressure_force, geometric_bed_slope


def fixture(state, bed, dx, periodic, fraction_kind, *, second_order=True, shoreline_limiter='binary'):
    original = np.asarray(state,dtype=float)
    state = original.astype(np.float32).astype(float)
    bed = np.asarray(bed,dtype=np.float32).astype(float)
    h = state[...,0]
    captured = []
    saved = bank.nonlinear_pressure_force
    def capture(*args,**kwargs):
        captured.append([p.copy() for p in args[4]])
        return np.zeros_like(args[2]),[dict(relative_residual=0.,iterations=0)]
    try:
        bank.nonlinear_pressure_force = capture
        hydro,cfl = bank.rate(state,bed,dx,second_order=second_order,periodic=periodic,dispersive=True,
            pressure_model='rational_sgn',pressure_interpolation='depth_weighted',
            pressure_formulation='kinematic',pressure_bed_slope='geometry',shoreline_limiter=shoreline_limiter)
    finally:
        bank.nonlinear_pressure_force = saved
    hydro = hydro.astype(np.float32).astype(float)
    pairs = captured[0]
    slope = geometric_bed_slope(bed,dx,periodic).astype(np.float32).astype(float)
    fraction = np.ones_like(h)
    if fraction_kind == 'zero': fraction[:] = 0
    elif fraction_kind == 'mixed':
        y,x = np.indices(h.shape); fraction = np.array([0.,.35,1.])[(x//4+y//3)%3]
    elif fraction_kind == 'front': fraction,_ = dispersion_fraction(h,bed,hydro[...,0],pairs,dx)
    fraction = fraction.astype(np.float32).astype(float)
    velocity = np.divide(state[...,1:],h[...,None],out=np.zeros_like(state[...,1:]),where=h[...,None]>0)
    poles = []
    force,stats = nonlinear_pressure_force(h,bed,velocity,np.zeros_like(velocity),pairs,dx,
        interpolation='depth_weighted',formulation='kinematic',mass_rate=hydro[...,0],momentum_rate=hydro[...,1:],
        bed_slope=slope,dispersion_fraction=fraction,on_pressure=poles.extend)
    arrays = [np.stack((h,bed),axis=-1), np.concatenate((state,np.zeros((*h.shape,1))),axis=-1),
        np.concatenate((hydro,np.zeros((*h.shape,1))),axis=-1),slope,fraction,
        pairs[0].astype(np.uint32)+2*pairs[1].astype(np.uint32),
        np.concatenate([p['rhs'] for p in poles],axis=-1),
        np.concatenate([p['correction'] for p in poles],axis=-1),
        np.stack([v for p in poles for v in (p['pressure'],p['bottom_pressure'])],axis=-1),force]
    metadata = dict(shape=list(h.shape),cell_m=dx,periodic=periodic,fraction_kind=fraction_kind,
        second_order=second_order,shoreline_limiter=shoreline_limiter,cfl_bound_s=float(cfl) if np.isfinite(cfl) else None,
        positive_depths_rounded_to_zero=int(np.count_nonzero((original[...,0]>0)&(h==0))),
        depth_quantization_max_m=float(abs(h-original[...,0]).max()),
        momentum_quantization_max=float(abs(state[...,1:]-original[...,1:]).max()),
        reference_solver=stats,force_max=float(abs(force).max()))
    return arrays,metadata


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--snapshot',type=Path)
    args = parser.parse_args()
    manifest_path = args.output.with_suffix('.json')
    if args.output.exists() or manifest_path.exists(): raise FileExistsError(args.output)
    cases = []; metadata = []
    for kind in ('lake','closed','periodic','mixed','zero','minimum_subnormal','subnormal','minimum_normal'):
        y,x = np.indices((13,17)); bed=.08*np.sin(x*.2)*np.cos(y*.3)
        h=.9+.2*np.sin(x*.23)+.1*np.cos(y*.31)
        u=.4*np.sin(x*.31)+1.; v=.3*np.cos(y*.19)
        if kind == 'lake': h[:]=1.; bed[:]=0.; u[:]=0.; v[:]=0.
        if kind in ('mixed','zero'):
            h[5,5]=0.;h[6,7]=1e-20
        if kind in ('minimum_subnormal','subnormal','minimum_normal'):
            h[6,7]={'minimum_subnormal':2.**-149,'subnormal':2.**-130,'minimum_normal':2.**-126}[kind]
        state = np.stack((h,h*u,h*v),axis=-1)
        arrays,meta = fixture(state,bed,.5,kind=='periodic',kind)
        cases.append(arrays);metadata.append(dict(name=kind,**meta))
    hashes = {}
    if args.snapshot:
        meta,arrays,hashes = read_snapshot(args.snapshot)
        flow,detail = arrays['flow'].astype(float),arrays['state'].astype(float)
        h=flow[...,0]+detail[...,0]
        state=np.concatenate((h[...,None],h[...,None]*flow[...,1:3]+detail[...,1:3]),axis=-1)
        for kind in ('nonbreaking','front'):
            fields,record=fixture(state,arrays['mean_geometry'][...,0],meta['cell_m'],False,kind)
            cases.append(fields);metadata.append(dict(name='captured_'+kind,**record))
    with args.output.open('xb') as out:
        out.write(struct.pack('<III',0x52535046,1,len(cases)))
        for fields,meta in zip(cases,metadata):
            ny,nx=meta['shape'];out.write(struct.pack('<IIIf',nx,ny,int(meta['periodic']),meta['cell_m']))
            for index,field in enumerate(fields):
                if not np.all(np.isfinite(field)): raise ValueError('Nonfinite reference fixture')
                converted=np.asarray(field,dtype='<u4' if index==5 else '<f4')
                if not np.all(np.isfinite(converted)): raise ValueError('Float32 reference output overflow')
                out.write(converted.tobytes(order='C'))
    manifest = dict(schema='raftsim.nonlinear_pressure_fixtures.v1',scope=__doc__,scene_accepted=False,
        fixture_sha256=hashlib.sha256(args.output.read_bytes()).hexdigest(),source_hashes=hashes,cases=metadata,
        implementation_hashes={name:hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
            for name in ('export_nonlinear_pressure_fixtures.py','total_depth_bank_replay.py','adaptive_hydrostatic_precision.py','total_depth_nonlinear_pressure.py','pressure_cg_range_reference.py','breaking_front_reference.py')})
    with manifest_path.open('x') as out: json.dump(manifest,out,indent=2,allow_nan=False)
    print(json.dumps(manifest,indent=2))


if __name__ == '__main__': main()
