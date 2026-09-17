"""Own each conditional side-front segment once on original affine sources.

The straight ray is X(tau)=A+u*(T-tau), tau=r**3 in [0,T]. Source crossings
are rational in tau, even when their r coordinates are irrational. Infinitesimal
+/- inlet-edge directions distinguish the wet/dry trace without an epsilon.
This is source ownership of ONE conditional stream, not ownership of evolving
wet pools, a multi-stream Riemann solution, or a conservative time integrator.
"""
from dataclasses import replace
from fractions import Fraction as F

from subcell_exact_geometry import SourceFragment, clip
from subcell_inlet_sweep_geometry import _cross
from subcell_inlet_lateral_flux import lateral_flux
from subcell_inlet_lateral_energy import lateral_energy_flux


def _exact_fragments(fragments):
    result = {}
    for key,fragment in fragments.items():
        if (not isinstance(fragment,SourceFragment) or len(fragment.gradient)!=2
                or len(fragment.polygon)<3 or any(len(p)!=3 for p in fragment.polygon)):
            raise ValueError('Positive original affine source required')
        result[key] = replace(fragment,polygon=tuple(tuple(F(x) for x in p) for p in fragment.polygon),
                              gradient=tuple(F(g) for g in fragment.gradient))
    return result


def _source_interval(sweep, fragment):
    if not isinstance(fragment, SourceFragment) or len(fragment.gradient) != 2 or fragment.area <= 0:
        raise ValueError('Positive original affine source required')
    polygon = fragment.polygon
    anchor = polygon[0]
    if any(p[2]-anchor[2] != sum(g*(p[j]-anchor[j]) for j,g in enumerate(fragment.gradient))
           for p in polygon):
        raise ValueError('Original source gradient and vertices disagree')
    orientation = sum(_cross(a,b) for a,b in zip(polygon,polygon[1:]+polygon[:1]))
    if not orientation:
        raise ValueError('Nondegenerate convex original source required')
    sign = 1 if orientation > 0 else -1
    edges = [(a,(b[0]-a[0],b[1]-a[1])) for a,b in zip(polygon,polygon[1:]+polygon[:1])]
    if any(sign*_cross(edge,(p[0]-a[0],p[1]-a[1])) < 0 for a,edge in edges for p in polygon):
        raise ValueError('Convex original source required')
    start = tuple(sweep.edge[0][j]+sweep.velocity[j]*sweep.time_root**3 for j in range(2))
    lo, hi, wet, dry = F(0), sweep.time_root**3, True, True
    for a,edge in edges:
        if edge == (0,0):
            continue  # Exact repeated vertices have no independent half-plane.
        c = sign*_cross(edge,(start[0]-a[0],start[1]-a[1]))
        d = -sign*_cross(edge,sweep.velocity)
        if d > 0:
            lo = max(lo,-c/d)
        elif d < 0:
            hi = min(hi,-c/d)
        elif c < 0:
            return None
        elif c == 0:
            side = sign*_cross(edge,sweep.delta)
            wet &= side >= 0
            dry &= side <= 0
    return (lo,hi,wet,dry) if lo < hi else None


def _bed(sweep, fragment, tau):
    xy = tuple(sweep.edge[0][j]+sweep.velocity[j]*(sweep.time_root**3-tau) for j in range(2))
    anchor = fragment.polygon[0]
    return anchor[2]+sum(g*(xy[j]-anchor[j]) for j,g in enumerate(fragment.gradient))


