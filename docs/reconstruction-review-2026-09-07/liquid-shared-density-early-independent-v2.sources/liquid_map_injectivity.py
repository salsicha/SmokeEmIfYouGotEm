"""Conservative global no-fold bound for the continuous compact correction map.

Extend the finite displacement grid by zero, as an explicit mathematical map
extension (not a fluid boundary condition). In cell coordinates u=delta/h,
normal derivatives are tent-weighted centered differences of u. Transverse
derivatives are convex-weighted adjacent differences. Bounding each derivative
by the largest corresponding grid difference bounds the infinity-norm Lipschitz
constant L. If L<1, ||F(x)-F(y)||inf >= (1-L)||x-y||inf, so F is injective.

This does NOT prove float32 rounded particle positions unique, conservation of
geometric volume, terrain adherence, or a physical exterior boundary condition.
"""
import numpy as np


def compact_map_bound(delta,spacing):
    d=np.asarray(delta,float);h=np.asarray(spacing,float)
    if (d.ndim!=4 or d.shape[-1]!=3 or min(d.shape[:3])<4 or h.shape!=(3,) or
            not np.isfinite(d).all() or not np.isfinite(h).all() or (h<=0).any()):
        raise ValueError('Finite compact XYZ displacement grid and positive metric required')
    with np.errstate(over='ignore',invalid='ignore'):u=d/h
    if not np.isfinite(u).all():raise ValueError('Cell-metric displacement overflow')
    bounds=np.zeros((3,3))
    for component in range(3):
        for axis in range(3):
            array_axis=2-axis;pad=[(0,0)]*3;pad[array_axis]=(1,1)
            padded=np.pad(u[...,component],pad)
            if axis==component:
                a=[slice(None)]*3;b=a.copy();a[array_axis]=slice(2,None);b[array_axis]=slice(None,-2)
                # Include the derivative at nodes just outside the finite grid.
                padded=np.pad(padded,pad)
                differences=(padded[tuple(a)]-padded[tuple(b)])*.5
            else:differences=np.diff(padded,axis=array_axis)
            bounds[component,axis]=float(abs(differences).max(initial=0))
    lipschitz=float(bounds.sum(axis=1).max())
    # Reserve roundoff headroom in the certificate, rather than accepting an
    # almost-one rounded bound. This is arithmetic guard, not a physical limit.
    guard=64*np.finfo(float).eps*max(1.,lipschitz)
    certified=lipschitz+guard<1
    return dict(derivative_absolute_bounds_cell_metric=bounds.tolist(),lipschitz_upper_bound=lipschitz,
        floating_point_guard=guard,continuous_map_globally_injective=bool(certified),
        minimum_cell_metric_separation_factor=max(0.,1-lipschitz-guard) if certified else None,
        extension='zero displacement outside finite grid; not a physical fluid boundary condition',
        native_quantized_injectivity_proven=False,volume_preservation_proven=False)
