"""Bounded Manning construction on the actual guarded, quantized triangle bed.

This is a geometry-aware construction hypothesis, never a hydraulic solve.
Every fitted constraint also reaches the geographic stations of its triangle
vertices and protection probes; a numerical row cannot silently own a bend.
"""
import numpy as np
import shapely

from chilko_triangle_ownership import POLICY, support_offsets
from export_colorado_continuous_terrain import SPACING, HEIGHT_BASE, HEIGHT_RANGE


def capacity_grid(origin):
    origin=np.asarray(origin,dtype=float)
    if origin.shape!=(2,) or not np.isfinite(origin).all():
        raise ValueError('Explicit finite canonical terrain origin required')
    return dict(horizontal_origin_m=origin.tolist(),spacing_m=SPACING,
        height_base_m=HEIGHT_BASE,height_range_m=HEIGHT_RANGE,encoding='uint16_nearest',
        diagonal='SE_to_NW_in_east_north_grid',support_policy=POLICY)


def validate_capacity_grid(receipt,origin):
    if receipt!=capacity_grid(origin):
        raise ValueError('Encoded capacity requires the identical canonical terrain grid and guard')


def triangle_stencil(xy, origin):
    xy,origin=np.asarray(xy,dtype=float),np.asarray(origin,dtype=float)
    if xy.ndim!=3 or xy.shape[-1]!=2 or origin.shape!=(2,) or not np.isfinite(xy).all() or not np.isfinite(origin).all():
        raise ValueError('Finite row/lateral geographic queries and common grid origin required')
    grid=(xy-origin)/SPACING;cell=np.floor(grid).astype(np.int64);f=grid-cell
    lower=f[...,0]+f[...,1]<=1
    offsets=np.where(lower[...,None,None],np.array([[0,0],[1,0],[0,1]]),np.array([[1,1],[0,1],[1,0]]))
    lattice=cell[...,None,:]+offsets
    weights=np.where(lower[...,None],np.stack((1-f.sum(-1),f[...,0],f[...,1]),-1),
                     np.stack((f.sum(-1)-1,1-f[...,0],1-f[...,1]),-1))
    nodes,inverse=np.unique(lattice.reshape(-1,2),axis=0,return_inverse=True)
    return origin+nodes*SPACING,inverse.reshape(xy.shape[:-1]+(3,)),weights


def parameters(model, xy):
    r=model.sample(xy)
    ground=np.asarray(r['source_height_m']);stage=np.asarray(r['reference_m'])
    mapped=np.asarray(r['mapped_water'])
    if ground.shape!=xy.shape[:-1] or not np.isfinite(ground).all() or mapped.dtype.kind!='b':
        raise ValueError('Incomplete source terrain')
    eligible=mapped&(ground<=r['ownership_reference_m']+.25)
    shape=np.zeros(ground.shape);station=np.full(ground.shape,np.nan)
    if mapped.any():
        points=shapely.points(xy[mapped]);s=shapely.line_locate_point(model.line,points)
        station[mapped]=s
        width=np.interp(s,model.station,model.width)
        shape[mapped]=np.sqrt(np.clip(2*shapely.distance(points,model.polygon.boundary)/width,0,1))
    if not np.isfinite(stage[eligible]).all() or not np.isfinite(shape[eligible]).all():
        raise ValueError('Missing owned source reference')
    return ground,stage,shape,station,eligible


def inference_threshold(ground,stage,shape,eligible):
    """Exact strict amplitude threshold for the existing source lowering rule."""
    threshold=np.full(ground.shape,np.inf)
    minimum=eligible&((stage-ground)<.05)
    threshold[minimum]=-np.inf
    variable=eligible&~minimum&(shape>0)
    threshold[variable]=(stage[variable]-ground[variable])/shape[variable]
    return threshold


