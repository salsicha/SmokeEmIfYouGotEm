"""Reference-condition capillary migration, not a calibrated water-foam model.

Patel & Zhu 2026, doi:10.1017/jfm.2025.11003, equations 4.2/4.4,
section 4.1 (Bo=1, Mo=1e-4) and Appendix E (Cd=2 at Bo=1).
Original implementation. Stops before near-contact/shape-deformation physics.
"""
import argparse
import json
import math
from pathlib import Path
import numpy as np
from surface_bubble_shape import bessel_k
from solve_surface_bubble_equilibrium import solve


def physical_inputs(model):
    if abs(model['bond']-1.)>1e-6:
        raise ValueError('Cd=2 is documented for Bo=1; do not transfer silently')
    rho,sigma,g=model['density_kg_m3'],model['tension_N_m'],model['gravity_m_s2']
    return dict(morton=1e-4,drag_coefficient=2.,
                viscosity_Pa_s=(1e-4*rho*sigma**3/g)**.25,
                viscosity_ratio=100., ordinary_water=False)


def migration_rate(distance,model,inputs):
    radius=model['gas_radius_m']
    if distance<2.5*radius:
        raise ValueError('Near-contact migration outside this validation interval')
    rim,cap,length=model['rim_radius_m'],model['cap_curvature_radius_m'],model['capillary_length_m']
    slope=rim/math.sqrt(cap*cap-rim*rim)*float(bessel_k(1,distance/length)/bessel_k(1,rim/length))
    return -model['tension_N_m']*rim*rim/(inputs['viscosity_Pa_s']*inputs['drag_coefficient']*radius*cap)*slope


def trajectory(model,inputs,substeps=4,seconds=3.,fps=24,initial_gap_radii=1.6):
    radius=model['gas_radius_m']
    distance=(2+initial_gap_radii)*radius
    dt=1/(fps*substeps)
    rows=[]
    count=round(seconds*fps)
    for frame in range(count+1):
        speed=-migration_rate(distance,model,inputs)/2
        reynolds=model['density_kg_m3']*speed*2*radius/inputs['viscosity_Pa_s']
        rows.append(dict(frame=frame+1,seconds=frame/fps,distance_m=distance,
                         centers_xy_m=[[-distance/2,0.],[distance/2,0.]],
                         single_bubble_speed_mps=speed,reynolds_diameter=reynolds,
                         capillary_number=speed*inputs['viscosity_Pa_s']/model['tension_N_m']))
        if frame==count:
            break
        for _ in range(substeps):
            f=lambda d:migration_rate(d,model,inputs)
            a=f(distance); b=f(distance+dt*a/2); c=f(distance+dt*b/2); d=f(distance+dt*c)
            distance+=dt*(a+2*b+2*c+d)/6
    return rows


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    radius=math.sqrt(.072/(4*998.*9.80665))
    coarse=solve(radius=radius,steps=512)
    equilibrium=solve(radius=radius,steps=1024,initial=coarse['parameters_log'])
    model=equilibrium['model']
    inputs=physical_inputs(model)
    # End the study before the excluded near-contact regime, without slowing
    # the model or clamping/overlapping bubbles to force a three-second clip.
    nodes,weights=np.polynomial.legendre.leggauss(128)
    initial_distance,stop_distance=3.6*radius,2.6*radius
    distances=(initial_distance+stop_distance)/2+(initial_distance-stop_distance)/2*nodes
    time_to_stop=(initial_distance-stop_distance)/2*sum(w/(-migration_rate(d,model,inputs)) for w,d in zip(weights,distances))
    seconds=math.floor(time_to_stop*24)/24
    rows=trajectory(model,inputs,seconds=seconds)
    fine=trajectory(model,inputs,substeps=8,seconds=seconds)
    error=max(abs(a['distance_m']-b['distance_m']) for a,b in zip(rows,fine))
    if error>1e-8:
        raise RuntimeError('Pair timestep difference exceeds 10 nm')
    if max(r['reynolds_diameter'] for r in rows)>=1:
        raise RuntimeError('Reference migration leaves the Stokes regime')
    # Same radii and drag, but water-like viscosity: expose invalid transfer.
    water_inputs=dict(inputs,viscosity_Pa_s=.001)
    water_re=[]
    for row in rows:
        velocity=-migration_rate(row['distance_m'],model,water_inputs)/2
        water_re.append(model['density_kg_m3']*velocity*2*radius/.001)
    initial_d,final_d=rows[0]['distance_m'],rows[-1]['distance_m']
    dd=(initial_d+final_d)/2+(initial_d-final_d)/2*nodes
    quadrature_time=(initial_d-final_d)/2*sum(w/(-migration_rate(d,model,inputs)) for w,d in zip(weights,dd))
    if abs(quadrature_time-seconds)>1e-6:
        raise RuntimeError('Separated-variable time integral differs from trajectory')
    report=dict(equilibrium=equilibrium,inputs=inputs,frames=fine,fps=24,
                maximum_timestep_difference_m=error,
                independently_integrated_duration_s=quadrature_time,
                ordinary_water_reynolds_range=[min(water_re),max(water_re)],
                physical_accuracy_accepted=False,visual_accuracy_accepted=False,
                scope='Calibrated reduced-model reference-condition study, not measured water foam. Axisymmetric isolated shapes, linear superposition and fitted pair drag; no near-contact deformation, drainage or rupture.')
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2))
    print('PAIR_MIGRATION',json.dumps(dict(radius_m=radius,inputs=inputs,
         initial=rows[0],final=rows[-1],timestep_error_m=error,
         time_integral_s=quadrature_time,water_reynolds_range=report['ordinary_water_reynolds_range'])),flush=True)


if __name__=='__main__':
    main()
