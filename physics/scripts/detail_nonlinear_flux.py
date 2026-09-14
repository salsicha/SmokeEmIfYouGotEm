"""Finite-amplitude relative-momentum reference, NOT the production solver.

Constant background H,U: eta=h-H; q=h*(u-U). Fluxes follow the full
Saint-Venant conservation laws by subtracting the background flux and U
times the mass equation. For a mean that owns its own acceleration/bed balance,
variable U additionally requires mean_strain_source. Subtracting fluxes alone
would leave an eta*U-gradient term that the mean acceleration balance cancels.
No finite-depth dispersion, overturning, wet/dry transition or foam closure
is supplied here. This is a verification reference for their integration.
"""
import numpy as np

G = 9.81


def relative_flux(state, depth, velocity, axis=0):
    state = np.asarray(state, dtype=float)
    velocity = np.asarray(velocity, dtype=float)
    h = np.asarray(depth) + state[..., 0]
    if (state.shape[-1] != 3 or velocity.shape[-1] != 2 or axis not in (0, 1)
            or not np.all(np.isfinite(state)) or not np.all(np.isfinite(h))
            or not np.all(np.isfinite(velocity)) or np.any(h <= 0)
            or np.any(np.asarray(depth) <= 0)):
        raise ValueError("Finite positive total and background depth required")
    eta, q = state[..., 0], state[..., 1:]
    result = np.empty_like(state)
    result[..., 0] = velocity[..., axis] * eta + q[..., axis]
    result[..., 1:] = velocity[..., axis, None] * q + q[..., axis, None] * q / h[..., None]
    result[..., axis + 1] += G * (depth * eta + .5 * eta * eta)
    return result


def mean_strain_source(state, gradient):
    """gradient[...,i,j]=d U_i/d x_j; required even in linearized variable flow."""
    return -np.einsum("...ij,...j->...i", gradient, state[..., 1:])


def signal_speed(state, depth, velocity, axis=0):
    h = depth + state[..., 0]
    if np.any(h <= 0) or not np.all(np.isfinite(h)):
        raise ValueError("Nonpositive/nonfinite total depth; never clip mass")
    return np.abs(velocity[axis] + state[..., axis + 1] / h) + np.sqrt(G * h)


def _rhs(state, depth, velocity, dx):
    left, right = state - np.roll(state, 1, axis=0), np.roll(state, -1, axis=0) - state
    slope = .5 * (np.sign(left) + np.sign(right)) * np.minimum(
        .5 * np.abs(left + right), 2 * np.minimum(np.abs(left), np.abs(right)))
    a, b = state + .5 * slope, np.roll(state - .5 * slope, -1, axis=0)
    speed = np.maximum(signal_speed(a, depth, velocity), signal_speed(b, depth, velocity))
    flux = .5 * (relative_flux(a, depth, velocity) + relative_flux(b, depth, velocity))
    flux -= .5 * speed[:, None] * (b - a)
    return -(flux - np.roll(flux, 1, axis=0)) / dx


def advance_periodic(state, depth, velocity, dx, seconds, max_step=1 / 120):
    """1-D constant-background MC/SSP-RK2 verification; not a river substitute.

    Reject a stage that loses positivity or its CFL bound, then retry the SAME
    physical interval with smaller internal steps. No height/momentum clipping.
    Production GPU integration must provide equivalent state-aware control.
    """
    state = np.asarray(state, dtype=float).copy()
    velocity = np.asarray(velocity, dtype=float)
    if not all(np.isfinite(v) for v in (dx, seconds, max_step)) or dx <= 0 or seconds < 0 or max_step <= 0:
        raise ValueError("Invalid integration interval")
    elapsed, steps, retries = 0., 0, 0
    while elapsed < seconds:
        dt = min(max_step, seconds - elapsed, .4 * dx / np.max(signal_speed(state, depth, velocity)))
        for attempt in range(40):
            try:
                stage = state + dt * _rhs(state, depth, velocity, dx)
                if dt * np.max(signal_speed(stage, depth, velocity)) / dx > .45:
                    raise ValueError("Stage CFL exceeded")
                candidate = .5 * (state + stage + dt * _rhs(stage, depth, velocity, dx))
                signal_speed(candidate, depth, velocity)
                if not np.all(np.isfinite(candidate)):
                    raise ValueError("Nonfinite state")
                break
            except ValueError:
                dt *= .5
                retries += 1
        else:
            raise RuntimeError("No admissible stage; do not advance the simulation clock")
        state = candidate
        elapsed += dt
        steps += 1
    return state, dict(elapsed_s=elapsed, steps=steps, rejected_stages=retries)


def simple_wave(x, seconds, depth=1.5, amplitude=.45, wavelength=40., current=.4):
    """Exact right-going nonlinear simple wave BEFORE characteristic crossing."""
    k, c0 = 2 * np.pi / wavelength, np.sqrt(G * depth)
    if depth <= abs(amplitude) or seconds < 0:
        raise ValueError("Invalid simple-wave state")
    # A sufficient global pre-crossing bound: min dx/dxi > 0.
    bound = 1.5 * np.sqrt(G) * abs(amplitude) * k / np.sqrt(depth - abs(amplitude))
    if seconds * bound >= 1:
        raise ValueError("Characteristic map may fold; this is not a post-breaking solution")
    x = np.asarray(x, dtype=float)
    xi = x - (current + c0) * seconds
    for _ in range(20):
        h = depth + amplitude * np.sin(k * xi)
        speed = current + 3 * np.sqrt(G * h) - 2 * c0
        derivative = 1 + seconds * 1.5 * np.sqrt(G) * amplitude * k * np.cos(k * xi) / np.sqrt(h)
        xi -= (xi + speed * seconds - x) / derivative
    h = depth + amplitude * np.sin(k * xi)
    q = h * 2 * (np.sqrt(G * h) - c0)
    return np.stack((h - depth, q, np.zeros_like(q)), axis=-1)
