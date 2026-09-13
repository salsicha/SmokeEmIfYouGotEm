"""Position-level density projection and geometric solid kernel completion.

Adapted from Kugelstadt et al., TVCG 2019/2021, equations 10--12. This code
uses the project's centered D M G pair, not the paper's MAC Laplacian.
No particle mass is clipped/deleted and no momentum is added. Boundary density
is an integral over the actual solid under a height-field mesh, not an extra
liquid particle or an enlargement of the wet surface.
"""
import numpy as np
from liquid_compatible_projection import project,shift


def tent_cdf(r):
    """Integral of the unit tent kernel from minus infinity to r."""
    r=np.asarray(r,float)
    if not np.isfinite(r).all():raise ValueError('Finite kernel coordinate required')
    return np.where(r<=-1,0,np.where(r<0,.5*(r+1)**2,np.where(r<1,1-.5*(1-r)**2,1)))


def solid_kernel_fraction(sample_bed,xy,heights,spacing,axes,order=4):
    """Volume of the normalized trilinear kernel that lies below exact bed.

    Vertical integration is analytic. Each horizontal tent is split at its
    center and integrated by Gauss quadrature. Callers must compare quadrature
    orders on real geometry; no claim that one order resolves all triangles.
    xy, heights, bed and spacing share a length unit. axes maps grid XY to bed XY.
    Returns [height, point]; no off-mesh fill or clipping of bed queries.
    """
    xy=np.asarray(xy,float);heights=np.asarray(heights,float)
    h=np.asarray(spacing,float);axes=np.asarray(axes,float)
    if (xy.ndim!=2 or xy.shape[1]!=2 or heights.ndim!=1 or h.shape!=(3,) or
        axes.shape!=(2,2) or not all(np.isfinite(a).all() for a in (xy,heights,h,axes)) or
        (h<=0).any() or not np.allclose(axes@axes.T,np.eye(2),atol=1e-7,rtol=0) or
        not isinstance(order,int) or not 1<=order<=128):raise ValueError('Finite orthogonal kernel frame and quadrature order 1..128 required')
    nodes,weights=np.polynomial.legendre.leggauss(order)
    positive=(nodes+1)/2;w=weights/2*(1-positive)
    nodes=np.r_[-positive,positive];weights=np.r_[w,w]
    result=np.zeros((len(heights),len(xy)))
    xx,yy=np.meshgrid(nodes,nodes,indexing='ij');ww=np.outer(weights,weights).ravel()
    offsets=np.column_stack((xx.ravel(),yy.ravel()))*h[:2]@axes
    for first in range(0,len(offsets),32):
        query=xy[None,:,:]+offsets[first:first+32,None,:]
        bed=np.asarray(sample_bed(query[:,:,0].ravel(),query[:,:,1].ravel()),float)
        if bed.shape!=(query.shape[0]*len(xy),) or not np.isfinite(bed).all():raise ValueError('Complete finite exact-bed queries required')
        bed=bed.reshape(query.shape[:2])
        fraction=tent_cdf((bed[None,:,:]-heights[:,None,None])/h[2])
        result+=np.sum(fraction*ww[first:first+32][None,:,None],axis=1)
    if (result < -1e-12).any() or (result>1+1e-12).any():raise ValueError('Solid kernel integral escaped unit volume')
    return result


