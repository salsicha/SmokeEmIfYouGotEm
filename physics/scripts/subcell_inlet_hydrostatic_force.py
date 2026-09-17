"""Hydrostatic pressure and original bed force on a conditional inlet profile.

This is an instantaneous momentum-rate contribution (per density), not a
nonhydrostatic/rational pressure closure or a coupled water update. A constant
velocity inlet has a nonzero pressure/bed residual; reporting it is not proof
that constant-velocity advection solves the shallow-water momentum equation.
"""
from fractions import Fraction as F

from subcell_exact_geometry import SourceFragment
from subcell_inlet_sweep_geometry import _cross, polynomial_bounds
from subcell_inlet_face_transport import source_transport_balance


def _linear_bounds(terms):
    lower = upper = F(0)
    for coefficient, lo, hi in terms:
        lower += coefficient*(lo if coefficient >= 0 else hi)
        upper += coefficient*(hi if coefficient >= 0 else lo)
    return lower, upper


def lateral_front_moment(sweep, fragment, relative_bound=F(1, 10**12), max_depth=48, *, include_boundary=False):
    """Bound integral r**4 dr on the s=0 ray STRICTLY INSIDE this source.

    Its h=k*r jump has a distributional pressure gradient. A ray lying on
    a source boundary is not an interior jump: its one-sided trace instead
    belongs to the boundary traction. That is not a qualified wet/dry Riemann
    flux on a shared face, which still requires a physical front law.
    """
    if not 0 < F(relative_bound) < 1 or type(max_depth) is not int or not 1 <= max_depth <= 128:
        raise ValueError('Strict lateral-front integration bound and depth 1..128 required')
    if type(include_boundary) is not bool:
        raise ValueError('Explicit boolean lateral-front boundary inclusion required')
    lower, upper, vertical = sweep._constraints(fragment)
    # At s=0 the original inequalities are -lower>=0, upper>=0, vertical>=0.
    # Remove the two inlet-support inequalities; only source boundaries decide
    # whether the ray is strictly interior. Their identically-zero polynomial
    # means the entire ray is on that source boundary, not an interior front.
    constraints = [tuple(-c for c in p) for p in lower[1:]]+upper[1:]+vertical
    if not include_boundary and any(not any(p) for p in constraints):
        return F(0), F(0)
    constraints = [p for p in constraints if any(p)]
    exact = uncertainty = F(0)
    pending = [(F(0), sweep.time_root, 0)]
    while pending:
        lo, hi, depth = pending.pop()
        ranges = [polynomial_bounds(p, lo, hi) for p in constraints]
        if any(b <= 0 for a, b in ranges):
            continue
        amount = (hi**5-lo**5)/5
        if all(a >= 0 for a, b in ranges):
            exact += amount
        elif depth == max_depth:
            uncertainty += amount
        else:
            mid = (lo+hi)/2
            pending.extend(((lo,mid,depth+1),(mid,hi,depth+1)))
    if uncertainty > F(relative_bound)*sweep.time_root**5/5:
        raise ValueError('Lateral-front integration bound unresolved; no front deletion')
    return exact, exact+uncertainty


