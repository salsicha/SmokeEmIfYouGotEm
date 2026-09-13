"""Exact triangle-wise clearance along short straight correction segments.

Checking endpoints alone misses a rock ridge crossed between them. Barycentric
coordinates and height are affine along each triangle interval, so its minimum
vertical clearance occurs at an interval endpoint. No distance sampling or
height interpolation across triangle edges is used here.
"""
import numpy as np
from liquid_edge_visibility import edge_visibility_planes


def swept_clearance(sampler,start,end,*,maximum_nominal_span=8):
    a=np.asarray(start,float);b=np.asarray(end,float)
    if a.ndim!=2 or a.shape[1]!=3 or b.shape!=a.shape or not np.isfinite(a).all() or not np.isfinite(b).all():
        raise ValueError('Finite matching ENU segment endpoints required')
    if not isinstance(maximum_nominal_span,int) or maximum_nominal_span<1:raise ValueError('Positive bounded search span required')
    if not len(a):return np.empty(0),np.empty(0),np.empty(0,dtype=int)
    # Half-cell vertex motion guarantees coverage in this interior rectangle.
    # Reject near-boundary queries rather than assuming a partly off-mesh path
    # is safe because its two endpoints happened to land on triangles.
    xy=np.concatenate((a[:,:2],b[:,:2]))
    if (np.any(xy[:,0]<sampler.east[0]+sampler.dx/2) or np.any(xy[:,0]>sampler.east[-1]-sampler.dx/2) or
        np.any(xy[:,1]<sampler.north[-1]+sampler.dy/2) or np.any(xy[:,1]>sampler.north[0]-sampler.dy/2)):
        raise ValueError('Swept query leaves the guaranteed registered-mesh interior')
    c0=np.floor((a[:,0]-sampler.east[0])/sampler.dx).astype(int)
    c1=np.floor((b[:,0]-sampler.east[0])/sampler.dx).astype(int)
    r0=np.floor((sampler.north[0]-a[:,1])/sampler.dy).astype(int)
    r1=np.floor((sampler.north[0]-b[:,1])/sampler.dy).astype(int)
    if np.any(abs(c1-c0)>maximum_nominal_span) or np.any(abs(r1-r0)>maximum_nominal_span):
        raise ValueError('Correction exceeds the bounded triangle search span')
    cmin=np.minimum(c0,c1)-1;rmin=np.minimum(r0,r1)-1
    nc=abs(c1-c0)+3;nr=abs(r1-r0)+3;travel=b-a
    minimum=np.full(len(a),np.inf);fraction=np.full(len(a),np.nan);face_ids=np.full(len(a),-1,dtype=int)
    for dr in range(int(nr.max())):
        for dc in range(int(nc.max())):
            rows=rmin+dr;cols=cmin+dc
            indices=np.flatnonzero((dr<nr)&(dc<nc)&(rows>=0)&(rows<sampler.rows-1)&(cols>=0)&(cols<sampler.cols-1))
            for side in (0,1):
                faces=rows[indices]*(sampler.cols-1)+cols[indices]+side*sampler.quads
                p,q,s=(sampler.xyz[sampler.faces[faces,j]] for j in range(3))
                u=q-p;v=s-p;offset=a[indices]-p;d=travel[indices]
                determinant=u[:,0]*v[:,1]-u[:,1]*v[:,0]
                x=(offset[:,0]*v[:,1]-offset[:,1]*v[:,0])/determinant
                y=(u[:,0]*offset[:,1]-u[:,1]*offset[:,0])/determinant
                dx=(d[:,0]*v[:,1]-d[:,1]*v[:,0])/determinant
                dy=(u[:,0]*d[:,1]-u[:,1]*d[:,0])/determinant
                lo=np.zeros(len(indices));hi=np.ones(len(indices));valid=np.ones(len(indices),bool)
                for value,slope in ((x,dx),(y,dy),(1-x-y,-dx-dy)):
                    moving=slope!=0;cross=np.divide(-value,slope,out=np.zeros_like(value),where=moving)
                    lo=np.where(slope>0,np.maximum(lo,cross),lo)
                    hi=np.where(slope<0,np.minimum(hi,cross),hi)
                    valid&=moving|(value>=0)
                valid&=lo<=hi
                base=offset[:,2]-x*u[:,2]-y*v[:,2]
                slope=d[:,2]-dx*u[:,2]-dy*v[:,2]
                at=np.where(slope>=0,lo,hi);height=base+at*slope
                take=valid&(height<minimum[indices]);selected=indices[take]
                minimum[selected]=height[take];fraction[selected]=at[take];face_ids[selected]=faces[take]
    if not np.isfinite(minimum).all():raise ValueError('Incomplete swept triangle coverage')
    return minimum,fraction,face_ids


