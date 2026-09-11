"""Independent current-SDF foam transport reference, centimeters and seconds.

This is a coverage model, not resolved multiphase fluid or acceptance of a river.
"""
import numpy as np


def surface_coverage_statistics(surface):
    """Coverage at highest upward zero crossings; not visible-pixel coverage.

    Columns with no crossing are omitted, and terrain/camera occlusion is not
    modeled. This diagnostic must not be used as photographic acceptance.
    """
    surface=np.asarray(surface,dtype=float)
    if surface.ndim!=4 or surface.shape[-1]!=4 or not np.isfinite(surface).all():
        raise ValueError('Finite RGBA distance/coverage field required')
    phi=surface[...,0];foam=surface[...,1]
    crossing=(phi[:-1]<0)&(phi[1:]>=0)
    heights=np.where(crossing,np.arange(len(phi)-1)[:,None,None],-1).max(axis=0)
    y,x=np.nonzero(heights>=0);z=heights[y,x]
    if not len(z):return dict(columns=0,coverage_quantiles=[],fraction_above_0_1=0.)
    fraction=-phi[z,y,x]/(phi[z+1,y,x]-phi[z,y,x])
    values=foam[z,y,x]*(1-fraction)+foam[z+1,y,x]*fraction
    return dict(columns=len(z),coverage_quantiles=np.quantile(values,[0,.25,.5,.75,.9,.99,1]).tolist(),
        fraction_above_0_1=float(np.mean(values>.1)),mean_coverage=float(values.mean()),
        visible_pixel_or_reference_coverage=False)


def sample(field,unit):
    """Cell-centered trilinear interpolation, XYZ unit coordinates, ZYX field."""
    field=np.asarray(field,dtype=float)
    size=np.array(field.shape[:3][::-1])
    position=np.asarray(unit)*size-.5
    low=np.floor(position).astype(int);fraction=position-low
    result=np.zeros((len(position),field.shape[-1]))
    for z in (0,1):
        for y in (0,1):
            for x in (0,1):
                bit=np.array([x,y,z]);p=np.clip(low+bit,0,size-1)
                weight=np.prod(np.where(bit,fraction,1-fraction),axis=1)
                result+=field[p[:,2],p[:,1],p[:,0]]*weight[:,None]
    return result


def surface_kinematics(gradients, normal):
    """Coordinate-independent surface compression and deforming vorticity.

    J_ij = d velocity_i / d position_j, all gradients in inverse seconds.
    Surface compression is -trace((I-nn^T)J). Rigid rotation has curl but
    no symmetric strain, so it must not be an aeration source by itself.
    This is an empirical coverage-source diagnostic, not entrained air volume.
    """
    jacobian=np.stack(gradients,axis=-1)
    normal=np.asarray(normal,dtype=float)
    magnitude=np.linalg.norm(normal,axis=-1)
    valid=magnitude>.2
    n=np.divide(normal,magnitude[...,None],out=np.zeros_like(normal),where=valid[...,None])
    compression=np.maximum(-(np.trace(jacobian,axis1=-2,axis2=-1)-
        np.einsum('...i,...ij,...j->...',n,jacobian,n)),0)
    symmetric=.5*(jacobian+np.swapaxes(jacobian,-1,-2))
    strain=np.sqrt(2*np.sum(symmetric*symmetric,axis=(-2,-1)))
    dx,dy,dz=gradients
    curl=np.linalg.norm(np.stack((dy[...,2]-dz[...,1],dz[...,0]-dx[...,2],dx[...,1]-dy[...,0]),axis=-1),axis=-1)
    return np.where(valid,compression,0),np.where(valid,np.minimum(curl,strain),0)


