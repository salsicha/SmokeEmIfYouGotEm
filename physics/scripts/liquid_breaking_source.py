"""Resolved convex/outward crest diagnostic for current liquid SDF snapshots.

Centimeters and seconds. Uses the convexity and outward-velocity criteria in
Bender et al., Turbulent Micropolar SPH Fluids with Foam, section 6 (2018),
https://dankoschier.github.io/resources/papers/BKKW18.pdf . This grid curvature
estimator is not their SPH neighborhood sum or their entrained-air model.
No normalization to each frame's maximum: that would whiten calm frames.
"""
import numpy as np
from liquid_current_surface_foam import sample


def crest_activity(surface,velocity,unit,extent):
    """Return signed mean-curvature sum, alignment, and convex extension / s.

    Positive divergence of the outward SDF normal means convex liquid.
    All differences use physical solver-cell sizes, including cross terms.
    Smooth .6-.8 alignment ramp avoids the paper's binary classification
    becoming a visible temporal threshold in an Eulerian coverage texture.
    Values are source diagnostics, not measured air entrainment or foam area.
    """
    extent=np.asarray(extent,dtype=float);unit=np.asarray(unit,dtype=float)
    du=1/np.array(velocity.shape[:3][::-1]);step=du*extent
    center=sample(surface,unit)[:,0]
    gradient=np.zeros((len(unit),3));hessian=np.zeros((len(unit),3,3))
    for a in range(3):
        da=np.eye(3)[a]*du
        plus=sample(surface,unit+da)[:,0];minus=sample(surface,unit-da)[:,0]
        gradient[:,a]=(plus-minus)/(2*step[a])
        hessian[:,a,a]=(plus-2*center+minus)/(step[a]**2)
        for b in range(a):
            db=np.eye(3)[b]*du
            cross=(sample(surface,unit+da+db)[:,0]-sample(surface,unit+da-db)[:,0]
                -sample(surface,unit-da+db)[:,0]+sample(surface,unit-da-db)[:,0])/(4*step[a]*step[b])
            hessian[:,a,b]=cross;hessian[:,b,a]=cross
    magnitude=np.linalg.norm(gradient,axis=1);valid=magnitude>.2
    normal=np.divide(gradient,magnitude[:,None],out=np.zeros_like(gradient),where=valid[:,None])
    curvature=np.divide(np.trace(hessian,axis1=1,axis2=2)-
        np.einsum('ni,nij,nj->n',normal,hessian,normal),magnitude,
        out=np.zeros(len(unit)),where=valid)
    flow=sample(velocity,unit)[:,:3];speed=np.linalg.norm(flow,axis=1)
    alignment=np.divide(np.sum(flow*normal,axis=1),speed,out=np.zeros(len(unit)),where=speed>0)
    gate=np.clip((alignment-.6)/.2,0,1);gate=gate*gate*(3-2*gate)
    activity=np.maximum(curvature,0)*speed*gate
    return curvature,alignment,activity
