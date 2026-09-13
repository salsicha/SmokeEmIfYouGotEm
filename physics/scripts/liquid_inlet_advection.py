"""Float64 reference for upstream relaxation and prescribed inlet advection.

This does not authorize reverse outflow or delete water. The boundary supplies
normal momentum; tangential transport is unchanged. Terrain contact follows it.
"""
import numpy as np


def relaxation(distance, width, depth, dt):
    """Exact frozen-coefficient integration, not a per-frame blend.

    Four crossing times of damping is an experimental coefficient. Neither
    this scalar test nor a passing particle gate establishes wave absorption.
    """
    if not np.isfinite([distance,width,depth,dt]).all() or min(width,depth,dt)<=0 or distance<0:
        raise ValueError('Invalid inlet relaxation geometry or timestep')
    q=np.clip(1-distance/width,0,1)
    x=4*np.sqrt(981*depth)/width*q*q*(3-2*q)*dt
    end=np.exp(-x)
    average=-np.expm1(-x)/x if x else 1.
    return average,end


def constrain(start, predicted, velocity, dt, profile, bed_query, *, relaxation_enabled=True):
    start, predicted, velocity = (np.asarray(v, dtype=float) for v in (start, predicted, velocity))
    unchanged = (predicted.copy(), velocity.copy(), 0)
    packed = np.asarray(profile['packed_vectors'], dtype=float)
    axes = packed[:2]*[1, -1, 1]
    origin = packed[2]*[1, -1, 1]
    half = packed[3, :2]/2
    extent = packed[3]
    def local(p):
        d = p-origin
        return np.r_[axes @ d+half, d[2]]
    a, b = local(start), local(predicted)
    if (not np.isfinite(np.r_[a,b,velocity,dt]).all() or dt <= 0 or
            np.any(a < 0) or np.any(a > extent)):
        return unchanged
    cells = packed[5].astype(int)
    distances=np.array([a[0],extent[0]-a[0],a[1],extent[1]-a[1]])
    nearest=np.argsort(distances); face=int(nearest[0]);d=distances[face]
    width=min(4*packed[4,face//2],.25*extent[face//2])
    marker=0
    if (relaxation_enabled and distances[nearest[1]]-d>1.e-6 and d<width and 0<=b[2]<=extent[2]):
        tangent=1-face//2
        column=int(np.clip(np.floor(a[tangent]/packed[4,tangent]),0,cells[tangent]-1))
        row=[0,cells[1],2*cells[1],2*cells[1]+cells[0]][face]+column
        _,stage,inward=packed[8+row]
        bed=float(bed_query(face,a[tangent]))
        if np.isfinite([bed,stage,inward]).all() and inward>0 and stage>bed and start[2]>bed:
            average,end=relaxation(d,width,stage-bed,dt)
            normal=axes[face//2]*(1 if face%2==0 else -1)
            travel=predicted-start
            predicted=predicted+normal*(inward*dt-np.dot(travel,normal))*(1-average)
            velocity=velocity+normal*(inward-np.dot(velocity,normal))*(1-end)
            b=local(predicted);marker=face+1
    unchanged=(predicted.copy(),velocity.copy(),marker)
    hits = []
    for axis in range(3):
        if b[axis] < 0 or b[axis] > extent[axis]:
            high = b[axis] > extent[axis]
            t = ((extent[axis] if high else 0)-a[axis])/(b[axis]-a[axis])
            hits.append((t, 2*axis+int(high)))
    if not hits:
        return unchanged
    hits.sort()
    t, face = hits[0]
    if (face >= 4 or not 0 <= t <= 1 or
            (len(hits)>1 and abs(hits[1][0]-t)<=8*np.finfo(np.float32).eps)):
        return unchanged
    tangent = 1 if face < 2 else 0
    hit = a+t*(b-a)
    column = int(np.clip(np.floor(hit[tangent]/packed[4,tangent]),0,cells[tangent]-1))
    row = [0,cells[1],2*cells[1],2*cells[1]+cells[0]][face]+column
    _, stage, inward = packed[8+row]
    bed = float(bed_query(face, hit[tangent]))
    if (not np.isfinite([bed,stage,inward]).all() or inward < 0 or
            hit[2]+origin[2] >= stage or hit[2]+origin[2] <= bed):
        return unchanged
    normal = axes[face//2]*(1 if face%2 == 0 else -1)
    travel = predicted-start
    corrected = start+travel-normal*np.dot(travel,normal)+normal*(inward*dt)
    corrected_velocity = velocity+normal*(inward-np.dot(velocity,normal))
    return corrected, corrected_velocity, face+1
