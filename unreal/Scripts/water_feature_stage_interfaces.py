"""Explicit column-wise zero crossings, not mesh normals or material speed.

Ambiguous/absent/obstacle crossings are reported, never filled or projected.
"""
import numpy as np


def column_interface(phi, flags, column, spacing):
    phi, flags = np.asarray(phi), np.asarray(flags)
    if (phi.ndim != 3 or min(phi.shape) < 7 or flags.shape != phi.shape
            or not np.issubdtype(flags.dtype, np.integer) or not np.isfinite(phi).all()
            or len(column) != 2 or any(isinstance(c, bool) or not isinstance(c, (int, np.integer)) for c in column)
            or not all(1 <= c < phi.shape[a]-1 for a,c in enumerate(column))
            or not np.isfinite(spacing) or spacing <= 0):
        raise ValueError('Need finite matching fields and an interior integer column')
    x,y = column
    crossings, obstacle_crossings = [], 0
    for k in range(2, phi.shape[2]-3):
        a,b = float(phi[x,y,k]), float(phi[x,y,k+1])
        if a < 0 <= b:
            if int(flags[x,y,k] | flags[x,y,k+1]) & 2:
                obstacle_crossings += 1
                continue
            t = -a/(b-a)
            crossings.append(dict(lower_cell=k, fraction=t,
                relative_height_m=(k+.5+t)*spacing, endpoint_phi_cells=[a,b]))
    return dict(status='supported' if len(crossings) == 1 else 'absent' if not crossings else 'ambiguous',
        crossings=crossings, obstacle_crossings=obstacle_crossings, accepted=False,
        scope='Vertical interpolated native base-phi zero; not rendered mesh distance, a normal or material velocity')


def stage_displacements(interfaces):
    if any(i['status'] != 'supported' for i in interfaces):
        return None
    if len(interfaces) != 4:
        raise ValueError('Need before, advected, joined and final interface samples')
    z = [i['crossings'][0]['relative_height_m'] for i in interfaces]
    return dict(advection_vertical_displacement_m=z[1]-z[0],
        join_minus_advection_vertical_displacement_m=z[2]-z[1],
        final_minus_advection_vertical_displacement_m=z[3]-z[1],
        final_minus_join_vertical_displacement_m=z[3]-z[2], accepted=False)