class EncodedSections:
    def __init__(self,model,xy,origin,slope,spacing=1.):
        self.xy=np.asarray(xy,dtype=float);self.slope=np.asarray(slope,dtype=float);self.spacing=float(spacing)
        if (self.xy.ndim!=3 or self.slope.shape!=(len(self.xy),) or not np.isfinite(self.slope).all()
                or np.any(self.slope<=0) or not np.isfinite(spacing) or spacing<=0):
            raise ValueError('Positive finite section slopes and quadrature spacing required')
        self.nodes,self.indices,self.weights=triangle_stencil(self.xy,origin)
        self.ground,self.stage,self.shape,self.station,eligible=parameters(model,self.nodes)
        _,self.query_stage,_,_,self.query_owned=parameters(model,self.xy)
        if not self.query_owned.any(axis=1).all():raise ValueError('No source-owned channel at a section')
        self.threshold=inference_threshold(self.ground,self.stage,self.shape,eligible)
        offsets=support_offsets();self.probe_station=np.full((len(self.nodes),len(offsets)),np.nan)
        selected=np.flatnonzero(eligible)
        for start in range(0,len(selected),1024):
            ids=selected[start:start+1024];q=self.nodes[ids,None,:]+offsets[None,:,:]
            ground,stage,shape,station,owned=parameters(model,q)
            self.threshold[ids]=np.maximum(self.threshold[ids],inference_threshold(ground,stage,shape,owned).max(axis=1))
            self.probe_station[ids]=station
        if np.any(self.ground<HEIGHT_BASE) or np.any(self.ground>HEIGHT_BASE+HEIGHT_RANGE):
            raise ValueError('Source outside common Landscape height encoding')

    def vertex_heights(self,amplitude):
        amplitude=np.asarray(amplitude,dtype=float)
        if amplitude.shape!=(len(self.xy),) or not np.isfinite(amplitude).all() or np.any(amplitude<=0) or np.any(amplitude>10):
            raise ValueError('One bounded amplitude per row required')
        ids=self.indices;a=amplitude[:,None,None]
        proposed=np.minimum(self.ground[ids],self.stage[ids]-np.maximum(a*self.shape[ids],.05))
        height=np.where(a>self.threshold[ids],proposed,self.ground[ids])
        if not np.isfinite(height).all() or np.any(height<HEIGHT_BASE) or np.any(height>HEIGHT_BASE+HEIGHT_RANGE):
            raise ValueError('Inferred bed outside common Landscape encoding')
        return HEIGHT_BASE+np.rint((height-HEIGHT_BASE)*65535/HEIGHT_RANGE)*HEIGHT_RANGE/65535

    def capacity(self,amplitude,roughness):
        if not np.isfinite(roughness) or not .02<=roughness<=.1:raise ValueError('Bounded inferred Manning n required')
        bed=np.sum(self.vertex_heights(amplitude)*self.weights,axis=-1)
        depth=np.where(self.query_owned,np.maximum(self.query_stage-bed,0),0)
        return np.sum(depth**(5/3),axis=1)*self.spacing*np.sqrt(self.slope)/roughness

    def fit(self,discharge=45.,roughness=.045):
        if not np.isfinite(discharge) or not 0<discharge<=500:raise ValueError('Bounded positive construction discharge required')
        lo=np.full(len(self.xy),.05);hi=np.full(len(self.xy),10.)
        initial=self.capacity(lo,roughness);maximum=self.capacity(hi,roughness)
        failed=np.flatnonzero(maximum<discharge)
        if len(failed):raise ValueError('Protected encoded sections exceed 10 m amplitude bound: '+str(failed.tolist()))
        active=initial<discharge
        for _ in range(40):
            mid=(lo+hi)/2;below=self.capacity(mid,roughness)<discharge
            lo=np.where(active&below,mid,lo);hi=np.where(active&~below,mid,hi)
        fitted=np.where(active,hi,.05)
        return fitted,initial,self.capacity(fitted,roughness)

    def apply_geographic_envelope(self,model,depth,amplitude):
        from build_chilko_corridor_depth import constrain_source_amplitude
        # Every contributing vertex must retain its cut under the final varying
        # depth profile, so constrain its 37 support probes as well as itself.
        self.vertex_heights(amplitude) # validate bounded row amplitudes first
        required=np.zeros(len(self.nodes))
        values=np.broadcast_to(np.asarray(amplitude)[:,None,None],self.indices.shape)
        active=(self.weights>0)&(values>self.threshold[self.indices])
        np.maximum.at(required,self.indices[active],values[active])
        ids=np.flatnonzero(required>0)
        if not len(ids):return depth
        s=np.c_[self.station[ids],self.probe_station[ids]]
        a=np.broadcast_to(required[ids,None],s.shape)
        if not np.isfinite(s).all():raise ValueError('A retained cut has missing geographic support')
        return constrain_source_amplitude(model.station,depth,s.ravel(),a.ravel())
