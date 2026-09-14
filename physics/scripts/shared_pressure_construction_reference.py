"""Isolated exact reuse of W/V within one unchanged pressure geometry.

Pole length and dispersion fraction do not enter W/V. They DO enter the
preconditioner: replay its original scalar accumulation order for each pole.
No across-stage geometry freeze, precision change or production installation.
"""
from contextlib import contextmanager
import hashlib
import numpy as np


def immutable_geometry_key(geometry):
    """Require read-only arrays and rehash their actual bits on every use."""
    arrays = [geometry.h, geometry.bed]
    metadata = [geometry.pressure_trace, geometry.bed_quadrature,
                repr(geometry.dx), repr(geometry.periodic)]
    for edge in geometry.edges:
        for name in sorted(edge):
            metadata.append(name); arrays.append(edge[name])
    result = hashlib.sha256(repr(metadata).encode('ascii'))
    for value in arrays:
        if not isinstance(value, np.ndarray) or value.flags.writeable or value.dtype.hasobject:
            return None
        result.update(repr((value.dtype.str, value.shape)).encode('ascii'))
        result.update(value.tobytes())
    return result.digest()


def replay_preconditioner(system):
    """Original row/column insertion order, Python coefficient scalar arithmetic."""
    diagonal = np.ones((*system.h.shape, 2)).ravel()
    off = np.zeros(system.h.size)
    grouped = {}; previous_row = None; factor = 0.
    def finish_row():
        for column, (w, v) in grouped.items():
            if column % 2 == 0 and column+1 in grouped:
                other_w, other_v = grouped[column+1]
                off[column//2] += factor*(w*other_w+.75*v*other_v)
    for row, column, w, v in zip(system.rows, system.columns,
                                 system.w_coefficients, system.v_coefficients):
        row, column, w, v = int(row), int(column), float(w), float(v)
        if row != previous_row:
            finish_row(); grouped = {}; previous_row = row
        factor = system.length*system.fraction.ravel()[row]
        diagonal[column] += factor*(w*w+.75*v*v)
        grouped[column] = w, v
    finish_row()
    system.diagonal = diagonal.reshape(*system.h.shape, 2)
    system.off_diagonal = off.reshape(system.h.shape)
    if not np.isfinite(system.diagonal).all() or not np.isfinite(system.off_diagonal).all():
        raise ValueError('Acceleration preconditioner exceeds storage range')
    system.diagonal.flags.writeable = system.off_diagonal.flags.writeable = False


def coefficient_key(system):
    result = hashlib.sha256()
    for name in ('rows', 'columns', 'w_coefficients', 'v_coefficients'):
        value = getattr(system, name)
        if value.flags.writeable or value.dtype.hasobject: return None
        result.update(repr((value.dtype.str, value.shape)).encode('ascii'))
        result.update(value.tobytes())
    return result.digest()


@contextmanager
def shared_pressure_coefficients(metrics=None):
    """Bounded one-geometry cache in this process only; always restore binding."""
    import reconstructed_nonlinear_pressure as nonlinear
    original = nonlinear.ReconstructedAccelerationSystem
    counters = metrics if metrics is not None else {}
    counters.update(builds=0, reuses=0, uncacheable_builds=0)
    cached = None
    class Shared(original):
        def __init__(self, geometry, length, *, dispersion_fraction=None, project_zero_mass_rows=False):
            nonlocal cached
            # Preserve original validation order before any reuse path.
            if geometry.pressure_trace != 'integrated_column' or geometry.bed_quadrature != 'shared_bottom':
                raise ValueError('Requires integrated/shared-bottom research geometry')
            if not np.isfinite(length) or length <= 0:
                raise ValueError('Invalid pressure pole length')
            if type(project_zero_mass_rows) is not bool:
                raise ValueError('Invalid zero-mass projection mode')
            fraction = (np.ones_like(geometry.h) if dispersion_fraction is None
                        else np.array(dispersion_fraction, dtype=float, copy=True))
            if (fraction.shape != geometry.h.shape or not np.isfinite(fraction).all()
                    or np.any(fraction < 0) or np.any(fraction > 1)):
                raise ValueError('Invalid nonbreaking dispersion fraction')
            fraction.flags.writeable = False
            key = immutable_geometry_key(geometry)
            self.construction_reused = bool(key is not None and cached is not None
                and cached[0] is geometry and cached[1] == key and cached[2] == project_zero_mass_rows
                and coefficient_key(cached[3]) == cached[4])
            if not self.construction_reused:
                super().__init__(geometry, length, dispersion_fraction=dispersion_fraction,
                    project_zero_mass_rows=project_zero_mass_rows)
                counters['builds'] += 1
                if key is None: counters['uncacheable_builds'] += 1
                cached = (geometry, key, project_zero_mass_rows, self, coefficient_key(self)) if key is not None else None
                return
            self.geometry, self.h, self.length = geometry, geometry.h, float(length)
            self.fraction = fraction
            for name in ('rows', 'columns', 'w_coefficients', 'v_coefficients'):
                setattr(self, name, getattr(cached[3], name))
            replay_preconditioner(self)
            counters['reuses'] += 1
    nonlinear.ReconstructedAccelerationSystem = Shared
    try:
        yield counters
    finally:
        nonlinear.ReconstructedAccelerationSystem = original
