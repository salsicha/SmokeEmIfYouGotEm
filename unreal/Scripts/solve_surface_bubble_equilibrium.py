"""Axisymmetric Young-Laplace floating bubble with fixed gas volume.

Original numerical implementation of Patel & Zhu (2026), Appendix B,
doi:10.1017/jfm.2025.11003. Massless noncoalescing film and negligible gas
density; no dynamic foam, film drainage, surfactant transport or rupture.
All integration uses R0 and sigma/R0 units. No scipy dependency.
"""
import argparse
import json
import math
from pathlib import Path
import numpy as np
from surface_bubble_shape import shape, bessel_k


def integrate(fun, start, stop, initial, steps):
    x = np.linspace(start, stop, steps+1)
    y = np.empty((steps+1, len(initial)))
    y[0] = initial
    h = (stop-start)/steps
    for i in range(steps):
        k1 = fun(x[i], y[i])
        k2 = fun(x[i]+h/2, y[i]+h*k1/2)
        k3 = fun(x[i]+h/2, y[i]+h*k2/2)
        k4 = fun(x[i]+h, y[i]+h*k3)
        y[i+1] = y[i]+h*(k1+2*k2+2*k3+k4)/6
        if not np.isfinite(y[i+1]).all() or np.max(np.abs(y[i+1])) > 1e5:
            raise ValueError('Unbounded shooting trajectory')
    return x, y


def shooting(parameters, q, steps, far_lengths):
    rb, tangent, amplitude = np.exp(parameters)
    alpha = math.atan(tangent)
    if not .8 < rb < 1.5 or not 0 < alpha < .8 or not 0 < amplitude < 2:
        raise ValueError('Outside small-bubble branch')
    eps = 1e-5
    def cavity(beta, y):
        r, z, _ = y
        denominator = r*(q*z+2/rb)-math.sin(beta)
        if denominator <= 0 or r <= 0:
            raise ValueError('Invalid cavity branch')
        dr = r*math.cos(beta)/denominator
        dz = r*math.sin(beta)/denominator
        return np.array([dr, dz, math.pi*r*r*dz])
    beta, cav = integrate(cavity,eps,math.pi-alpha,
                         [rb*eps,.5*rb*eps**2,math.pi*rb**3*eps**4/4],steps)
    rim, rim_z, cavity_volume = cav[-1]
    cap_radius = rim/math.sin(alpha)
    gas_pressure = 4/cap_radius
    flat_z = (gas_pressure-2/rb)/q
    height = rim**2/(cap_radius+math.sqrt(cap_radius**2-rim**2))
    volume = cavity_volume+math.pi*height**2*(cap_radius-height/3)
    length = 1/math.sqrt(q)
    far = far_lengths*length
    def exterior(x, y):
        r = math.exp(x)
        z, slope_log = y
        slope = slope_log/r
        return np.array([slope_log,q*r*r*z*(1+slope*slope)**1.5-slope_log**3/r**2])
    start = [amplitude*float(bessel_k(0,far_lengths)),
             -amplitude*far_lengths*float(bessel_k(1,far_lengths))]
    log_r, men = integrate(exterior,math.log(far),math.log(rim),start,steps)
    residual = np.array([men[-1,0]-(rim_z-flat_z),
                         men[-1,1]/rim+tangent, volume/(4*math.pi/3)-1])
    return residual, dict(rb=rb, alpha=alpha, amplitude=amplitude,
        beta=beta, cavity=cav, exterior_r=np.exp(log_r), exterior=men,
        rim=rim, rim_z=rim_z-flat_z, cap_radius=cap_radius,
        cap_height=height, flat_z=flat_z, volume=volume, gas_pressure=gas_pressure)


