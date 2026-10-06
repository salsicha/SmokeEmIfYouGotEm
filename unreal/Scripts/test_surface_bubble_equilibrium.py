"""Independent profile residual/volume checks across three small bubble sizes."""
import argparse
import json
import math
from pathlib import Path
import numpy as np
from solve_surface_bubble_equilibrium import solve


def audit(solution):
    m=solution['model']
    cavity=np.array(solution['cavity_profile_rz_m'])
    exterior=np.array(solution['exterior_profile_rz_m'])[::-1]
    assert np.all(np.diff(cavity[:,1])>0)
    assert np.all(np.diff(exterior[:,0])>0)
    assert np.all(exterior[:,1]>0) and np.all(np.diff(exterior[:,1])<0)
    np.testing.assert_allclose(cavity[-1],exterior[0],atol=1e-11,rtol=0)
    height=m['cap_height_above_rim_m']
    # Quadrature directly on sampled coordinates, separate from ODE volume state.
    volume=math.pi*np.trapezoid(cavity[:,0]**2,cavity[:,1])+math.pi*height**2*(m['cap_curvature_radius_m']-height/3)
    volume_error=volume/m['nominal_gas_volume_m3']-1
    r,z=exterior.T
    # Differentiate the uniform log-radius sampling directly. Low-order
    # derivatives in r lose accuracy when the two principal curvatures nearly
    # cancel for small bubbles. These are independent position-only stencils.
    dx=np.diff(np.log(r))
    np.testing.assert_allclose(dx,dx[0],rtol=1e-10,atol=1e-14)
    h=dx[0]
    first=(z[:-4]-8*z[1:-3]+8*z[3:-1]-z[4:])/(12*h)
    second=(-z[:-4]+16*z[1:-3]-30*z[2:-2]+16*z[3:-1]-z[4:])/(12*h*h)
    rr=r[2:-2]
    curvature=(second+first**3/rr**2)/(rr**2*(1+first**2/rr**2)**1.5)
    pressure=m['density_kg_m3']*m['gravity_m_s2']/m['tension_N_m']*z[2:-2]
    residual=np.max(np.abs(curvature[6:-6]-pressure[6:-6]))/np.max(np.abs(pressure[6:-6]))
    assert abs(volume_error)<1e-5
    assert residual<.002
    assert solution['independent_fd_relative_pressure_residual']<1e-4
    return dict(radius_m=m['gas_radius_m'],bond=m['bond'],independent_volume_relative_error=volume_error,
                meniscus_fd_relative_curvature_error=float(residual),
                cavity_fd_relative_pressure_error=solution['independent_fd_relative_pressure_residual'])


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    rows=[audit(solve(radius=r,steps=1024)) for r in (.0005,.0007,.001)]
    args.output.write_text(json.dumps(dict(cases=rows,accepted=False,
        scope='Independent sampled-profile checks; not measured foam or optical calibration.'),indent=2))
    print('EQUILIBRIUM_TESTS',json.dumps(rows),flush=True)