def source_hydrostatic_force(sweep, fragment, *, relative_bound=F(1, 10**12), max_depth=48):
    """Bound the hydrostatic interior-trace residual on an original source.

    X=A+sD+u*age, r**3=T-age, h=k*r-B*s. Thus
    grad(h)=-B*grad(s)-k*grad(age)/(3*r**2).
    Include the distributional pressure jump at the finite-depth s=0 front
    when it lies in the source interior. The apparent birth singularity in
    the smooth part cancels the original area Jacobian exactly.
    All force components retain the current non-horizontal support; no water
    is relocated to a source minimum and no small time/depth is substituted.
    """
    if not isinstance(fragment, SourceFragment) or fragment.area <= 0 or len(fragment.gradient) != 2:
        raise ValueError('Original affine bed gradient required')
    gradient = tuple(F(v) for v in fragment.gradient)
    anchor = fragment.polygon[0]
    if any(F(p[2])-F(anchor[2]) != sum(gradient[j]*(F(p[j])-F(anchor[j])) for j in range(2))
           for p in fragment.polygon):
        raise ValueError('Original source bed gradient and vertices disagree')
    # Also rejects an upstream donor misidentified as an empty receiver and
    # a source with an unaccounted inlet birth segment in its interior.
    balance = source_transport_balance(sweep, fragment, relative_bound=relative_bound, max_depth=max_depth)
    storage = balance['storage']
    weighted = sweep._constraint_moments(*sweep._constraints(fragment), relative_bound, max_depth,
                                        radial_power=0)
    volume = storage['lower'][1], storage['upper'][1]
    weighted_volume = weighted['lower'][1], weighted['upper'][1]
    lateral = lateral_front_moment(sweep, fragment, relative_bound, max_depth)
    lateral_closure = lateral_front_moment(sweep, fragment, relative_bound, max_depth, include_boundary=True)
    determinant = _cross(sweep.delta, sweep.velocity)
    grad_s = sweep.velocity[1]/determinant, -sweep.velocity[0]/determinant
    grad_age = -sweep.delta[1]/determinant, sweep.delta[0]/determinant
    smooth, curtain, pressure, bed, combined = [], [], [], [], []
    for j in range(2):
        pressure_coefficient = sweep.gravity*sweep.bed_span*grad_s[j]
        birth_coefficient = sweep.gravity*sweep.height_scale*grad_age[j]/3
        bed_coefficient = -sweep.gravity*gradient[j]
        jump_coefficient = -3*sweep.gravity*sweep.jacobian*sweep.height_scale**2*grad_s[j]/2
        smooth.append(_linear_bounds(((pressure_coefficient, *volume), (birth_coefficient, *weighted_volume))))
        curtain.append(_linear_bounds(((jump_coefficient, *lateral),)))
        pressure.append(_linear_bounds(((pressure_coefficient, *volume), (birth_coefficient, *weighted_volume),
                                        (jump_coefficient, *lateral))))
        bed.append(_linear_bounds(((bed_coefficient, *volume),)))
        # These contributions share the SAME volume: combine its coefficients
        # before bounding, retaining exact pressure/bed cancellation.
        combined.append(_linear_bounds(((pressure_coefficient+bed_coefficient, *volume),
                                        (birth_coefficient, *weighted_volume), (jump_coefficient, *lateral))))
    work = _linear_bounds(tuple((sweep.velocity[j], *combined[j]) for j in range(2)))
    return dict(source_id=fragment.source_id, original_gradient=gradient,
                time_seconds=sweep.time_root**3, volume_bounds=volume,
                pressure_weighted_volume_bounds=weighted_volume,
                smooth_pressure_force_per_density_bounds=tuple(smooth),
                interior_lateral_front_radial_moment_bounds=lateral,
                closed_lateral_front_radial_moment_bounds=lateral_closure,
                positive_depth_lateral_front_proven=lateral_closure[0] > 0,
                positive_depth_lateral_front_on_source_boundary_proven=lateral_closure[0] > 0 and lateral[1] == 0,
                lateral_front_pressure_jump_per_density_bounds=tuple(curtain),
                pressure_force_per_density_bounds=tuple(pressure),
                bed_force_per_density_bounds=tuple(bed),
                combined_force_per_density_bounds=tuple(combined),
                velocity_dot_force_per_density_bounds=work,
                force_units='m^4/s^2; multiply by density for newtons',
                pressure_weighted_moment_relative_width=max(
                    (weighted['upper'][p]-weighted['lower'][p])/sweep.full_moment(p, radial_power=0)
                    for p in range(4)),
                conditional_advective_balance_bounded=balance['conditional_advective_balance_bounded'],
                hydrostatic_force_bounded=True,
                wet_dry_riemann_flux_or_lateral_fan_accepted=False,
                force_scope='Hydrostatic interior-trace spatial residual of the conditional profile, including interior finite-depth front jumps. Not a common numerical flux or accepted momentum update at discontinuous shared faces.',
                nonhydrostatic_or_curvature_or_coupled_time_or_gameplay_accepted=False)
