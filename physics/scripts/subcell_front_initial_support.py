"""Initial water traces on a conditional front, not a time-evolved Riemann state.

Terrain ownership and initial pool ownership are separate. A known dry source
is explicit None; an absent state is unknown. Stage/bed crossings are exact in
entry time, including positive intervals too small for floating-point export.
"""
from fractions import Fraction as F

from subcell_inlet_front_ownership import _exact_fragments, _bed, front_ownership


def initial_front_support(sweep, fragments, states):
    """Partition original wet support on BOTH traces of the same entire ray.

    states maps source keys to None (known initially dry) or a record containing
    pool_id, stage_offset and datum. A pool's source membership alone never
    establishes positive depth. No interpolation across pool/source boundaries.
    Endpoint contact has zero line measure; a whole zero-depth trace is retained.
    """
    fragments = _exact_fragments(fragments)
    if not set(states).issubset(fragments):
        raise ValueError('Initial water state requires its original source geometry')
    prepared = {}
    for key, state in states.items():
        if state is None:
            prepared[key] = None
            continue
        try:
            stage = F(state['datum'])+F(state['stage_offset'])
            pool = state['pool_id']
        except (KeyError, TypeError, ValueError, OverflowError) as exc:
            raise ValueError('Finite exact stage and explicit pool id required') from exc
        if pool is None:
            raise ValueError('Explicit wet pool id required')
        prepared[key] = (pool, stage)

    result = []
    for source_segment in front_ownership(sweep, fragments):
        lo, hi = source_segment['entry_time_interval']
        cuts = {lo, hi}
        for side in ('wet_source', 'dry_source'):
            key = source_segment[side]
            if key not in prepared or prepared[key] is None:
                continue
            stage = prepared[key][1]
            h0, h1 = (stage-_bed(sweep, fragments[key], t) for t in (lo, hi))
            if h0*h1 < 0:
                cuts.add(lo+(hi-lo)*h0/(h0-h1))
        cuts = sorted(cuts)
        for a, b in zip(cuts, cuts[1:]):
            row = dict(entry_time_interval=(a, b))
            for side in ('wet_source', 'dry_source'):
                key = source_segment[side]
                trace = dict(source=key, pool_id=None, stage=None, depth_endpoints=None)
                if key not in prepared:
                    trace['status'] = 'unknown'
                elif prepared[key] is None:
                    trace['status'] = 'initially-dry'
                else:
                    pool, stage = prepared[key]
                    depths = tuple(stage-_bed(sweep, fragments[key], t) for t in (a, b))
                    middle = sum(depths)/2
                    trace.update(pool_id=pool, stage=stage, depth_endpoints=depths,
                                 status=('positive-depth' if middle > 0 else
                                         'initially-dry' if middle < 0 else 'zero-depth-trace'))
                row[side] = trace
            row['initially_dry_on_both_traces'] = all(
                row[side]['status'] in ('initially-dry', 'zero-depth-trace')
                for side in ('wet_source', 'dry_source'))
            result.append(row)
    return dict(segments=result,
                complete_initial_state=all(r[s]['status'] != 'unknown' for r in result
                                           for s in ('wet_source', 'dry_source')),
                positive_initial_depth_present=any(r[s]['status'] == 'positive-depth' for r in result
                                                  for s in ('wet_source', 'dry_source')),
                evolving_front_or_flux_or_time_accepted=False)


def require_initially_dry_front(report):
    """Guard only this necessary condition; passing is NOT flux qualification."""
    if not report['segments'] or not all(r['initially_dry_on_both_traces'] for r in report['segments']):
        raise ValueError('Dry-front law requires known initially dry support on both traces')


def initially_dry_front_transfers(sweep, fragments, states, **integration):
    """Common conditional rates only after validating original dry support.

    The original instantaneous law is unchanged. This guards its initial-state
    prerequisite, not donor depletion or a finite-time/multi-stream solution.
    """
    from subcell_inlet_front_ownership import owned_front_transfers
    support = initial_front_support(sweep, fragments, states)
    require_initially_dry_front(support)
    return dict(owned_front_transfers(sweep, fragments, **integration),
                initial_support=support, initial_dry_support_verified=True)
