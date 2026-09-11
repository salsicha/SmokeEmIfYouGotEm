"""Independent segment/heightfield-triangle contact reference (centimetres).

Enumerate segment endpoints and XY triangle-edge crossing times. Vertical
clearance is affine inside a triangle, so its minimum lies at one of those
events. This reference is not the shader's half-space interval implementation.
Only a single-valued top surface is supported, not overhangs or moving rocks.
"""
import numpy as np


def segment_triangle_contact(start,end,triangle,padding=.1):
    start=np.asarray(start,float);end=np.asarray(end,float);triangle=np.asarray(triangle,float)
    if start.shape!=(3,) or end.shape!=(3,) or triangle.shape!=(3,3) or not np.isfinite(np.r_[start,end,triangle.ravel(),padding]).all() or padding<0:
        raise ValueError('Finite segment, triangle and nonnegative padding required')
    a,b,c=triangle
    basis=np.column_stack([(b-a)[:2],(c-a)[:2]])
    if abs(np.linalg.det(basis))<1e-6:
        raise ValueError('Triangle has degenerate XY projection')
    uv0=np.linalg.solve(basis,(start-a)[:2]);uv1=np.linalg.solve(basis,(end-a)[:2])
    bary0=np.r_[uv0,1-uv0.sum()];bary1=np.r_[uv1,1-uv1.sum()]
    events=[0.,1.]
    for initial,slope in zip(bary0,bary1-bary0):
        if abs(slope)>1e-14:
            t=-initial/slope
            if 0<=t<=1:events.append(t)
    for t in events:
        uv=uv0+t*(uv1-uv0)
        if min(uv[0],uv[1],1-uv.sum())>=-1e-10:
            bed=a[2]+uv[0]*(b[2]-a[2])+uv[1]*(c[2]-a[2])
            z=start[2]+t*(end[2]-start[2])
            if z-bed<=padding+1e-10:return True
    return False