def density_target(particle_density,solid_fraction,boundary):
    rho=np.asarray(particle_density,float);solid=np.asarray(solid_fraction,float)
    b=np.asarray(boundary,float)
    if (rho.ndim!=3 or solid.shape!=rho.shape or b.shape!=(*rho.shape,4) or
        not all(np.isfinite(a).all() for a in (rho,solid,b)) or (rho<0).any() or
        (solid < -1e-12).any() or (solid>1+1e-12).any()):raise ValueError('Finite nonnegative density and solid kernel volume required')
    types=np.rint(b[...,3]).astype(int)
    if not np.isin(types,[0,1,2,3]).all():raise ValueError('Known fluid/solid/air/exterior types required')
    fluid=types==0;near_air=np.zeros_like(fluid)
    for axis in range(3):
        for sign in (-1,1):near_air|=shift(types==2,sign,axis)
    full=rho+solid
    # Free-surface kernel deficiency must not generate attraction. The measured
    # density remains untouched; this modifies only the correction equation.
    effective=np.where(near_air,np.maximum(full,1),full)
    # Paper section 3.2: cap the RHS, NOT the measured mass or accepted error.
    # Uncorrected excess remains in the particles and in the returned report.
    target=np.where(fluid,np.clip(effective,.5,1.5)-1,0)
    report=dict(fluid_cells=int(fluid.sum()),maximum_actual_total_density=float(full[fluid].max(initial=0)),
        maximum_actual_particle_density=float(rho[fluid].max(initial=0)),
        rms_actual_density_error=float(np.sqrt(np.mean((full[fluid]-1)**2))) if fluid.any() else 0,
        limited_rhs_cells=int((fluid&((effective<.5)|(effective>1.5))).sum()),
        free_surface_attraction_suppressed_cells=int((fluid&near_air&(full<1)).sum()),
        particle_mass_modified=False)
    # These global/phase totals must accompany frozen-fluid error statistics:
    # moving a clump across an old phase boundary is not density convergence.
    # Kernel weight on solid cells is not particle penetration; exact geometry
    # is checked separately. Do not discard that weight from volume accounting.
    report['whole_domain']=density_accounting(rho,solid,types)
    return target,report


def density_accounting(rho,solid,types):
    """Unclipped density and kernel-weight accounting across ALL grid phases.

    Density sums have units of cell volumes; multiply by the metric cell volume
    to recover m3. Kernel overlap in air/solid is reported, not reclassified as
    spray or lost water. Phase names describe input labels, not measured matter.
    """
    rho=np.asarray(rho,float);solid=np.asarray(solid,float);types=np.asarray(types)
    if (rho.ndim!=3 or solid.shape!=rho.shape or types.shape!=rho.shape or
        not np.isfinite(rho).all() or not np.isfinite(solid).all() or (rho<0).any() or
        (solid < -1e-12).any() or (solid>1+1e-12).any() or not np.isin(types,[0,1,2,3]).all()):
        raise ValueError('Matching nonnegative density, solid fraction and integral phase labels required')
    full=rho+solid
    def summarize(selected):
        p=rho[selected];total=full[selected];excess=np.maximum(total-1,0)
        return dict(cells=int(selected.sum()),particle_density_sum=float(p.sum()),
            maximum_particle_density=float(p.max(initial=0)),maximum_total_density=float(total.max(initial=0)),
            total_density_excess_sum=float(excess.sum()),total_density_excess_squared_sum=float(excess@excess),
            cells_total_density_over_one=int((total>1).sum()))
    worst=np.unravel_index(np.argmax(full),full.shape)
    return dict(**summarize(np.ones(rho.shape,bool)),
        maximum_total_density_cell_zyx=[int(v) for v in worst],
        maximum_total_density_cell_phase=int(types[worst]),
        phases={name:summarize(types==code) for code,name in enumerate(('fluid','solid','air','exterior'))},
        phase_scope='input grid labels; solid/air kernel overlap is not particle penetration or spray')


def solve(particle_density,solid_fraction,boundary,spacing,*,max_iterations=600,tolerance=1e-7):
    """Solve A q = density_error - D fixed, delta_x = fixed - M G q.

    q = dt^2*p2/rho0 removes timestep from the position-level system. Boundary
    XYZ contains prescribed displacement, not velocity. Current implementation
    reuses the existing stair-step mobility; exact solid density completion does
    not itself make that mobility conform to oblique bed faces.
    """
    target,report=density_target(particle_density,solid_fraction,boundary)
    displacement,potential,solver=project(np.zeros((*target.shape,3)),boundary,spacing=spacing,dt=1,
        max_iterations=max_iterations,tolerance=tolerance,boundary_pressure=np.zeros_like(target),
        target_divergence=target)
    report.update(solver=solver,maximum_grid_displacement_cells=float(np.linalg.norm(displacement/np.asarray(spacing),axis=-1).max()),
        momentum_modified=False,native_integrated=False,physical_visual_or_performance_acceptance=False)
    return displacement,potential,report
