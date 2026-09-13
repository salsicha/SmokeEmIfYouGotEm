"""Metric RK2 semi-Lagrangian transport of an explicit liquid interface.

The scalar is carried, not regenerated from particle density. A supplied update
box separates owned cells from halo/boundary values owned by the caller. Bad
traces retain their input scalar and are flagged; they are NOT successful steps.
This is an operator reference, not yet a coupled native river solver.
"""
import numpy as np
from liquid_volume_interface import sample_centred
from liquid_compatible_advection import sample_compact


def advect(phi, velocity, spacing, dt, minimum, maximum, compact=False, *, details=False):
    phi, velocity, spacing = np.asarray(phi, float), np.asarray(velocity, float), np.asarray(spacing, float)
    minimum, maximum = np.asarray(minimum), np.asarray(maximum)
    if (phi.ndim != 3 or velocity.shape != (*phi.shape, 3) or not np.isfinite(phi).all() or
            not np.isfinite(velocity).all() or spacing.shape != (3,) or not np.isfinite(spacing).all() or
            (spacing <= 0).any() or not np.isfinite(dt) or dt < 0 or minimum.shape != (3,) or maximum.shape != (3,) or
            not np.issubdtype(minimum.dtype, np.integer) or not np.issubdtype(maximum.dtype, np.integer) or
            (minimum < 0).any() or (maximum > phi.shape[::-1]).any() or (minimum >= maximum).any()):
        raise ValueError('Finite matching scalar/velocity, metric, timestep and half-open update box required')
    output = phi.copy()
    z, y, x = np.meshgrid(np.arange(minimum[2], maximum[2]), np.arange(minimum[1], maximum[1]),
                         np.arange(minimum[0], maximum[0]), indexing='ij')
    indices = np.column_stack((x.ravel(), y.ravel(), z.ravel()))
    points = (indices+.5)*spacing
    def sample_flow(query):
        if compact:
            lo=np.floor(query/spacing-.5).astype(int)-1
            valid=((lo>=0)&(lo+3<phi.shape[::-1])).all(axis=1)
            values=np.full_like(query,np.nan)
            values[valid]=sample_compact(query[valid],velocity.transpose(2,1,0,3),spacing)
            return values,valid
        values=[];valid=np.ones(len(query),bool)
        for c in range(3):
            value,complete=sample_centred(velocity[...,c],query,spacing)
            values.append(value);valid&=complete
        return np.column_stack(values),valid
    valid=np.ones(len(points),bool)
    at_start = velocity[z, y, x].reshape(-1, 3)
    if compact:at_start,valid=sample_flow(points)
    midpoint = points-.5*dt*np.nan_to_num(at_start)
    mid_velocity,complete=sample_flow(midpoint)
    valid &= complete
    # Do not pass nonfinite invalid samples into the sampling routine.
    traced = points-dt*np.nan_to_num(mid_velocity)
    transported, complete = sample_centred(phi, traced, spacing)
    valid &= complete
    destination = indices[valid]
    output[destination[:, 2], destination[:, 1], destination[:, 0]] = transported[valid]
    report=dict(updated_cells=int(valid.sum()), rejected_trace_cells=int((~valid).sum()),
                        candidate_step_valid=bool(valid.all()),
                        max_valid_trace_distance_cells=float(np.linalg.norm((traced[valid]-points[valid])/spacing, axis=1).max()) if valid.any() else None,
                        max_midpoint_trace_distance_cells=float(np.max(np.linalg.norm((midpoint-points)/spacing, axis=1), initial=0)))
    if details:report.update(indices=indices,traced_points=traced,valid_mask=valid)
    return output,report