def front_ownership(sweep, fragments):
    """Partition the entire ray; retain missing owners and reject overlap.

    fragments maps stable source keys (e.g. parent/source pairs) to ORIGINAL
    fragments. An internal front may have the same source on both sides, but
    those remain distinct conditional wet/dry domains. Positive-width source
    overlap is an error, never resolved by choosing a key or input order.
    Zero-length endpoint contacts carry no line flux and are not segments.
    """
    if None in fragments:
        raise ValueError('None is reserved for missing source ownership')
    fragments = _exact_fragments(fragments)
    intervals = {key:value for key,fragment in fragments.items()
                 if (value := _source_interval(sweep,fragment)) is not None}
    cuts = sorted({F(0),sweep.time_root**3} | {v for interval in intervals.values() for v in interval[:2]})
    segments = []
    for lo,hi in zip(cuts,cuts[1:]):
        middle = (lo+hi)/2
        owners = []
        for side in (2,3):
            candidates = [key for key,(a,b,wet,dry) in intervals.items()
                          if a < middle < b and (wet if side == 2 else dry)]
            if len(candidates) > 1:
                raise ValueError('Overlapping original sources on one side of a positive front segment')
            owners.append(candidates[0] if candidates else None)
        wet,dry = owners
        if wet is not None and dry is not None:
            if any(_bed(sweep,fragments[wet],t) != _bed(sweep,fragments[dry],t) for t in (lo,hi)):
                raise ValueError('Two original bed traces disagree on the shared front')
        segments.append(dict(entry_time_interval=(lo,hi), wet_source=wet, dry_source=dry))
    return tuple(segments)


def owned_front_transfers(sweep, fragments, *, energy_datum=F(0), **integration):
    """One common mass/momentum/energy rate and two references per segment.

    Debit and credit refer to the SAME transfer id, not independently evaluated
    fluxes. Missing source endpoints remain explicit external/unresolved entries.
    No flux is manufactured across a segment with no original bed on either
    side. Existing interval integrators retain their unchanged error gates.
    """
    fragments = _exact_fragments(fragments)
    segments = front_ownership(sweep,fragments)
    axis = 0 if abs(sweep.velocity[0]) >= abs(sweep.velocity[1]) else 1
    transfers = []
    for transfer_id,segment in enumerate(segments):
        lo,hi = segment['entry_time_interval']
        wet,dry = segment['wet_source'],segment['dry_source']
        selected = wet if wet is not None else dry
        row = dict(segment, transfer_id=transfer_id,
                   debit=dict(transfer_id=transfer_id,sign=-1,source=wet,domain='conditional-wet-side'),
                   credit=dict(transfer_id=transfer_id,sign=1,source=dry,domain='conditional-dry-side'))
        if selected is None:
            row.update(status='missing-both-original-bed-traces', common_rate_bounds=None)
        else:
            fragment = fragments[selected]
            bounds = sorted(sweep.edge[0][axis]+sweep.velocity[axis]*(sweep.time_root**3-t) for t in (lo,hi))
            polygon = clip(clip(fragment.polygon,axis,bounds[0],True),axis,bounds[1],False)
            restricted = replace(fragment,polygon=polygon)
            mass_momentum = lateral_flux(sweep,restricted,**integration)
            energy = lateral_energy_flux(sweep,restricted,energy_datum=energy_datum,**integration)
            if energy['outward_volume_rate_bounds'] != mass_momentum['outward_volume_momentum_rate_bounds'][0]:
                raise ValueError('Common mass and energy fluxes use different front measures')
            row.update(status='paired-original-sources' if wet is not None and dry is not None
                       else 'missing-one-original-source',
                       common_rate_bounds=(*mass_momentum['outward_volume_momentum_rate_bounds'],
                                           energy['outward_energy_rate_per_density_bounds']),
                       flux_source=selected,
                       maximum_relative_mass_width=mass_momentum['maximum_relative_mass_width'],
                       maximum_scaled_energy_width=energy['maximum_scaled_energy_width'])
        transfers.append(row)
    return dict(transfers=transfers, energy_datum=F(energy_datum),
                complete_original_source_ownership=all(t['status']=='paired-original-sources' for t in transfers),
                full_entry_time_interval=(F(0),sweep.time_root**3),
                single_stream_front_partition_exact=True,
                coupled_time_or_energy_or_native_or_gameplay_accepted=False,
                scope='One conditional stream only. Wet/dry labels denote its two traces, not actual evolving pool ownership. Common rate references do not prove donor depletion, finite-time, multi-stream, bed or dispersive energy conservation.')
