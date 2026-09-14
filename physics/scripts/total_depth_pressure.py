"""Finite-depth pressure correction on an evolving hydrostatic wet graph.

Research component, not a full nonlinear Green-Naghdi/DtN operator. It retains
the existing two-Helmholtz rational response and 40-iteration budget. The graph
uses positive submerged face depths, not an imposed minimum film. Solve for
psi-surface directly so rest states and vertical datums do not cancel tiny waves.
"""
import numpy as np
from finite_depth_pressure_reference import LENGTHS, WEIGHTS


def wet_pairs(depth, bed, periodic=False):
    pairs = []
    for axis in (1, 0):
        other_h = np.roll(depth, -1, axis)
        jump = np.roll(bed, -1, axis)-bed
        pair = (depth-np.maximum(jump, 0) > 0) & (other_h-np.maximum(-jump, 0) > 0)
        if depth.shape[axis] == 1:
            pair[:] = False  # A periodic self-edge contributes no Laplacian.
        if not periodic:
            edge = [slice(None), slice(None)]; edge[axis] = -1
            pair[tuple(edge)] = False
        pairs.append(pair)
    return pairs


def pressure_correction(depth, bed, cell_m, iterations=40, periodic=False, pairs=None):
    depth, bed = np.asarray(depth, dtype=float), np.asarray(bed, dtype=float)
    if (depth.ndim != 2 or depth.shape != bed.shape or not depth.size
            or not np.all(np.isfinite(depth)) or np.any(depth < 0)
            or not np.all(np.isfinite(bed)) or not np.isfinite(cell_m) or cell_m <= 0
            or not isinstance(iterations, int) or not 1 <= iterations <= 128):
        raise ValueError('Invalid finite-depth pressure input')
    if pairs is None:
        pairs = wet_pairs(depth, bed, periodic)
    elif len(pairs) != 2 or any(np.shape(p) != depth.shape or np.asarray(p).dtype != bool for p in pairs):
        raise ValueError('Invalid pressure wet graph')
    for axis, pair in zip((1, 0), pairs):
        if np.any(pair & ((depth <= 0) | (np.roll(depth, -1, axis) <= 0))):
            raise ValueError('Pressure edge touches a dry cell')
        if (depth.shape[axis] == 1 and np.any(pair)) or (not periodic and np.any(np.take(pair, [-1], axis=axis))):
            raise ValueError('Pressure edge leaves the physical domain')
    degree = np.zeros_like(depth)
    surface_laplacian = np.zeros_like(depth)
    for axis, pair in zip((1, 0), pairs):
        backward = np.roll(pair, 1, axis)
        degree += pair.astype(float)+backward
        # Take component differences before adding to preserve tiny surface
        # differences and exactly cancel representable lake-at-rest states.
        delta = (np.roll(depth, -1, axis)-depth)+(np.roll(bed, -1, axis)-bed)
        surface_laplacian += pair*delta-backward*np.roll(delta, 1, axis)
    alpha = LENGTHS[:, None, None]*(depth/cell_m)**2
    diagonal = 1+alpha*degree
    rhs = alpha*surface_laplacian
    previous, older = np.zeros_like(alpha), np.zeros_like(alpha)
    # Actual row off-diagonal/diagonal bound, including disconnected and 1-D
    # graphs. A four-neighbor bound needlessly slows the same 40 iterations.
    c = np.max(alpha*degree/diagonal, axis=(1, 2))
    rho = c.copy()
    for iteration in range(iterations):
        total = np.zeros_like(previous)
        for axis, pair in zip((1, 0), pairs):
            total += pair*np.roll(previous, -1, axis+1)
            total += np.roll(pair, 1, axis)*np.roll(previous, 1, axis+1)
        jacobi = (rhs+alpha*total)/diagonal
        relaxation, momentum = np.ones(2), np.zeros(2)
        if iteration:
            next_rho = np.divide(c, 2-rho*c, out=np.zeros_like(c), where=c > 0)
            relaxation = np.divide(2*next_rho, c, out=np.ones_like(c), where=c > 0)
            momentum, rho = next_rho*rho, next_rho
        current = previous+relaxation[:, None, None]*(jacobi-previous)
        current += momentum[:, None, None]*(previous-older)
        older, previous = previous, current
    return np.sum(WEIGHTS[:, None, None]*previous, axis=0), pairs
