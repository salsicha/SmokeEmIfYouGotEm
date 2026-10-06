"""Independent interface-motion/velocity consistency, not a foam solve.

At phi=0 a material free surface requires dphi/dt + u.grad(phi)=0.
Use two actual central-time stencils and report their disagreement; do not
change velocity, retime geometry or extrapolate a fitted residual away.
"""
import numpy as np


def kinematic_condition(phi_minus2, phi_minus1, phi_zero, phi_plus1, phi_plus2,
                        dt, gradient, velocity, zero_tolerance_m=1e-10):
    phi = np.asarray([phi_minus2, phi_minus1, phi_zero, phi_plus1, phi_plus2], float)
    g, u = np.asarray(gradient, float), np.asarray(velocity, float)
    if (phi.shape != (5,) or not np.isfinite(phi).all() or g.shape != (3,)
            or u.shape != (3,) or not np.isfinite(g).all() or not np.isfinite(u).all()
            or not np.isfinite(dt) or dt <= 0 or not np.isfinite(zero_tolerance_m)
            or zero_tolerance_m <= 0):
        raise ValueError('Five finite timed distances, positive interval and matched 3D vectors required')
    length = float(np.linalg.norm(g))
    if length < 1e-12 or abs(phi_zero) > zero_tolerance_m:
        raise ValueError('A supported actual interface point and resolved gradient are required')
    normal = g/length
    fine_rate = float((phi[3]-phi[1])/(2*dt))
    coarse_rate = float((phi[4]-phi[0])/(4*dt))
    normal_velocity = float(u @ normal)
    fine_required, coarse_required = -fine_rate/length, -coarse_rate/length
    return dict(velocity_normal_mps=normal_velocity,
        required_surface_normal_velocity_mps=fine_required,
        coarse_required_surface_normal_velocity_mps=coarse_required,
        signed_normal_mismatch_mps=normal_velocity-fine_required,
        coarse_signed_normal_mismatch_mps=normal_velocity-coarse_required,
        temporal_stencil_disagreement_mps=abs(fine_required-coarse_required),
        phi_time_rate_mps=fine_rate, coarse_phi_time_rate_mps=coarse_rate,
        normal=normal.tolist(), dt_seconds=float(dt), accepted=False,
        scope='Local finite-time kinematic consistency only; no temporal interpolation, velocity correction, marker transport or physical foam acceptance.')
