"""Limited BFECC interface transport, as described by Selle et al. (2008).

Uses the existing RK2 traces and velocity basis in both directions. New extrema
are limited to the contributing original donor range; cells without a complete round-trip
owned stencil or touching caller-specified solid also use first order. Neither
invalid forward traces nor lost volume are hidden by the accuracy fallback.
No marker movement, scalar reset, authored waves or guaranteed volume claim.
"""
from itertools import product
import numpy as np
from liquid_interface_transport import advect


def advect_limited(phi,velocity,spacing,dt,minimum,maximum,compact=False,*,solid=None):
    p=np.asarray(phi,float);v=np.asarray(velocity,float);h=np.asarray(spacing,float)
    forward,a=advect(p,v,h,dt,minimum,maximum,compact,details=True)
    reverse,b=advect(forward,-v,h,dt,minimum,maximum,compact,details=True)
    solid=np.zeros(p.shape,bool) if solid is None else np.asarray(solid)
    if solid.shape!=p.shape or solid.dtype!=bool:raise ValueError('Matching explicit boolean solid mask required')
    ids=a['indices'];key=tuple(ids[:,::-1].T)
    forward_valid=np.zeros(p.shape,bool);forward_valid[key]=a['valid_mask']
    roundtrip=a['valid_mask']&b['valid_mask']&~solid[key]
    low=np.floor(a['traced_points']/h-.5).astype(int)
    backlow=np.floor(b['traced_points']/h-.5).astype(int)
    fraction=a['traced_points']/h-.5-low;backfraction=b['traced_points']/h-.5-backlow
    minimum=np.asarray(minimum);maximum=np.asarray(maximum);size=np.array(p.shape[::-1])
    # Correct the source BEFORE the third advection (BFECC). Correcting the
    # already-forward value (MacCormack) failed our moving-crest accuracy gate.
    for offset in product((0,1),repeat=3):
        used=np.prod(np.where(offset,backfraction,1-backfraction),axis=1)>0
        donor=backlow+offset;valid=((donor>=minimum)&(donor<maximum)).all(1)
        roundtrip&=valid|~used
        rows=np.flatnonzero(valid&used);dk=tuple(donor[rows,::-1].T)
        roundtrip[rows]&=forward_valid[dk]&~solid[dk]
    source_ready=np.zeros(p.shape,bool);source_ready[key]=roundtrip
    corrected=p.copy();chosen=ids[roundtrip];ck=tuple(chosen[:,::-1].T)
    corrected[ck]=p[ck]+.5*(p[ck]-reverse[ck])
    transported,c=advect(corrected,v,h,dt,minimum,maximum,compact)
    ready=a['valid_mask']&~solid[key]
    donor_min=np.full(len(ids),np.inf);donor_max=np.full(len(ids),-np.inf)
    for offset in product((0,1),repeat=3):
        # Zero-weight corners do not contribute to either characteristic.
        # Including them can admit new extrema in an orthogonal direction,
        # e.g. a vertical level-set gradient during pure horizontal transport.
        used=np.prod(np.where(offset,fraction,1-fraction),axis=1)>0
        donor=low+offset
        valid=((donor>=0)&(donor<size)).all(1)
        rows=np.flatnonzero(valid&used);dk=tuple(donor[rows,::-1].T)
        donor_min[rows]=np.minimum(donor_min[rows],p[dk]);donor_max[rows]=np.maximum(donor_max[rows],p[dk])
        ready[rows]&=~solid[dk]&source_ready[dk];ready&=valid|~used
    candidate=transported[key]
    extrema=(candidate<donor_min)|(candidate>donor_max)
    use=ready&np.isfinite(candidate);output=forward.copy();chosen=ids[use]
    output[tuple(chosen[:,::-1].T)]=np.minimum(np.maximum(candidate[use],donor_min[use]),donor_max[use])
    return output,dict(candidate_step_valid=a['candidate_step_valid'] and c['candidate_step_valid'],updated_cells=a['updated_cells'],
        rejected_forward_trace_cells=a['rejected_trace_cells'],second_order_cells=int(use.sum()),
        extrema_limited_cells=int((use&extrema).sum()),
        boundary_or_incomplete_roundtrip_reverted_cells=int((a['valid_mask']&~ready).sum()),
        reverse_trace_failures=int(b['rejected_trace_cells']),
        method='limited-bfecc-rk2',source_or_particle_modified=False,volume_conservation_proven=False,native_integrated=False)