def solve(radius=.001, steps=512, far_lengths=12., initial=None):
    bond = 4*998.*9.80665*radius**2/.072
    if not 0 < bond <= 1.00000001:
        raise ValueError('Equilibrium branch currently checked only through Bo=1')
    # The analytical approximation is only an initial guess. At Bo > .6 use
    # a smaller-bubble dimensionless seed, never its geometry as the solution.
    seed_radius = min(radius, math.sqrt(.6*.072/(4*998.*9.80665)))
    approximate = shape(seed_radius)
    q = bond/4
    if initial is None:
        initial = np.log([1.02,approximate['rim_slope'],approximate['meniscus_amplitude_m']/seed_radius])
    parameters = np.array(initial)
    history = []
    for iteration in range(20):
        residual, solution = shooting(parameters,q,steps,far_lengths)
        norm = float(np.linalg.norm(residual))
        history.append(norm)
        if norm < 1e-10:
            break
        jac = np.empty((3,3))
        for j in range(3):
            shifted = parameters.copy()
            shifted[j] += 1e-5
            jac[:,j] = (shooting(shifted,q,steps,far_lengths)[0]-residual)/1e-5
        delta = np.linalg.solve(jac,-residual)
        for exponent in range(15):
            candidate = parameters+delta*2**(-exponent)
            try:
                new_norm = np.linalg.norm(shooting(candidate,q,steps,far_lengths)[0])
            except (ValueError, OverflowError):
                continue
            if new_norm < norm:
                parameters = candidate
                break
        else:
            raise RuntimeError(f'Shooting did not descend: {history}')
    else:
        raise RuntimeError(f'Shooting did not converge: {history}')
    # Independently estimate meridian curvature from sampled positions.
    beta, cav = solution['beta'],solution['cavity']
    r,z = cav[:,0],cav[:,1]
    dr,dz = np.gradient(r,beta),np.gradient(z,beta)
    ddr,ddz = np.gradient(dr,beta),np.gradient(dz,beta)
    speed = np.hypot(dr,dz)
    curvature = (dr*ddz-dz*ddr)/speed**3+dz/(r*speed)
    expected = solution['gas_pressure']+q*(z-solution['flat_z'])
    pressure_error = float(np.max(np.abs(curvature[8:-8]-expected[8:-8]))/solution['gas_pressure'])
    profile = np.column_stack((r*radius,(z-solution['flat_z'])*radius))
    profile = np.vstack(([0.,-solution['flat_z']*radius],profile))
    exterior = np.column_stack((solution['exterior_r']*radius,solution['exterior'][:,0]*radius))
    model = dict(gas_radius_m=radius, density_kg_m3=approximate['density_kg_m3'],
        tension_N_m=approximate['tension_N_m'],gravity_m_s2=approximate['gravity_m_s2'],
        bond=bond,rim_radius_m=solution['rim']*radius,
        rim_height_m=solution['rim_z']*radius,cap_curvature_radius_m=solution['cap_radius']*radius,
        cap_height_above_rim_m=solution['cap_height']*radius,
        capillary_length_m=approximate['capillary_length_m'],
        gas_volume_m3=solution['volume']*radius**3, nominal_gas_volume_m3=4*math.pi/3*radius**3,
        gas_pressure_Pa=solution['gas_pressure']*approximate['tension_N_m']/radius,
        cavity_bottom_z_m=-solution['flat_z']*radius,
        bottom_curvature_radius_m=solution['rb']*radius)
    return dict(model=model,cavity_profile_rz_m=profile.tolist(),exterior_profile_rz_m=exterior.tolist(),
        parameters_log=parameters.tolist(),iterations=history,steps_per_interface=steps,
        far_boundary_capillary_lengths=far_lengths,
        boundary_and_volume_residual=residual.tolist(),
        independent_fd_relative_pressure_residual=pressure_error,
        accepted=False,scope='Numerical isolated axisymmetric static equilibrium under massless-film and negligible-gas-density assumptions; not foam dynamics or measured optical validation.')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,required=True)
    args = p.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    coarse = solve()
    fine = solve(steps=1024,initial=coarse['parameters_log'])
    far = solve(steps=1024,far_lengths=16.,initial=fine['parameters_log'])
    compare_keys = ('rim_radius_m','rim_height_m','cap_curvature_radius_m','cavity_bottom_z_m')
    refinement = {key:abs(fine['model'][key]-coarse['model'][key]) for key in compare_keys}
    boundary = {key:abs(far['model'][key]-fine['model'][key]) for key in compare_keys}
    if max(refinement.values()) > 1e-8 or max(boundary.values()) > 1e-8:
        raise RuntimeError('Geometry changed by more than 10 nm on refinement/far-field extension')
    if fine['independent_fd_relative_pressure_residual'] > 1e-4:
        raise RuntimeError('Independent pressure residual exceeds 0.01%')
    report = dict(solution=fine,coarse=coarse,far_field_check=far,
                  refinement_difference_m=refinement,far_field_difference_m=boundary)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2))
    print('EQUILIBRIUM_RESULT',json.dumps(dict(model=fine['model'],
          refinement=refinement,far_field=boundary,
          pressure_residual=fine['independent_fd_relative_pressure_residual'],
          iterations=fine['iterations'])),flush=True)


if __name__ == '__main__':
    main()
