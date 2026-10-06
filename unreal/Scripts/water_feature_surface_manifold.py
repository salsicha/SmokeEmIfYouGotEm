"""Fresh surface-marker dynamics, not a renderer correction to cached foam.

Constraint/velocity-rotation component inspired by Wretborn et al. (2022),
sections 6.6--6.7: https://doi.org/10.1145/3528223.3530059.
No claim of their full SPH, bubble coupling, emission or bursting model.
"""
from dataclasses import dataclass
import numpy as np


@dataclass
class SurfaceState:
    positions: np.ndarray
    velocities: np.ndarray
    tangent_speed: np.ndarray


def tangent(vector, normal):
    return vector-np.sum(vector*normal, axis=1)[:, None]*normal


def values(surface, positions, time):
    phi, gradient = surface(positions, time)
    phi, gradient = np.asarray(phi, float), np.asarray(gradient, float)
    if (phi.shape != (len(positions),) or gradient.shape != positions.shape
            or not np.isfinite(phi).all() or not np.isfinite(gradient).all()):
        raise ValueError('Finite supported surface values and gradients required')
    length = np.linalg.norm(gradient, axis=1)
    if np.any(length < 1e-12):
        raise ValueError('Unresolved surface normal')
    return phi, gradient, gradient/length[:, None]


def initialize(positions, velocities, surface, time=0., tolerance=1e-10):
    positions, velocities = np.asarray(positions, float), np.asarray(velocities, float)
    if (positions.ndim != 2 or positions.shape[1] != 3 or len(positions) == 0 or velocities.shape != positions.shape
            or not np.isfinite(positions).all() or not np.isfinite(velocities).all()):
        raise ValueError('Finite matched 3D positions/velocities required')
    phi, _, normal = values(surface, positions, time)
    if np.any(np.abs(phi) > tolerance):
        raise ValueError('Fresh initial markers must already lie on the surface')
    return SurfaceState(positions.copy(), velocities.copy(), np.linalg.norm(tangent(velocities, normal), axis=1))


def step(state, surface, time, dt, acceleration=None, tolerance=1e-10,
         maximum_correction=.01, iterations=16):
    if (not all(np.isfinite(v) for v in (time, dt, tolerance, maximum_correction))
            or dt <= 0 or tolerance <= 0 or maximum_correction <= 0 or iterations < 1):
        raise ValueError('Positive bounded integration settings required')
    phi, gradient, normal = values(surface, state.positions, time)
    if np.any(np.abs(phi) > tolerance):
        raise ValueError('Initial surface constraint lost; no hidden reprojection')
    speed = np.asarray(state.tangent_speed, float)
    if speed.shape != phi.shape or not np.isfinite(speed).all() or np.any(speed < 0):
        raise ValueError('Finite nonnegative previous tangent speed required')
    velocity = tangent(state.velocities, normal)
    current_speed = np.linalg.norm(velocity, axis=1)
    if np.any((current_speed < 1e-14) & (speed > 1e-14)):
        raise ValueError('Tangent direction lost; reduce timestep, do not invent direction')
    scale = np.ones(len(speed))
    np.divide(speed, current_speed, out=scale, where=current_speed > 1e-14)
    velocity *= scale[:, None]
    acceleration = np.zeros_like(velocity) if acceleration is None else np.asarray(acceleration, float)
    if acceleration.shape != velocity.shape or not np.isfinite(acceleration).all():
        raise ValueError('Finite explicit acceleration required')
    velocity += dt*tangent(acceleration, normal)
    next_speed = np.linalg.norm(velocity, axis=1)
    predictor = state.positions+dt*velocity
    alpha = np.zeros(len(speed))
    converged = np.zeros(len(speed), bool)
    for count in range(iterations):
        candidate = predictor+alpha[:, None]*gradient
        residual, next_gradient, _ = values(surface, candidate, time+dt)
        converged |= np.abs(residual) <= tolerance
        if converged.all():
            break
        derivative = np.sum(next_gradient*gradient, axis=1)
        if np.any(np.abs(derivative[~converged]) < 1e-12):
            raise ValueError('Unresolved normal intersection; no surface tunneling fallback')
        alpha[~converged] -= residual[~converged]/derivative[~converged]
    else:
        raise ValueError('Surface constraint did not converge')
    correction = np.linalg.norm(candidate-predictor, axis=1)
    if np.any(correction > maximum_correction):
        raise ValueError('Surface motion exceeds declared correction bound')
    result = SurfaceState(candidate, (candidate-state.positions)/dt, next_speed)
    return result, dict(iterations=count+1, maximum_residual_m=float(np.max(np.abs(residual))),
                        maximum_correction_m=float(correction.max()),
                        count=len(candidate), accepted=False)