def evolve(current,history,velocity,boundary,clock,extent,half_width=1050.,source_scale=1.,decay=.25,project_history=False,surface_source=False):
    current=np.asarray(current,dtype=float);velocity=np.asarray(velocity,dtype=float)
    boundary=np.asarray(boundary,dtype=float);extent=np.asarray(extent,dtype=float)
    half_width=np.asarray(half_width,dtype=float)
    if half_width.shape not in ((),(2,)) or not np.isfinite(half_width).all() or (half_width<=0).any():
        raise ValueError('Positive finite physical half-extent in both XY axes required')
    half_width=np.broadcast_to(half_width,(2,))
    clock=np.asarray(clock,dtype=float);dt=clock[1]
    if current.ndim!=4 or current.shape[-1]!=4 or not np.isfinite(current).all() or not np.isfinite(clock).all() or not 0<=dt<=.25:
        raise ValueError('Finite current surface and bounded simulation delta required')
    output=current.copy();audit=np.zeros(current.shape);audit[...,2]=dt
    if history is None or clock[2]!=0:
        output[...,1]=0
        return output,audit
    history=np.asarray(history,dtype=float)
    if history.shape!=current.shape or not np.isfinite(history).all() or (history[...,1]<0).any() or (history[...,1]>1).any():
        raise ValueError('Matching finite coverage history required')
    if dt==0:
        output[...,1]=history[...,1];audit[...,1]=history[...,1];audit[...,3]=history[...,1]
        return output,audit
    shape=np.array(current.shape[:3]);vshape=np.array(velocity.shape[:3])
    if not np.array_equal(shape,vshape*2) or boundary.shape!=velocity.shape or velocity.shape[-1]!=4 or not np.isfinite(velocity).all():
        raise ValueError('Aligned finite 2x render/flow grids required')
    if not np.isin(boundary[...,3],(0,1,2,3)).all():raise ValueError('Invalid boundary category')
    z,y,x=np.indices(shape)
    units=np.stack(((x+.5)/shape[2],(y+.5)/shape[1],(z+.5)/shape[0]),axis=-1)
    parents=boundary[...,3].repeat(2,0).repeat(2,1).repeat(2,2)
    cell=np.max(extent/shape[::-1]);du=1/vshape[::-1]
    mask=(abs(current[...,0])<float(np.float16(3*cell)))&(parents!=1)&(parents!=3)
    unit=units[mask];v=sample(velocity,unit)[:,:3]
    middle=sample(velocity,unit-.5*dt*v/extent)[:,:3]
    previous=unit-dt*middle/extent
    inside=((previous>0)&(previous<1)).all(axis=1)
    if project_history:
        # Retained only to reproduce the rejected projected-history-v2 capture.
        # It failed live parity and reduced exposed-surface foam; not runtime.
        point=previous[inside].copy();step=1/shape[::-1]
        for _ in range(2):
            phi=sample(history,point)[:,0];gradient=[]
            for axis in range(3):
                offset=np.zeros(3);offset[axis]=step[axis]
                gradient.append((sample(history,point+offset)[:,0]-sample(history,point-offset)[:,0])/(2*step[axis]*extent[axis]))
            gradient=np.stack(gradient,axis=1);norm=np.sum(gradient**2,axis=1)
            scale=np.divide(np.clip(phi,-2*cell,2*cell),norm,out=np.zeros_like(norm),where=norm>.04)
            point-=scale[:,None]*gradient/extent
        previous[inside]=point
        inside &= ((previous>0)&(previous<1)).all(axis=1)
    old=np.zeros(len(unit));old[inside]=np.clip(sample(history,previous[inside])[:,1],0,1)
    gradients=[]
    for axis in range(3):
        offset=np.zeros(3);offset[axis]=du[axis]
        gradients.append((sample(velocity,unit+offset)[:,:3]-sample(velocity,unit-offset)[:,:3])/(2*du[axis]*extent[axis]))
    dx,dy,dz=gradients
    curl=np.linalg.norm(np.stack((dy[:,2]-dz[:,1],dz[:,0]-dx[:,2],dx[:,1]-dy[:,0]),axis=1),axis=1)
    compression=np.maximum(-(dx[:,0]+dy[:,1]),0)
    if surface_source:
        # Sample the same rendered SDF that carries foam, at solver-scale
        # offsets to avoid treating subcell reconstruction noise as a crest.
        normal=[]
        for axis in range(3):
            offset=np.zeros(3);offset[axis]=du[axis]
            normal.append((sample(current,unit+offset)[:,0]-sample(current,unit-offset)[:,0])/(2*du[axis]*extent[axis]))
        compression,curl=surface_kinematics(gradients,np.stack(normal,axis=-1))
    band=np.clip(1-abs(current[...,0][mask])/(2*cell),0,1)
    physical=abs((unit-.5)*extent)
    edge=np.clip((half_width-physical[:,:2]).min(axis=1)/(2*np.max(du[:2]*extent[:2])),0,1)
    speed=np.clip((np.linalg.norm(v,axis=1)-50)/150,0,1)
    rate=np.minimum(8,source_scale*band*edge*speed*(np.maximum(curl-1.2,0)*.35+np.maximum(compression-.8,0)*.5))
    total=rate+decay;equilibrium=np.divide(rate,total,out=np.zeros_like(rate),where=total>0)
    foam=np.clip(np.where(total>0,equilibrium+(old-equilibrium)*np.exp(-total*dt),old),0,1)
    output[...,1]=0;output[...,1][mask]=foam.astype(np.float16).astype(float)
    audit[...,0][mask]=rate;audit[...,1][mask]=old;audit[...,3][mask]=foam
    return output,audit
