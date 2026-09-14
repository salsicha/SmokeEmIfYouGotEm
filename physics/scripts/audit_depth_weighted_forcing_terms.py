"""Decompose raw Q/C failures on the unchanged original entering-ray fixture.

This intentionally uses the original test's endpoint arithmetic (no extra
cut-endpoint context). Physical two-pole force results are separate reports.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from reconstructed_pressure_geometry import ReconstructedPressureGeometry as Geometry
from reconstructed_pressure_rates import PressureGeometryRate
from directional_pressure_geometry import DirectionalPressureGeometry
from source_supported_scalar_boundary import SourceSupportedScalarBoundary
from depth_weighted_scalar_gradient import DepthWeightedSourceBoundary
from connected_depth_weighted_scalar_gradient import ConnectedDepthWeightedSourceBoundary


def terms(boundary, tangent, trace):
    g=boundary.original;u=boundary.velocity[boundary.core]
    q,c,adv=boundary.forcing(tangent,trace)
    d,e=g.kinematic_components(u);dt,et=tangent.kinematic_rate(u)
    lift=g.prescribed_divergence_lift(trace);d=d+lift[...,0];dt=dt+lift[...,1]
    ghost_d,ghost_e=boundary.exterior_kinematics(trace)
    da,ea=g.kinematic_components(adv)
    gd=np.sum(u*boundary.gradient(d,ghost_d),axis=-1)
    ge=np.sum(u*boundary.gradient(e,ghost_e),axis=-1)
    np.testing.assert_array_equal(q,d*d+da-dt-gd)
    np.testing.assert_array_equal(c,et+ge-ea)
    return dict(Q=q,C=c,Adv=adv,Q_d_squared=d*d,Q_D_adv=da,Q_minus_Dt=-dt,
        Q_minus_u_grad_D=-gd,C_Et=et,C_u_grad_E=ge,C_minus_E_adv=-ea)


def ray(implementation, flat):
    n=5;dx=1/n
    y,x=np.meshgrid((np.arange(n+6)-2.5)*dx,(np.arange(n+6)-2.5)*dx,indexing='ij')
    h=np.where(x<.25,0.,1.);bed=np.zeros_like(x) if flat else .125*np.maximum(x,0)+.0625*y
    state=np.stack((h,h*(.2+x),h*(.3+y)),axis=-1)
    rate=np.zeros_like(state);rate[...,0]=.125;rate[...,1]=.0625;rate[...,2]=-.03125
    core=(slice(3,-3),slice(3,-3));trace=np.zeros((20,2));wet=h[core]>0
    def evaluate(current, entering):
        g=Geometry(current[core][...,0],bed[core],dx,pressure_trace='integrated_column',bed_quadrature='shared_bottom')
        if entering:
            g=DirectionalPressureGeometry(g,rate[core][...,0]);tangent=g.tangent
        else:
            tangent=PressureGeometryRate(g,g.bed,rate[core][...,0])
        b=implementation(g,current[core],current,bed,**({'full_rate':rate} if entering else {}))
        return terms(b,tangent,trace)
    limit=evaluate(state,True);cases=[]
    for eps in (2.**-8,2.**-16,2.**-24):
        actual=evaluate(state+eps*rate,False);fields={}
        for name in actual:
            delta=actual[name]-limit[name]
            point=np.unravel_index(np.argmax(abs(delta)),delta.shape)
            fields[name]=dict(maximum_error=float(abs(delta).max()),
                originally_wet_maximum_error=float(abs(delta[wet]).max()),
                originally_dry_maximum_error=float(abs(delta[~wet]).max()),
                largest_error_index=list(map(int,point)))
        error=max(fields[name]['maximum_error'] for name in ('Q','C','Adv'))
        cases.append(dict(epsilon=eps,raw_test_error=error,fields=fields))
    return dict(implementation=implementation.__name__,flat=flat,cases=cases,
        original_absolute_gate_passed=cases[-1]['raw_test_error']<1e-6,
        original_reduction_gate_passed=cases[-1]['raw_test_error']<cases[0]['raw_test_error']/10000)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report',type=Path,required=True);args=parser.parse_args()
    if args.report.exists():raise FileExistsError(args.report)
    cases=[ray(implementation,flat)
        for implementation in (SourceSupportedScalarBoundary,DepthWeightedSourceBoundary,ConnectedDepthWeightedSourceBoundary)
        for flat in (True,False)]
    result=dict(scope=__doc__,cases=cases,original_assertions_unchanged=True,
        physical_force_or_energy_or_gameplay_accepted=False,
        implementation_hashes={name:hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
            for name in ('source_supported_scalar_boundary.py','depth_weighted_scalar_gradient.py',
                         'connected_depth_weighted_scalar_gradient.py','audit_depth_weighted_forcing_terms.py')})
    with args.report.open('x') as stream:json.dump(result,stream,indent=2,allow_nan=False)
    for case in cases:
        print(json.dumps(dict(implementation=case['implementation'],flat=case['flat'],
            errors=[c['raw_test_error'] for c in case['cases']],last=case['cases'][-1])),flush=True)


if __name__=='__main__':main()
