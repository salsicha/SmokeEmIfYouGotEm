"""Stratified weighted source-site selection for one native spawn batch.

Preserve the number/volume of births and the prescribed weighted distribution.
For a shared uniform offset u, quantiles (i+u)/N yield expected site counts N*p
and each site's realized count differs from N*p by less than one. If N*p_max
<1, a batch cannot select a site twice (subject to explicit numeric checks).
This is a CPU candidate; native wiring/readback is still required. It does not
move source sites, jitter positions, remove coincident water, or alter terrain.
"""
import numpy as np


def cumulative_weights(weights):
    w=np.asarray(weights,float)
    if w.ndim!=1 or not len(w) or not np.isfinite(w).all() or (w<0).any() or w.sum()<=0:
        raise ValueError('Finite nonnegative source weights with positive total required')
    cdf=np.cumsum(w)/w.sum();cdf[-1]=1.
    return cdf


def select_sites(weights,count,offset):
    if (not isinstance(count,int) or isinstance(count,bool) or count<0 or
        not np.isfinite(offset) or not 0<=offset<1):raise ValueError('Nonnegative integral count and shared offset in [0,1) required')
    cdf=cumulative_weights(weights)
    quantiles=(np.arange(count)+offset)/count if count else np.empty(0)
    chosen=np.searchsorted(cdf,quantiles,side='right')
    if (chosen>=len(cdf)).any():raise ValueError('Finite quantile precision escaped the CDF')
    ideal=np.asarray(weights,float)/np.sum(weights)*count;observed=np.bincount(chosen,minlength=len(cdf))
    # Report finite arithmetic honestly; the exact count bound is mathematical,
    # not permission to omit a high-probability site's multiple births.
    return chosen,dict(births=count,maximum_site_count=int(observed.max(initial=0)),
        duplicate_site_births=int(np.maximum(observed-1,0).sum()),
        maximum_count_discrepancy=float(abs(observed-ideal).max(initial=0)),
        maximum_expected_site_count=float(ideal.max(initial=0)),
        mass_or_source_weights_modified=False,native_integrated=False)


def native_sites(weights,sequences,batch_first,batch_count,seed):
    """Match uint32 hash and float32 quantile/CDF arithmetic of native candidate.

    First/count are per actual SpawnInfo group, not the total live population.
    The final min is solely the float32 representation of a half-open quantile;
    no source weight, particle mass or source position is clamped.
    """
    sequences=np.asarray(sequences);first=np.asarray(batch_first);count=np.asarray(batch_count)
    if (sequences.shape!=first.shape or first.shape!=count.shape or sequences.ndim!=1 or
        any(not np.issubdtype(a.dtype,np.integer) for a in (sequences,first,count)) or
        (count<=0).any() or (first<0).any() or (sequences<first).any() or (sequences-first>=count).any() or
        (sequences>0xffffffff).any() or not 0<=seed<=0xffffffff):raise ValueError('Valid uint32 identities and exact native spawn-group bounds required')
    w=np.asarray(weights,float);cumulative_weights(w)
    cdf=(np.cumsum(w)/np.cumsum(w)[-1]).astype('<f4');cdf[-1]=1
    if np.any((w>0)&(np.diff(np.r_[np.float32(0),cdf])<=0)):raise ValueError('Positive source support collapsed in native CDF')
    key=first.astype(np.uint64)^np.uint64(seed);mask=np.uint64(0xffffffff)
    key^=key>>16;key=(key*np.uint64(0x7feb352d))&mask
    key^=key>>15;key=(key*np.uint64(0x846ca68b))&mask;key^=key>>16
    offset=((key>>9).astype('<f4')+np.float32(.5))*np.float32(2**-23)
    q=((sequences-first).astype('<f4')+offset)/count.astype('<f4')
    q=np.minimum(q,np.nextafter(np.float32(1),np.float32(0)))
    chosen=np.searchsorted(cdf,q,side='right')
    if (chosen>=len(w)).any():raise ValueError('Native quantile escaped CDF')
    return chosen
