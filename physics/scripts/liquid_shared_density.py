"""Whole-support density descent through one compact displacement field.

The chain rule is S^T grad(E), where S is the SAME component-wise compact
interpolator used by particle motion and inverse interface transport. No phase
mask removes density residuals. Mobility only fixes displacement unknowns.
This is a CPU position reference, not native momentum/time integration.
"""
import numpy as np
from liquid_boundary_displacement import compact_rows, project_rows
from liquid_compatible_advection import sample_compact
from liquid_particle_quantization import position_error_box, quantized_endpoint
from liquid_swept_bed import swept_contact_planes


def compact_adjoint(points, values, cells, spacing, mobility, *, batch_size=8192):
    """Apply the exact interpolation transpose without retaining a particle matrix."""
    p=np.asarray(points,float);v=np.asarray(values,float);c=np.asarray(cells)
    h=np.asarray(spacing,float);m=np.asarray(mobility,float)
    if (p.ndim!=2 or p.shape[1]!=3 or v.shape!=p.shape or c.shape!=(3,) or
            not np.isfinite(c).all() or (c!=np.floor(c)).any() or (c<4).any() or
            m.shape!=(*c.astype(int)[::-1],3) or not np.isin(m,[0,1]).all() or
            not isinstance(batch_size,int) or batch_size<1):
        raise ValueError('Complete integer grid, matching vector samples and binary mobility required')
    # compact_rows validates finite positions, values, metric and full support.
    result=np.zeros_like(m)
    for first in range(0,len(p),batch_size):
        ii,ww=compact_rows(p[first:first+batch_size],v[first:first+batch_size],c,h,m)
        np.add.at(result.ravel(),ii.ravel(),ww.ravel())
    if h.shape!=(3,) or not np.isfinite(h).all() or (h<=0).any() or not np.isfinite(v).all():
        raise ValueError('Finite values and positive metric required')
    return result


def shared_direction(points, particle_gradient, cells, spacing, mobility, *, max_cells=.25):
    """One cell-metric descent direction; no individual particle step clamps."""
    h=np.asarray(spacing,float)
    if not np.isfinite(max_cells) or max_cells<=0:
        raise ValueError('Positive shared trust radius required')
    gradient=compact_adjoint(points,particle_gradient,cells,h,mobility)
    field=-gradient*h*h
    motion=sample_compact(points,field.transpose(2,1,0,3),h)
    maximum=float(np.linalg.norm(motion/h,axis=1).max(initial=0))
    if maximum>max_cells:field*=max_cells/maximum;motion*=max_cells/maximum
    return field,dict(directional_derivative=float(np.sum(particle_gradient*motion)),
        gradient_squared_cell_metric=float(np.sum((gradient*h)**2)),
        maximum_particle_displacement_cells=float(np.linalg.norm(motion/h,axis=1).max(initial=0)),
        density_phase_masked=False,independent_particle_correction=False)


