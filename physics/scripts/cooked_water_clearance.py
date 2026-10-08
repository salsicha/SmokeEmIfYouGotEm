"""Bounded exact water-exclusion predicate on registered cooked cells.

Distances are capped at the requested clearance, not reported as surveyed or
global nearest-water distances. All wet cells capable of failing that clearance
remain in the query; no nearest-station assumption is made at close river bends.
"""
import numpy as np
from scipy.spatial import cKDTree
from export_colorado_continuous_runtime import _registered_geometry


class CookedWaterClearance:
    def __init__(self,mapping,terrain,grid,wet,*,block_cells=262144):
        if (type(block_cells) is not int or type(grid['ny']) is not int or
                type(grid['nx']) is not int or min(grid['ny'],grid['nx'])<1 or
                block_cells<grid['ny'] or
                not np.isfinite([grid['dx'],grid['dy']]).all() or min(grid['dx'],grid['dy'])<=0):
            raise ValueError('Invalid cooked-water clearance grid or block size')
        if np.shape(wet)!=(grid['ny'],grid['nx']):
            raise ValueError('Cooked wet mask has the wrong shape')
        _,self.selected,self.lateral,self.origin=_registered_geometry(mapping,terrain,grid)
        self.wet=wet;self.columns=max(1,block_cells//grid['ny'])
        self.diagonal=np.hypot(grid['dx'],grid['dy'])
        any_wet=False
        for start in range(0,grid['nx'],self.columns):
            block=wet[:,start:start+self.columns]
            if not np.all((block==0)|(block==1)):
                raise ValueError('Cooked wet mask must contain only zero or one')
            any_wet=any_wet or bool(np.any(block))
        if not any_wet:raise ValueError('No solved water for vegetation exclusion')
        # Same operation order as registered_queries, evaluated at both lateral
        # endpoints. Every intermediate point lies in this cross-section AABB.
        endpoints=(self.selected[None,:,1:3]+
            self.lateral[[0,-1],None,None]*self.selected[None,:,3:5])+self.origin
        self.lower=np.nextafter(endpoints.min(axis=0),-np.inf)
        self.upper=np.nextafter(endpoints.max(axis=0),np.inf)

    def sample(self,xy,clearance_m=12.):
        xy=np.asarray(xy,dtype=float)
        if xy.ndim!=2 or xy.shape[1]!=2 or not np.isfinite(xy).all():
            raise ValueError('Expected finite geographic point pairs')
        if not np.isfinite(clearance_m) or clearance_m<0:
            raise ValueError('Invalid water clearance radius')
        result=np.full(len(xy),float(clearance_m))
        if not len(xy):return result
        # Include the existing conservative cell diagonal, and round the broad
        # phase outward. Only centres outside this box are irrelevant to the
        # eligibility predicate. Nearby distant-station bends remain included.
        radius=np.nextafter(clearance_m+self.diagonal,np.inf)
        lower=np.nextafter(xy.min(axis=0)-radius,-np.inf)
        upper=np.nextafter(xy.max(axis=0)+radius,np.inf)
        columns=np.flatnonzero(((self.upper>=lower)&(self.lower<=upper)).all(axis=1))
        for start in range(0,len(columns),self.columns):
            select=columns[start:start+self.columns]
            points=(self.selected[None,select,1:3]+
                self.lateral[:,None,None]*self.selected[None,select,3:5])+self.origin
            keep=np.asarray(self.wet[:,select],dtype=bool)
            keep&=((points>=lower)&(points<=upper)).all(axis=2)
            if keep.any():
                distances=cKDTree(points[keep]).query(xy)[0]-self.diagonal
                result=np.minimum(result,distances)
        return result