def swept_contact_planes(sampler,positions_cm,movement_cm,world_axes,required_clearance_cm):
    """Contact Jacobians at the worst point of each straight correction path.

    Interior edge hits use a clearance plane through the original particle and
    the lifted edge, independent of the changing crossing time. Other contacts
    use fraction * face normal, avoiding division by a vanishing time. The
    unchanged final geometric audit still verifies the complete path.
    """
    p=np.asarray(positions_cm,float);d=np.asarray(movement_cm,float);axes=np.asarray(world_axes,float)
    required=np.asarray(required_clearance_cm,float)
    if (p.ndim!=2 or p.shape[1]!=3 or d.shape!=p.shape or axes.shape!=(3,3) or required.shape!=(len(p),) or
        not all(np.isfinite(a).all() for a in (p,d,axes,required)) or (required<0).any() or
        not np.allclose(axes@axes.T,np.eye(3),atol=1e-7,rtol=0)):
        raise ValueError('Finite matching positions, movement, orthogonal frame and clearance required')
    flip=np.array([1.,-1.,1.]);end=p+d@axes
    clearance,fraction,faces=swept_clearance(sampler,p*flip/100,end*flip/100)
    clearance_cm=100*clearance
    # This is the existing geometric reference's 1e-6 cm residual threshold,
    # not a new allowance for crossing solid terrain. Raw minima are reported.
    need=clearance_cm<required-1e-6
    if np.any(need&(fraction==0)):raise ValueError('Initial particle already violates required swept clearance')
    selected=np.flatnonzero(need&(fraction>0))
    vertices=sampler.xyz[sampler.faces[faces[selected]]]
    normal=np.cross(vertices[:,2]-vertices[:,0],vertices[:,1]-vertices[:,0])
    normal/=np.linalg.norm(normal,axis=1)[:,None];normal*=flip
    at=p[selected]+fraction[selected,None]*(d[selected]@axes)
    plane=at.copy();plane[:,2]+=required[selected]-clearance_cm[selected]
    lower=np.sum((plane-p[selected])*normal,axis=1)
    jacobian=(normal@axes.T)*fraction[selected,None]
    best_error=np.full(len(selected),np.inf);ray_normal=np.zeros_like(normal);ray_used=np.zeros(len(selected),bool)
    world_vertices=vertices*flip*100
    for first,second in ((0,1),(1,2),(2,0)):
        candidate,valid,at_time,_=edge_visibility_planes(p[selected],d[selected]@axes,
            world_vertices[:,first],world_vertices[:,second],required[selected])
        error=abs(at_time-fraction[selected])
        use=valid&(fraction[selected]>0)&(fraction[selected]<1)&(error<=1e-8)&(
            (error<best_error)|((error==best_error)&(candidate[:,2]>ray_normal[:,2])))
        ray_normal[use]=candidate[use];best_error[use]=error[use];ray_used|=use
    jacobian[ray_used]=ray_normal[ray_used]@axes.T;lower[ray_used]=0
    return selected,jacobian,lower,dict(minimum_swept_bed_clearance_cm=float(clearance_cm.min(initial=np.inf)),
        particles_with_swept_bed_penetration=int((clearance_cm<0).sum()),
        minimum_swept_required_margin_cm=float((clearance_cm-required).min(initial=np.inf)),
        discovered_swept_contacts=len(selected),edge_visibility_contacts=int(ray_used.sum())),fraction[selected],faces[selected]
