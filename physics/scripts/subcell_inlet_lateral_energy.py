"""Energy flux of the SAME local zero-normal hydrostatic dry-front fan.

At the interface h*=4h/9, un*=2sqrt(gh)/3, ut=u. The energy flux is
q*(|u|²/2 + 2gh/3 + g*(bed-datum)), including pressure work, not just
advection of the initial energy. This is instantaneous and hydrostatic:
it does not advance the sloping 2D profile or close dispersive pressure work.
"""
from fractions import Fraction as F

from subcell_exact_geometry import SourceFragment
from subcell_inlet_contact_time import _sqrt_bounds
from subcell_inlet_hydrostatic_force import lateral_front_intervals, _linear_bounds


def lateral_energy_flux(sweep, fragment, *, energy_datum=F(0),
                        relative_bound=F(1, 10**12), max_depth=48, root_bits=128):
    """Bound one common signed energy transfer per density on the original ray.

    On X=A+u*(R³-r³), bed=bA+grad(b).u*(R³-r³). Let Mp=int(q*r**p dl).
    Its primitive is 16k/[9(2p+9)]*sqrt(g*k*|u|²*r**(2p+9)). Then
    FE=(|u|²/2+g*(bA-datum+grad(b).u*R³))*M0 + 2gk/3*M1
       -g*grad(b).u*M3. Original source crossings and radical roundoff are
    enclosed explicitly. Width is relative to the sum of absolute full-ray
    moment contributions, NOT a possibly cancelling signed energy flux.
    The datum is explicit because gravitational energy changes by g*C*mass
    under an elevation-reference shift. No source vertex or pool is changed.
    """
    if type(root_bits) is not int or not 16 <= root_bits <= 4096:
        raise ValueError('Lateral energy requires 16..4096 exact root bits')
    if not isinstance(fragment, SourceFragment) or len(fragment.gradient) != 2 or fragment.area <= 0:
        raise ValueError('Original affine source bed required for energy flux')
    gradient = tuple(F(x) for x in fragment.gradient)
    anchor = fragment.polygon[0]
    if any(p[2]-anchor[2] != sum(gradient[j]*(p[j]-anchor[j]) for j in range(2))
           for p in fragment.polygon):
        raise ValueError('Original source bed gradient and vertices disagree')
    datum = F(energy_datum)
    inside, unresolved = lateral_front_intervals(sweep, fragment, relative_bound, max_depth,
                                                include_boundary=True)
    k, g, radius = sweep.height_scale, sweep.gravity, sweep.time_root
    speed_squared = sum(v*v for v in sweep.velocity)
    bed_at_origin = anchor[2]+sum(gradient[j]*(sweep.edge[0][j]-anchor[j]) for j in range(2))
    along_bed_rate = sum(a*b for a,b in zip(gradient, sweep.velocity))
    coefficients = (speed_squared/2+g*(bed_at_origin-datum+along_bed_rate*radius**3),
                    F(2, 3)*g*k, -g*along_bed_rate)
    moments, full_moments = [], []
    for power in (0, 1, 3):
        factor = F(16, 9*(2*power+9))*k
        def primitive(r):
            return tuple(factor*x for x in _sqrt_bounds(g*k*speed_squared*r**(2*power+9), root_bits))
        lower = upper = F(0)
        for intervals, proven in ((inside, True), (unresolved, False)):
            for lo, hi in intervals:
                a, b = primitive(lo), primitive(hi)
                lower += max(F(0), b[0]-a[1]) if proven else 0
                upper += b[1]-a[0]
        moments.append((lower, upper))
        full_moments.append(primitive(radius))
    energy = _linear_bounds(tuple((c, *m) for c,m in zip(coefficients, moments)))
    scale = sum(abs(c)*m[0] for c,m in zip(coefficients, full_moments))
    if energy[1]-energy[0] > F(relative_bound)*scale:
        raise ValueError('Lateral energy bound unresolved; no guessed flux or front deletion')
    return dict(source_id=fragment.source_id, time_seconds=radius**3, energy_datum=datum,
                outward_energy_rate_per_density_bounds=energy,
                wet_side_energy_debit_rate_bounds=(-energy[1], -energy[0]),
                dry_side_energy_credit_rate_bounds=energy,
                outward_volume_rate_bounds=moments[0],
                mass_weighted_radial_moment_bounds=dict(zip(('0', '1', '3'), moments)),
                maximum_scaled_energy_width=(energy[1]-energy[0])/scale,
                energy_width_scale=scale,
                bounded_source_crossing_intervals=len(unresolved),
                local_homogeneous_hydrostatic_energy_flux_bounded=True,
                units='m^5/s^3 per density; multiply by density for watts',
                scope='One common local Riemann energy flux including pressure work and original bed elevation. Shared ownership, donor depletion, finite-time spreading, bed/curvature and dispersive energy coupling remain required.',
                coupled_time_or_energy_or_native_or_gameplay_accepted=False)
