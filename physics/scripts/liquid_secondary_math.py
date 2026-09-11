"""Independent reference for the empirical metric secondary-particle candidate."""
import numpy as np


def endpoint_surface_distance(endpoint,elapsed,velocity,previous_distance):
    """RK2 characteristic prediction, not the newly reconstructed surface.

    Callables take local centimetres; velocity returns local cm/s. This is
    suitable for a phase label at the integrated endpoint, not a replacement
    for current-surface collision or validation against rendered geometry.
    """
    p=np.asarray(endpoint,float)
    if p.shape!=(3,) or not np.isfinite(p).all() or not np.isfinite(elapsed) or not 0<=elapsed<=.25:
        raise ValueError('Finite endpoint and bounded surface age gap required')
    v=np.asarray(velocity(p),float)
    if v.shape!=(3,) or not np.isfinite(v).all():raise ValueError('Finite XYZ velocity required')
    mid=np.asarray(velocity(p-.5*elapsed*v),float)
    if mid.shape!=(3,) or not np.isfinite(mid).all():raise ValueError('Finite XYZ midpoint velocity required')
    phi=float(previous_distance(p-elapsed*mid))
    if not np.isfinite(phi):raise ValueError('Finite previous distance required')
    return phi


def shared_surface_ready(surface_age,simulation_age,dt):
    if not np.isfinite([surface_age,simulation_age,dt]).all() or not 0<=dt<=.25:return False
    gap=simulation_age-surface_age
    return bool(surface_age>0 and -.0005<=gap<=min(.25,max(.05,2*dt)))


def constrained_foam_position(position,flow_world,phi,gradient_local,rotation,dt):
    """Project to the sampled interface and advect; rotation rows are grid axes."""
    p,f,g,r=[np.asarray(x,dtype=float) for x in (position,flow_world,gradient_local,rotation)]
    if p.shape!=(3,) or f.shape!=(3,) or g.shape!=(3,) or r.shape!=(3,3) or not all(np.isfinite(x).all() for x in (p,f,g,r)) or not np.isfinite([phi,dt]).all() or not 0<=dt<=.25:
        raise ValueError('Finite foam constraint state required')
    if dt==0:return p.copy()
    if not np.allclose(r@r.T,np.eye(3),atol=1e-6) or np.dot(g,g)<.04:
        raise ValueError('Orthonormal grid basis and valid SDF gradient required')
    return p+(-phi*g/np.dot(g,g))@r+f*dt


def metric_curl(velocity,extent_cm):
    velocity=np.asarray(velocity,dtype=float);extent=np.asarray(extent_cm,dtype=float)
    if velocity.ndim!=4 or velocity.shape[-1]!=3 or min(velocity.shape[:3])<2 or extent.shape!=(3,) or not np.isfinite(velocity).all() or not np.isfinite(extent).all() or (extent<=0).any():
        raise ValueError('Finite vector grid and positive metric extents required')
    cell=extent/np.array(velocity.shape[:3][::-1])
    dz,dy,dx=np.gradient(velocity,*cell[::-1],axis=(0,1,2))
    return np.stack((dy[...,2]-dz[...,1],dz[...,0]-dx[...,2],dx[...,1]-dy[...,0]),axis=-1)


def expected_emission(phi_cm,curl_per_s,speed_cm_s,cell_cm,dt):
    cell=np.asarray(cell_cm,dtype=float)
    if cell.shape!=(3,) or not np.isfinite(cell).all() or (cell<=0).any() or not np.isfinite(dt) or not 0<=dt<=.25:
        raise ValueError('Finite metric cell and bounded elapsed time required')
    phi,curl,speed=np.broadcast_arrays(phi_cm,curl_per_s,speed_cm_s)
    if not all(np.isfinite(x).all() for x in (phi,curl,speed)):raise ValueError('Finite flow/surface required')
    t=np.clip((curl-1.2)/(4.-1.2),0,1)
    activity=t*t*(3-2*t)*np.clip((speed-50)/150,0,1)
    band=cell.max();area=2*np.prod(cell)/band*1e-4*np.clip(1+phi/band,0,1)
    return np.where((phi<=0)&(phi>-band),120*area*activity*dt,0.)


def update(position,velocity,flow_world,gravity,buoyancy,phi,thickness,dt):
    p,v,f,g,b=[np.asarray(x,dtype=float) for x in (position,velocity,flow_world,gravity,buoyancy)]
    if any(x.shape!=(3,) or not np.isfinite(x).all() for x in (p,v,f,g,b)) or not np.isfinite([phi,thickness,dt]).all() or thickness<=0 or not 0<=dt<=.25:
        raise ValueError('Finite state, positive thickness, and bounded timestep required')
    if dt==0:return p.copy(),v.copy()
    if abs(phi)<thickness:return p+f*dt,f.copy()
    if phi>0:return p+v*dt+.5*g*dt*dt,v+g*dt
    terminal=f+b/4;decay=np.exp(-4*dt)
    return p+terminal*dt+(v-terminal)*(1-decay)/4,terminal+(v-terminal)*decay