def constrained_field(points, local, desired, axes, spacing, lo, hi, sampler, required,
                      mobility, *, native_positions=False, iterations=16, max_sweeps=512, active_set=False, field_equality=None):
    """Discover exact swept contacts and project the SHARED field before motion.

    All rows accumulate and every solve starts from the original desired field.
    Contact metric is cell displacement; bounds retain physical centimetres.
    Float32 endpoint guards are derived from actual world position storage.
    Failure returns a diagnostic candidate, never a usable accepted correction.
    """
    h=np.asarray(spacing,float);m=np.asarray(mobility,float);base=np.asarray(desired,float)/h
    if (base.shape!=m.shape or not np.isin(m,[0,1]).all() or
            np.any(base[m==0]!=0) or iterations<1 or max_sweeps<1):
        raise ValueError('Matching mobile field and positive solve limits required')
    cells=np.array(base.shape[:3][::-1]);field=base.copy();history=[];known=set()
    indices=np.empty((0,96),int);weights=np.empty((0,96));bounds=np.empty(0)
    equality=None;equality_rhs=None;equality_report=None
    if field_equality is not None:
        from liquid_field_equality import project_field_equality
        equality=np.asarray(field_equality[0],float)*h;equality_rhs=float(field_equality[1])
        if equality.shape!=m.shape or np.any(equality[m==0]!=0):raise ValueError('Equality must use the same mobile shared field')
        field,equality_report=project_field_equality(base,indices,weights,bounds,equality,equality_rhs,max_sweeps=max_sweeps)
        if not equality_report['converged']:return field*h,dict(converged=False,history=[],constraints=0,equality=equality_report)
    radius=float(np.linalg.norm(h))
    error_box=position_error_box(points,radius) if native_positions else np.zeros_like(points)
    for iteration in range(iterations):
        motion=sample_compact(local,(field*h).transpose(2,1,0,3),h)
        tested=motion
        if native_positions:
            stored,_=quantized_endpoint(points,motion@axes,radius);tested=(stored-points)@axes.T
        ids,normals,limits,sweep,times,faces=swept_contact_planes(sampler,points,tested,axes,required)
        if native_positions:limits+=np.sum(np.abs(normals@axes)*error_box[ids],axis=1)
        pp=[];nn=[];cc=[]
        for row,k in enumerate(ids):
            key=(int(k),int(faces[row]),normals[row].tobytes(),float(limits[row]))
            if key not in known:
                known.add(key);pp.append(local[k]);nn.append(normals[row]);cc.append(limits[row])
        end=local+tested;outside=(end<lo)|(end>hi)
        for axis in range(3):
            for k in np.flatnonzero(outside[:,axis]):
                sign=1 if end[k,axis]<lo[axis] else -1;key=(int(k),'outer',axis,sign)
                if key not in known:
                    known.add(key);n=np.zeros(3);n[axis]=sign
                    pp.append(local[k]);nn.append(n)
                    cc.append(float(sign*((lo if sign==1 else hi)[axis]-local[k,axis]))+
                              float(np.abs(axes[axis])@error_box[k]))
        record=dict(iteration=iteration,new_constraints=len(pp),outer_violations=int(outside.any(1).sum()),**sweep)
        history.append(record)
        if not len(ids) and not outside.any():
            return field*h,dict(converged=True,history=history,constraints=len(bounds),native_positions=native_positions,
                independent_particle_correction=False,equality=equality_report)
        if not pp:break
        ii,ww=compact_rows(np.asarray(pp),np.asarray(nn),cells,h,m)
        # Unknowns are dimensionless cell displacements, not world cm.
        ww*=h[ii%3]
        indices=np.concatenate((indices,ii));weights=np.concatenate((weights,ww));bounds=np.r_[bounds,cc]
        if equality is not None:
            field,equality_report=project_field_equality(base,indices,weights,bounds,equality,equality_rhs,max_sweeps=max_sweeps)
            record['linearized_volume_and_contacts']=equality_report
            if not equality_report['converged']:break
            continue
        field=base.copy();dual=None;converged=False
        for first in range(0,max_sweeps,16):
            field,dual,violation=project_rows(field,indices,weights,bounds,dual,sweeps=min(16,max_sweeps-first))
            gap=bounds-np.sum(field.ravel()[indices]*weights,axis=1)
            kkt=float(np.max(np.where(dual>0,abs(gap),np.maximum(gap,0)),initial=0))
            if kkt<=1e-7:converged=True;break
        if not converged and active_set:
            # Solve the SAME projection's contact dual; no pressure equality,
            # phase-masked density target or diagonal regularizer is added.
            # Sparse support forms B B^T; only the small contact system is dense.
            from scipy import sparse
            from liquid_contact_active_set import polish_contact_dual
            B=sparse.csr_matrix((weights.ravel(),(np.repeat(np.arange(len(bounds)),96),indices.ravel())),
                               shape=(len(bounds),base.size))
            B.eliminate_zeros()
            S=(B@B.T).toarray();rhs=bounds-np.asarray(B@base.ravel()).ravel()
            dual,polish=polish_contact_dual(S,rhs,dual)
            field=base+np.asarray(B.T@dual).reshape(base.shape)
            gap=bounds-np.asarray(B@field.ravel()).ravel()
            kkt=float(np.max(np.where(dual>0,abs(gap),np.maximum(gap,0)),initial=0))
            violation=float(np.maximum(gap,0).max(initial=0))
            converged=polish['converged'] and kkt<=1e-7
            record['active_set_refinement']=polish
        record.update(projection_sweeps=min(first+16,max_sweeps),projection_kkt_error_cm=kkt,
                      maximum_constraint_violation_cm=violation,projection_converged=converged)
        if not converged:break
    return field*h,dict(converged=False,history=history,constraints=len(bounds),native_positions=native_positions,
        independent_particle_correction=False,equality=equality_report)
