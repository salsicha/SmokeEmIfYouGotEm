"""Common local hydrostatic dry-front flux on a conditional inlet's side ray.

The ray s=0 has h=k*r, zero normal velocity and tangent velocity u. The
homogeneous entropy rarefaction gives h*=4*h/9 and un*=2*sqrt(g*h)/3 at
the original interface. Hence q=8*h*sqrt(g*h)/27 and pn=8*g*h*h/27.
This is the zero-normal branch of subcell_dry_front_flux, not a new closure.
It is a LOCAL instantaneous flux, not a finite-time two-dimensional fan,
energy update, dispersive pressure closure or accepted gameplay integration.
"""
from fractions import Fraction as F

from subcell_inlet_contact_time import _sqrt_bounds
from subcell_inlet_hydrostatic_force import lateral_front_intervals, _linear_bounds
from subcell_inlet_sweep_geometry import _cross


def lateral_flux(sweep, fragment, *, relative_bound=F(1, 10**12), max_depth=48, root_bits=128):
    """Bound outward (volume, XY momentum) rates on the closed original ray.

    dl=3*|u|*r**2 dr. A mass primitive is
    16*k/81*sqrt(g*k*|u|**2*r**9). In the normal momentum primitive,
    |u| cancels the unit-normal denominator exactly. Radicals and source
    crossings have rational enclosures; positive sub-float flux is retained.
    Shared-boundary queries return the SAME oriented flux on both sides:
    callers must own it once and use its negative for the wet-side debit.
    No pool is mutated and no source-boundary ownership is inferred here.
    """
    if type(root_bits) is not int or not 16 <= root_bits <= 4096:
        raise ValueError('Lateral flux requires 16..4096 exact root bits')
    inside, unresolved = lateral_front_intervals(sweep, fragment, relative_bound, max_depth,
                                                include_boundary=True)
    k, g = sweep.height_scale, sweep.gravity
    speed_squared = sum(v*v for v in sweep.velocity)
    factor = F(16, 81)*k

    def primitive(r):
        return tuple(factor*x for x in _sqrt_bounds(g*k*speed_squared*r**9, root_bits))

    def mass_interval(lo, hi):
        a, b = primitive(lo), primitive(hi)
        return max(F(0), b[0]-a[1]), b[1]-a[0]

    mass_lo = mass_hi = radial_lo = radial_hi = F(0)
    for intervals, proven in ((inside, True), (unresolved, False)):
        for lo, hi in intervals:
            a, b = mass_interval(lo, hi)
            radial = (hi**5-lo**5)/5
            mass_lo += a if proven else 0
            mass_hi += b
            radial_lo += radial if proven else 0
            radial_hi += radial
    full_mass = primitive(sweep.time_root)
    if (mass_hi-mass_lo > F(relative_bound)*full_mass[0]
            or radial_hi-radial_lo > F(relative_bound)*sweep.time_root**5/5):
        raise ValueError('Lateral flux bound unresolved; no guessed flux or front deletion')
    sign = 1 if _cross(sweep.delta, sweep.velocity) > 0 else -1
    # Outward from s>=0 is -grad(s)/|grad(s)|.
    normal_times_speed = (-sign*sweep.velocity[1], sign*sweep.velocity[0])
    normal = tuple(_linear_bounds(((F(8,9)*g*k*k*v, radial_lo, radial_hi),))
                   for v in normal_times_speed)
    momentum = tuple(_linear_bounds(((u, mass_lo, mass_hi), (F(1), *pn)))
                     for u, pn in zip(sweep.velocity, normal))
    flux = ((mass_lo, mass_hi), *momentum)
    return dict(source_id=fragment.source_id, time_seconds=sweep.time_root**3,
                outward_volume_momentum_rate_bounds=flux,
                wet_side_debit_rate_bounds=tuple((-hi, -lo) for lo, hi in flux),
                dry_side_credit_rate_bounds=flux,
                normal_momentum_rate_bounds=normal,
                maximum_relative_mass_width=(mass_hi-mass_lo)/full_mass[0],
                positive_lateral_transfer_proven=mass_lo > 0,
                bounded_source_crossing_intervals=len(unresolved),
                local_homogeneous_hydrostatic_flux_bounded=True,
                scope='One common outward local zero-normal dry-front flux; shared ray ownership, finite-time spreading, energy and coupled bed/pressure evolution remain required.',
                coupled_time_or_energy_or_native_or_gameplay_accepted=False)
