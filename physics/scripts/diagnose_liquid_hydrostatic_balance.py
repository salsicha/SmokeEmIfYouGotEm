"""Still-water pressure regression, not a simulated or accepted South Fork scene.

This isolates the installed collocated pressure operator's empty-cell-centre
condition from its proposed subcell ghost-fluid replacement. The exact planar
interface is authored test geometry; it is NOT substituted for river motion.
"""
import argparse
import json
from pathlib import Path
import numpy as np
from liquid_compatible_projection import project,constrain_velocity,shift


def lake(stage=225.,spacing=(50.,50.,800/24),shape=(16,10,32),dt=1/60,gravity=980.):
    h=np.asarray(spacing,dtype=float)
    z=(np.arange(shape[0])+.5)*h[2]-2*h[2]
    phi=np.broadcast_to((z-stage)[:,None,None],shape).copy()
    b=np.zeros((*shape,4));b[...,3]=np.where(phi<0,0,2)
    # Two complete halo layers for the centred +/-2 pressure dependencies.
    b[:,:2,:,3]=b[:,-2:,:,3]=1
    b[:,2:-2,:2,3]=b[:,2:-2,-2:,3]=3
    b[z<=0,...,3]=1
    pressure=np.where(b[...,3]==3,gravity*np.maximum(-phi,0),0)
    v=np.zeros((*shape,3));v[...,2]=-gravity*dt
    return v,b,phi,pressure


def compare(stage=225.,spacing=(50.,50.,800/24)):
    dt=1/60;v,b,phi,known=lake(stage,spacing)
    fluid=b[...,3]==0
    _,mobility,_=constrain_velocity(v,b)
    support=np.stack([shift(fluid,-1,2-c)|shift(fluid,1,2-c) for c in range(3)],axis=-1)
    supported= support & (mobility>0)
    results={}
    for name,interface in [('cell_centre',None),('subcell_interface',phi)]:
        velocity,p,solve=project(v,b,spacing=spacing,dt=dt,boundary_pressure=known,
            free_surface_phi=interface,max_iterations=1800,tolerance=1e-11)
        results[name]=dict(solve=solve,
            max_supported_speed_component_cm_s=float(abs(velocity[supported]).max()),
            max_horizontal_speed_cm_s=float(abs(velocity[...,:2][supported[...,:2]]).max()),
            max_hydrostatic_pressure_error_cm2_s2=float(abs(p-980*np.maximum(-phi,0))[fluid].max()),
            pressure_head_error_quantiles_cm=np.quantile((p/980+phi)[fluid],[0,.1,.5,.9,1]).tolist())
    return dict(schema='raftsim.liquid_hydrostatic_pressure_diagnosis.v1',
        stage_cm=stage,spacing_cm=list(spacing),requested_step_seconds=dt,
        cases=results,authored_planar_interface=True,native_solver_modified=False,
        river_drainage_cause_verified=False,physical_river_or_visual_acceptance=False)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',required=True,type=Path)
    a=p.parse_args()
    if a.output.exists():raise FileExistsError(a.output)
    r=compare();a.output.write_text(json.dumps(r,indent=2,allow_nan=False)+'\n')
    print(json.dumps(r,indent=2))
