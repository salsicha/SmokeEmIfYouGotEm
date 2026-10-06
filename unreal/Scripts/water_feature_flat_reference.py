"""Manufactured planar reference; a lattice calibration is not a river fix."""
import math
import numpy as np


def planar_phi(shape,height_cells):
    if (len(shape)!=3 or any(type(n)!=int or n<12 for n in shape)
            or type(height_cells)!=int or not 4<=height_cells<=shape[2]-5):
        raise ValueError('Interior integer-height plane in a finite 3D domain required')
    return np.broadcast_to(np.arange(shape[2],dtype=np.float32)[None,None,:]+.5-height_cells,shape).copy()


def lattice_particle_phi(levels,height_cells,factor):
    """Interior d=2,zero-jitter lattice, matching the pinned native union kernel.

    Particle centers are quarter/three-quarter cell positions. The native
    kernel starts at +radius and searches floor(radius)+1 neighboring cells.
    Only the interior vertical column (far from walls) is predicted here.
    """
    if type(height_cells)!=int or not math.isfinite(factor) or not 0<factor<=2:
        raise ValueError('Finite supported radius and integer-height lattice required')
    radius=.5*math.sqrt(3)*(factor+.01)
    reach=int(radius)+1
    result=[]
    for k in levels:
        if type(k)!=int or k<2:
            raise ValueError('Interior integer cell index required')
        candidates=[radius]
        for cell in range(max(2,k-reach),min(height_cells-1,k+reach)+1):
            for dz in (.25,.75):
                candidates.append(math.sqrt(.25**2+.25**2+(k+.5-cell-dz)**2)-radius)
        result.append(min(candidates))
    return np.array(result)


def flat_lattice_radius():
    """Radius makes the two grid samples around this specific plane symmetric.

    Derived from point distances, NOT fitted to the measured eddy residual.
    Assumes a regular8-particle/cell lattice and this grid-phase/orientation.
    """
    radius=(math.sqrt(3)/4+math.sqrt(11)/4)/2
    return radius/(.5*math.sqrt(3))-.01


def root_height(levels,phi):
    levels,phi=list(levels),np.asarray(phi,float)
    if (phi.shape!=(len(levels),) or not np.isfinite(phi).all()
            or any(b!=a+1 for a,b in zip(levels,levels[1:]))):
        raise ValueError('Consecutive finite cell-centered samples required')
    roots=[a+.5-float(x)/(float(y)-float(x)) for a,x,y in zip(levels,phi,phi[1:]) if x<0<=y]
    if len(roots)!=1:raise ValueError('Exactly one upward crossing required')
    return roots[0]
