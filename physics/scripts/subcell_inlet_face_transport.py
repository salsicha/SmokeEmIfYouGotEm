"""Conservative advective fluxes of the conditional inlet's actual profile.

Integrate parcel crossings of ORIGINAL source edges from birth to R**3.
Depth is k*r-B*s, not a receiving-cell stage. Each parcel crosses a straight
face at most once under the conditional constant velocity. No pressure,
terrain potential-energy update, fan continuation or playable step is implied.
"""
from dataclasses import replace
from fractions import Fraction as F

from subcell_inlet_sweep_geometry import _cross


def face_transport(sweep, fragment, edge_index, *, relative_bound=F(1, 10**12), max_depth=48):
    """Bounds on integral(dt integral(face) h**p u.n dl), p=0..3.

    Positive means outward from this original convex source. Shared faces
    have exactly opposite bounds. Birth crossings at the original inlet are
    included: their inflow must be debited from the donor by a coupled update.
    """
    sweep._constraints(fragment)  # Validate the actual source polygon.
    if type(edge_index) is not int or not 0 <= edge_index < len(fragment.polygon):
        raise ValueError('Original source edge index required')
    a, b = fragment.polygon[edge_index], fragment.polygon[(edge_index+1) % len(fragment.polygon)]
    edge = tuple(F(b[j])-F(a[j]) for j in range(2))
    if edge == (0, 0):
        raise ValueError('Positive original source edge required')
    determinant = _cross(sweep.velocity, edge)
    orientation = sum((_cross(p, q) for p, q in
                       zip(fragment.polygon, fragment.polygon[1:]+fragment.polygon[:1])), F(0))
    direction = 0 if determinant == 0 else (1 if determinant*orientation > 0 else -1)
    lower, upper, vertical = [(F(0),)], [(F(0), sweep.height_scale/sweep.bed_span)], []
    if direction:
        offset = tuple(F(a[j])-sweep.edge[0][j] for j in range(2))
        # Crossing age alpha(s) and face fraction lambda(s), directly from
        # A+sD+u*alpha = a+lambda*edge. Their coefficients remain rational.
        alpha = (_cross(offset, edge)/determinant, -_cross(sweep.delta, edge)/determinant)
        lam = (_cross(offset, sweep.velocity)/determinant,
               -_cross(sweep.delta, sweep.velocity)/determinant)

        def constrain(coefficient, polynomial):
            # polynomial(r)+coefficient*s >= 0.
            if coefficient > 0:
                lower.append(tuple(-x/coefficient for x in polynomial))
            elif coefficient < 0:
                upper.append(tuple(-x/coefficient for x in polynomial))
            else:
                vertical.append(polynomial)

        constrain(alpha[1], (alpha[0],))                 # crossing is after entry
        constrain(lam[1], (lam[0],))                     # lambda >= 0
        constrain(-lam[1], (1-lam[0],))                  # lambda <= 1
        constrain(-alpha[1], (sweep.time_root**3-alpha[0], F(0), F(0), F(-1)))
        result = sweep._constraint_moments(lower, upper, vertical, relative_bound, max_depth)
    else:
        # Exactly tangent velocity has zero flux, regardless of wet area.
        # Still validate integration controls through the same bounded API.
        result = sweep._constraint_moments(lower, upper, [(F(-1),)], relative_bound, max_depth)
    signed_lower, signed_upper = result['lower'], result['upper']
    if direction < 0:
        signed_lower, signed_upper = tuple(-x for x in signed_upper), tuple(-x for x in signed_lower)
    return dict(source_id=fragment.source_id, original_edge_xyz=(a, b),
                time_seconds=sweep.time_root**3, outward_direction=direction,
                lower=signed_lower, upper=signed_upper,
                intervals_visited=result['intervals_visited'],
                bounded_switch_intervals=result['bounded_switch_intervals'],
                pressure_or_bed_force_or_coupled_step_accepted=False)


def source_transport_balance(sweep, fragment, *, birth_donor=False,
                             relative_bound=F(1, 10**12), max_depth=48):
    """Compare incoming-minus-outgoing flux to independently clipped storage.

    For receiver/downstream sources with no inlet birth segment in their
    interior. An explicitly identified original birth donor has a withdrawal,
    not newborn storage. Its full incoming stream is debited once, after
    checking that the original inlet is its boundary and velocity exits it.
    A non-closing balance raises rather than redistributing its discrepancy.
    """
    if type(birth_donor) is not bool:
        raise ValueError('Explicit boolean original birth-donor role required')
    if birth_donor:
        replace(sweep, velocity=tuple(-v for v in sweep.velocity)).validate_receiver(fragment)
    withdrawal = tuple(sweep.full_moment(p) if birth_donor else F(0) for p in range(4))
    storage = sweep.moments(fragment, relative_bound, max_depth)
    faces = [face_transport(sweep, fragment, i, relative_bound=relative_bound, max_depth=max_depth)
             for i in range(len(fragment.polygon))]
    change_lower = tuple(storage['lower'][p]-withdrawal[p] for p in range(4))
    change_upper = tuple(storage['upper'][p]-withdrawal[p] for p in range(4))
    lower = tuple(change_lower[p]+sum(f['lower'][p] for f in faces) for p in range(4))
    upper = tuple(change_upper[p]+sum(f['upper'][p] for f in faces) for p in range(4))
    if any(not lo <= 0 <= hi for lo, hi in zip(lower, upper)):
        raise ValueError('Original source transport balance does not close; no residual redistribution')
    return dict(source_id=fragment.source_id, storage=storage, faces=faces,
                birth_donor=birth_donor, original_inlet_withdrawal=withdrawal,
                advected_moment_change_lower=change_lower, advected_moment_change_upper=change_upper,
                balance_lower=lower, balance_upper=upper,
                maximum_relative_balance_width=max((hi-lo)/sweep.full_moment(p)
                                                  for p, (lo, hi) in enumerate(zip(lower, upper))),
                conditional_advective_balance_bounded=True,
                pressure_or_bed_force_or_coupled_step_accepted=False)
