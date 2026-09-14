"""Total-depth solver references on captured bed geometry, NOT gameplay.

Evolves h, hu, hv instead of freezing the mean. Hydrostatic face reconstruction
(Audusse et al. 2004), optional second-order MC free-surface/velocity slopes,
Rusanov flux, SSP-RK2. First-order remains available as the original control.
Default reflecting box boundaries conserve mass; explicit exterior FV states
support boundary flux exchange without an interior reset. Exterior pressure
requires separately supplied face velocity/time-derivative traces; it is not a
nonreflecting boundary or gameplay qualification. Optional pressure models are the
linear local-depth approximation, standard SGN, and a rational SGN extension.
The rational extension is not the exact Whitham-GN/DtN model. No damping, height
repair, forcing, foam production or moving-domain coupling: this isolates solver behavior,
not realistic river motion or the requested full water model.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from audit_detail_wave_regime import read_snapshot
from detail_nonlinear_flux import G
from total_depth_pressure import pressure_correction
from total_depth_nonlinear_pressure import nonlinear_pressure_force, geometric_bed_slope
from breaking_front_reference import dispersion_fraction
from adaptive_hydrostatic_precision import refine_faces


class ReplayExhausted(RuntimeError):
    def __init__(self, state, diagnostics):
        self.state = state.copy()
        self.diagnostics = diagnostics
        super().__init__(f"Total-depth replay exhausted at {diagnostics['elapsed_s']}s; no repair")


class ReplayInvalidRate(RuntimeError):
    def __init__(self, state, diagnostics):
        self.state = state.copy()
        self.diagnostics = diagnostics
        super().__init__(f"Total-depth rate failed at {diagnostics['elapsed_s']}s: {diagnostics['error']}; no repair")


def mc(value, axis, periodic, other=None):
    back = value-np.roll(value, 1, axis)
    front = np.roll(value, -1, axis)-value
    if other is not None:
        # Difference the components before adding: h+bed can round tiny h away.
        back += other-np.roll(other, 1, axis)
        front += np.roll(other, -1, axis)-other
    result = .5*(np.sign(back)+np.sign(front))*np.minimum(.5*abs(back+front), 2*np.minimum(abs(back), abs(front)))
    if not periodic:
        edge = [slice(None)]*value.ndim
        edge[axis] = [0, -1]; result[tuple(edge)] = 0
    return result


def momentum_faces(depth, velocity, depth_slope, velocity_slope, minimum, maximum, *, face_depths=None):
    """Positive depth faces whose average momentum equals the original cell.

    Independent h/u slopes introduce +dh*du/4 into that average. Weight the
    velocity increments by the OPPOSITE face's depth, then limit their common
    slope factor to neighboring velocity bounds. Only the polynomial changes;
    no conserved average, dry-cell mass or momentum is repaired.
    """
    hm, hp = (depth-.5*depth_slope, depth+.5*depth_slope) if face_depths is None else face_depths
    weight_m = np.divide(hp, 2*depth, out=np.zeros_like(depth), where=depth > 0)
    weight_p = np.divide(hm, 2*depth, out=np.zeros_like(depth), where=depth > 0)
    dm, dp = -weight_m[..., None]*velocity_slope, weight_p[..., None]*velocity_slope
    factor = np.ones_like(velocity)
    for delta in (dm, dp):
        allowed = np.where(delta >= 0, maximum-velocity, minimum-velocity)
        ratio = np.divide(allowed, delta, out=np.ones_like(delta), where=delta != 0)
        factor = np.minimum(factor, np.maximum(0, ratio))
    return hm[..., None]*(velocity+factor*dm), hp[..., None]*(velocity+factor*dp)


def face_pair(minus, plus, axis, periodic):
    a = np.concatenate((np.take(plus if periodic else minus,
        [-1] if periodic else [0], axis=axis), plus), axis=axis)
    b = np.concatenate((minus, np.take(minus if periodic else plus,
        [0] if periodic else [-1], axis=axis)), axis=axis)
    return a, b


def exterior_sides(exterior, shape, axis):
    """Packed ghost centres: west Ny, east Ny, south Nx, north Nx."""
    ny, nx = shape
    count, start = (ny, 0) if axis == 1 else (nx, 2*ny)
    state, bed = exterior
    return (state[start:start+count], state[start+count:start+2*count],
            bed[start:start+count], bed[start+count:start+2*count])


def exterior_pair(a, b, low, high, axis):
    edge = [slice(None)]*a.ndim
    edge[axis] = 0; a[tuple(edge)] = low
    edge[axis] = -1; b[tuple(edge)] = high


def hydrostatic_faces(depth, bed, dh, deta, axis, periodic, exterior=None, *, reconstruction=None, flattened=None,
                      slope_factors=None):
    hm, hp = depth-.5*dh, depth+.5*dh
    ha, hb = face_pair(hm, hp, axis, periodic)
    za, zb = face_pair(bed, bed, axis, periodic)
    offset_a, offset_b = face_pair(-.5*(deta-dh), .5*(deta-dh), axis, periodic)
    if exterior is not None:
        lo, hi, blo, bhi = exterior_sides(exterior, bed.shape, axis)
        exterior_pair(ha, hb, lo[:, 0], hi[:, 0], axis)
        exterior_pair(za, zb, blo, bhi, axis)
        exterior_pair(offset_a, offset_b, 0, 0, axis)
    # Difference before adding offsets, independent of absolute height datum.
    bed_jump = (zb-za)+(offset_b-offset_a)
    before_a = ha-np.maximum(0, bed_jump)
    before_b = hb-np.maximum(0, -bed_jump)
    hsa = np.maximum(0, before_a)
    hsb = np.maximum(0, before_b)
    if reconstruction is not None:
        refine_faces(depth, bed, axis, periodic, exterior, reconstruction, flattened,
                     hm, hp, ha, hb, hsa, hsb, before_a, before_b, slope_factors=slope_factors)
    return hm, hp, ha, hb, hsa, hsb


def rate(state, bed, dx, *, second_order=False, periodic=False, dispersive=False,
         pressure_model='linear', pressure_diagnostics=None, pressure_interpolation='centered',
         pressure_formulation='expanded', pressure_bed_slope='weighted', breaking_model='none', foam=None,
         exterior=None, boundary_diagnostics=None, pressure_boundary=None, shoreline_limiter='binary'):
    if shoreline_limiter not in ('binary', 'continuous', 'unscaled'):
        raise ValueError('Unknown shoreline reconstruction limiter')
    if (state.shape != (*bed.shape, 3) or not np.all(np.isfinite(state))
            or not np.all(np.isfinite(bed)) or not np.isfinite(dx) or dx <= 0
            or np.any(state[..., 0] < 0)
            or np.any(state[..., 1:][state[..., 0] == 0] != 0)):
        raise ValueError('Invalid total-depth state; no mass/momentum repair')
    if exterior is not None:
        if periodic or (dispersive and pressure_boundary is None):
            raise ValueError('Exterior transport cannot use periodic or unqualified closed pressure boundaries')
        es, eb = (np.asarray(value, dtype=state.dtype) for value in exterior)
        count = 2*sum(bed.shape)
        if (es.shape != (count, 4) or eb.shape != (count,) or not np.isfinite(es).all()
                or not np.isfinite(eb).all() or np.any(es[:, [0, 3]] < 0)
                or np.any(es[es[:, 0] == 0, 1:3] != 0)):
            raise ValueError('Invalid exterior state or bed; no repair')
        with np.errstate(over='ignore', invalid='ignore', divide='ignore'):
            ev = np.divide(es[:, 1:3], es[:, 0, None], out=np.zeros_like(es[:, 1:3]), where=es[:, 0, None] > 0)
        if not np.isfinite(ev).all():
            raise ValueError('Unrepresentable exterior velocity; no repair')
        exterior = es, eb
    if pressure_boundary is not None and (exterior is None or periodic or not dispersive
            or pressure_model not in ('sgn', 'rational_sgn') or pressure_interpolation != 'depth_weighted'
            or pressure_formulation != 'kinematic' or pressure_bed_slope != 'geometry'):
        raise ValueError('Prescribed pressure boundary requires exterior FV and depth-weighted kinematic nonlinear pressure with physical bed slopes')
    boundary_fluxes = []
    if pressure_model not in ('linear', 'sgn', 'rational_sgn'):
        raise ValueError('Unknown pressure model')
    if pressure_bed_slope not in ('weighted', 'geometry'):
        raise ValueError('Unknown pressure bed slope')
    if breaking_model not in ('none','hybrid_front') or (breaking_model != 'none' and
            (not dispersive or pressure_model == 'linear' or pressure_formulation != 'kinematic' or pressure_bed_slope != 'geometry')):
        raise ValueError('Hybrid breaking requires nonlinear kinematic pressure and physical bed slopes')
    result = np.zeros_like(state)
    if foam is not None:
        foam = np.asarray(foam, dtype=float)
        if foam.shape != bed.shape or not np.isfinite(foam).all() or np.any(foam < 0):
            raise ValueError('Invalid conserved foam density; no repair')
        foam_rate = np.zeros_like(foam)
    speed_sum = 0.
    depth = state[..., 0]
    velocity = np.divide(state[..., 1:], depth[..., None], out=np.zeros_like(state[..., 1:]), where=depth[..., None] > 0)
    faces, pressure_pairs = [], []
    for component, axis in enumerate((1, 0)):
        deta = mc(depth, axis, periodic, other=bed) if second_order else np.zeros_like(depth)
        du = mc(velocity, axis, periodic) if second_order else np.zeros_like(velocity)
        stencil = (depth > 0) & (np.roll(depth, 1, axis) > 0) & (np.roll(depth, -1, axis) > 0)
        deta *= stencil; du *= stencil[..., None]
        # Reconstruct h and free surface together. A cell-constant bed with an
        # eta slope creates a pressure acceleration in a shallow, blocked cell
        # even when both hydrostatic faces are dry. The matching within-cell
        # bed source below is essential; neither cell average is changed.
        dh = mc(depth, axis, periodic) if second_order else np.zeros_like(depth)
        dh *= stencil
        # A polynomial spanning a dry hydrostatic face is not fully wet.
        # Use the well-balanced cell average there, retaining MC accuracy in
        # fully wet cells (including arbitrarily thin continuous-bed films).
        # Classify the original polynomial, then reconstruct once. Cascading
        # neighbor flattening turns a continuous thin film into artificial bed
        # stairs throughout the domain, suppressing its gravity acceleration.
        # Only slopes change: no threshold, velocity cap, or conserved repair.
        hm, hp, ha, hb, hsa, hsb = hydrostatic_faces(depth, bed, dh, deta, axis, periodic, exterior, reconstruction=second_order)
        partial = (depth > 0) & ((np.take(hsa, range(1, hsa.shape[axis]), axis=axis) == 0)
            | (np.take(hsb, range(hsb.shape[axis]-1), axis=axis) == 0))
        changed = partial & ((dh != 0) | (deta != 0) | np.any(du != 0, axis=-1))
        if shoreline_limiter == 'continuous' and second_order:
            from continuous_shoreline_reconstruction import factors
            factor = factors(hm, hp, hsa, hsb, axis)
            dh *= factor; deta *= factor; du *= factor[..., None]
            hm, hp, ha, hb, hsa, hsb = hydrostatic_faces(depth, bed, dh, deta, axis, periodic, exterior,
                reconstruction=True, slope_factors=factor)
        elif shoreline_limiter == 'binary' and np.any(changed):
            dh[changed] = 0; deta[changed] = 0; du[changed] = 0
            hm, hp, ha, hb, hsa, hsb = hydrostatic_faces(depth, bed, dh, deta, axis, periodic, exterior, reconstruction=second_order, flattened=partial)
        # 'unscaled' is an explicit CPU diagnostic control: use the original
        # positive MC h/eta/u polynomials and the SAME hydrostatic source/flux.
        # No second shoreline pass, source correction, new floor or dt change.
        # This is not a new native model or permission to promote playable water.
        minimum = np.minimum(velocity, np.minimum(np.roll(velocity, 1, axis), np.roll(velocity, -1, axis)))
        maximum = np.maximum(velocity, np.maximum(np.roll(velocity, 1, axis), np.roll(velocity, -1, axis)))
        qm, qp = momentum_faces(depth, velocity, dh, du, minimum, maximum, face_depths=(hm, hp))
        minus = np.concatenate((hm[..., None], qm), axis=-1)
        plus = np.concatenate((hp[..., None], qp), axis=-1)
        a, b = face_pair(minus, plus, axis, periodic)
        low = [slice(None)]*3; low[axis] = 0
        high = [slice(None)]*3; high[axis] = -1
        low[-1] = high[-1] = component+1
        if exterior is not None:
            lo, hi, _, _ = exterior_sides(exterior, bed.shape, axis)
            # Match the interior zero-slope h*(M/h) reconstruction, including
            # its represented arithmetic; never reflect supplied momentum.
            def ghost_face(value):
                h = value[:, 0, None]
                u = np.divide(value[:, 1:3], h, out=np.zeros_like(value[:, 1:3]), where=h > 0)
                return np.concatenate((h, h*u), axis=-1)
            exterior_pair(a, b, ghost_face(lo), ghost_face(hi), axis)
        elif not periodic:
            a[tuple(low)] *= -1; b[tuple(high)] *= -1  # Reflect normal momentum only.
        faces.append((a, b, ha, hb, hsa, hsb, deta, dh))
        if dispersive:
            pair = np.take((hsa > 0) & (hsb > 0), range(1, hsa.shape[axis]), axis=axis)
            if not periodic:
                edge = [slice(None), slice(None)]; edge[axis] = -1
                pair[tuple(edge)] = False
            if depth.shape[axis] == 1: pair[:] = False
            pressure_pairs.append(pair)
    if dispersive and pressure_model == 'linear':
        correction, _ = pressure_correction(depth, bed, dx, periodic=periodic, pairs=pressure_pairs)
    hydro_force = np.zeros_like(velocity)
    for component, axis in enumerate((1, 0)):
        a, b, ha, hb, hsa, hsb, deta, dh = faces[component]
        ua = np.divide(a[..., 1:], ha[..., None], out=np.zeros_like(a[..., 1:]), where=ha[..., None] > 0)
        ub = np.divide(b[..., 1:], hb[..., None], out=np.zeros_like(b[..., 1:]), where=hb[..., None] > 0)
        sa = np.concatenate((hsa[..., None], hsa[..., None]*ua), axis=-1)
        sb = np.concatenate((hsb[..., None], hsb[..., None]*ub), axis=-1)
        va, vb = ua[..., component], ub[..., component]
        ca, cb = np.sqrt(G*hsa), np.sqrt(G*hsb)
        signal = np.maximum(abs(va)+ca, abs(vb)+cb)
        # Algebraically the same Rusanov flux, factored into nonnegative
        # transport weights. Do not form s-u after rounding |u|+sqrt(g*h):
        # tiny wet faces otherwise transfer momentum but exactly zero water.
        weight_a = .5*np.maximum((abs(va)+va)+ca, (abs(vb)+va)+cb)
        weight_b = .5*np.maximum((abs(va)-vb)+ca, (abs(vb)-vb)+cb)
        flux = weight_a[..., None]*sa-weight_b[..., None]*sb
        if foam is not None:
            # Same shared numerical water-mass flux, upwind donor concentration.
            # Divide mass flux by donor depth BEFORE multiplying foam: forming
            # foam/h first can overflow for otherwise representable thin films.
            da, db = face_pair(depth, depth, axis, periodic)
            fa, fb = face_pair(foam, foam, axis, periodic)
            if exterior is not None:
                lo, hi, _, _ = exterior_sides(exterior, bed.shape, axis)
                exterior_pair(da, db, lo[:, 0], hi[:, 0], axis)
                exterior_pair(fa, fb, lo[:, 3], hi[:, 3], axis)
            mass = flux[..., 0]
            donor_depth = np.where(mass >= 0, da, db)
            donor_foam = np.where(mass >= 0, fa, fb)
            if np.any((mass != 0) & (donor_depth <= 0)):
                raise ValueError('Nonzero foam transport without donor water')
            coefficient = np.divide(mass, donor_depth, out=np.zeros_like(mass), where=donor_depth > 0)
            foam_flux = coefficient*donor_foam
            if not np.isfinite(foam_flux).all():
                raise ValueError('Unrepresentable foam flux; no repair')
            foam_rate -= (np.take(foam_flux, range(1, foam_flux.shape[axis]), axis=axis)
                         -np.take(foam_flux, range(foam_flux.shape[axis]-1), axis=axis))/dx
        if boundary_diagnostics is not None:
            # Positive-axis oriented physical face flux. Bed sources prevent
            # general momentum conservation; water and foam balance exactly.
            physical = flux.copy()
            physical[..., component+1] += .25*G*(hsa*hsa+hsb*hsb)
            ledger = np.concatenate((physical, (foam_flux if foam is not None else
                np.zeros_like(hsa))[..., None]), axis=-1)
            boundary_fluxes.extend((np.take(ledger, 0, axis=axis), np.take(ledger, -1, axis=axis)))
        result -= (np.take(flux, range(1, flux.shape[axis]), axis=axis)
                   - np.take(flux, range(flux.shape[axis]-1), axis=axis))/dx
        # Cancel the owning-cell hydrostatic polynomial analytically, before
        # rounding: .5*g*(hp^2-hm^2)+g*h*(deta-dh) = g*h*deta.
        # Face deviations are equal/opposite; factor the square difference.
        # Same hydrostatic Rusanov equation, but a resting lake with equal
        # reconstructed face depths has exactly zero force, including FP32.
        jump = .25*G*(hsb-hsa)*(hsb+hsa)
        hydro_force[..., component] = -(np.take(jump, range(1, jump.shape[axis]), axis=axis)
            +np.take(jump, range(jump.shape[axis]-1), axis=axis))/dx-G*depth*deta/dx
        result[..., component+1] += hydro_force[..., component]
        if dispersive and pressure_model == 'linear':
            pair = pressure_pairs[component]
            ps = mc(correction, axis, periodic)
            ps *= pair & np.roll(pair, 1, axis)
            pa, pb = face_pair(correction-.5*ps, correction+.5*ps, axis, periodic)
            face_pressure = .5*(pa+pb)
            edge_pair = np.take(pair, [-1], axis=axis) if periodic else np.zeros_like(np.take(pair, [0], axis=axis))
            pair_faces = np.concatenate((edge_pair, pair), axis=axis)
            face_depth = np.where(pair_faces, .5*(hsa+hsb), 0)
            positive = range(1, face_depth.shape[axis])
            negative = range(face_depth.shape[axis]-1)
            # Same reconstructed face derivative as hydrostatic pressure, not
            # an unrelated centered gradient. The owning-cell balance cancels
            # constant pressure even at closed wet-graph faces.
            pressure_rate = np.take(face_depth, positive, axis=axis)*(np.take(face_pressure, positive, axis=axis)-correction)
            pressure_rate -= np.take(face_depth, negative, axis=axis)*(np.take(face_pressure, negative, axis=axis)-correction)
            result[..., component+1] -= G*pressure_rate/dx
        speed_sum += float(signal.max())
    if dispersive and pressure_model != 'linear':
        fraction = None
        if breaking_model == 'hybrid_front':
            fraction, breaking_stats = dispersion_fraction(depth, bed, result[...,0], pressure_pairs, dx)
            if pressure_diagnostics is not None:
                for name,value in breaking_stats.items():
                    key = 'maximum_'+name
                    pressure_diagnostics[key] = max(pressure_diagnostics.get(key,0),value)
        force, pressure_stats = nonlinear_pressure_force(depth, bed, velocity,
            hydro_force, pressure_pairs, dx, rational=pressure_model == 'rational_sgn', interpolation=pressure_interpolation,
            formulation=pressure_formulation, mass_rate=result[..., 0], momentum_rate=result[..., 1:],
            bed_slope=geometric_bed_slope(bed, dx, periodic,
                exterior_bed=exterior[1] if exterior is not None else None) if pressure_bed_slope == 'geometry' else None,
            dispersion_fraction=fraction, boundary_velocity=pressure_boundary)
        if pressure_boundary is not None and any(not np.isfinite(s['relative_residual']) or
                s['relative_residual'] > 2e-5 for s in pressure_stats):
            raise ValueError('Prescribed boundary pressure residual is unqualified')
        result[..., 1:] += force
        if pressure_diagnostics is not None:
            pressure_diagnostics['worst_relative_residual'] = max(pressure_diagnostics.get('worst_relative_residual', 0),
                max(s['relative_residual'] for s in pressure_stats))
            pressure_diagnostics['maximum_iterations'] = max(pressure_diagnostics.get('maximum_iterations', 0),
                max(s['iterations'] for s in pressure_stats))
            pressure_diagnostics['solve_count'] = pressure_diagnostics.get('solve_count', 0)+len(pressure_stats)
    if foam is not None:
        result = np.concatenate((result, foam_rate[..., None]), axis=-1)
    if boundary_diagnostics is not None:
        boundary_diagnostics['flux'] = np.concatenate(boundary_fluxes, axis=0)
        boundary_diagnostics['outward_rate'] = dx*sum(
            boundary_fluxes[j+1].sum(axis=0)-boundary_fluxes[j].sum(axis=0) for j in (0, 2))
    return result, .4*dx/speed_sum if speed_sum else np.inf


def advance(state, bed, dx, seconds, max_trials=10000, *, second_order=False, periodic=False,
            dispersive=False, pressure_model='linear', progress_every_seconds=0., on_progress=None,
            pressure_interpolation='centered', pressure_formulation='expanded', on_checkpoint=None, on_step=None,
            pressure_bed_slope='weighted', breaking_model='none', boundary_at_time=None, shoreline_limiter='binary'):
    """Advance with optional prescribed boundary data at each SSP-RK stage time.

    boundary_at_time(elapsed_seconds, readonly_stage) returns
    (ghost_state, ghost_bed, face_trace).
    It must be deterministic for retries and valid over the requested interval.
    The read-only stage supports physical reflecting walls or other explicit
    mixed boundary policies. It cannot be used to reset the interior in place.
    The face trace includes its time derivative; ghost centres alone do not
    establish it. This CPU reference does not supply an outgoing-wave condition.
    """
    if not np.isfinite(seconds) or seconds < 0 or max_trials < 1:
        raise ValueError('Invalid requested interval')
    current = np.asarray(state, dtype=float).copy()
    elapsed, steps, rejected = 0., 0, 0
    last_rejection = None
    if not np.isfinite(progress_every_seconds) or progress_every_seconds < 0:
        raise ValueError('Invalid progress interval')
    next_progress = progress_every_seconds
    pressure_diagnostics = {}
    outward_volume = 0.
    if boundary_at_time is not None and (not callable(boundary_at_time) or periodic):
        raise ValueError('Invalid prescribed boundary provider or periodic composition')
    def boundary(time, value):
        if boundary_at_time is None: return {}
        readonly = value.view(); readonly.flags.writeable = False
        es, eb, trace = boundary_at_time(time, readonly)
        return dict(exterior=(es, eb), pressure_boundary=trace)
    initial_volume = float(current[..., 0].sum()*dx*dx)
    def mass_budget(value):
        change = float(value[..., 0].sum()*dx*dx-initial_volume)
        # Historical volume_error is the inventory CHANGE, not an open-system
        # conservation error. Only accepted-stage flux enters the latter.
        return dict(volume_error_m3=change, boundary_outward_volume_m3=outward_volume,
                    mass_balance_error_m3=change+outward_volume)
    def diagnostics(value):
        h = value[..., 0]
        v = np.divide(value[..., 1:], h[..., None], out=np.zeros_like(value[..., 1:]), where=h[..., None] > 0)
        speed2 = np.sum(v*v, axis=-1)
        energy = float(np.sum(.5*h*speed2+.5*G*h*h+G*h*(bed-bed.min()))*dx*dx)
        return float(np.sqrt(speed2.max())), energy
    peak_speed, initial_energy = diagnostics(current)
    peak_energy = initial_energy
    while elapsed < seconds:
        first_ledger = {}
        try:
            first, bound = rate(current, bed, dx, second_order=second_order, periodic=periodic, dispersive=dispersive,
                pressure_model=pressure_model, pressure_diagnostics=pressure_diagnostics, pressure_interpolation=pressure_interpolation,
                pressure_formulation=pressure_formulation, pressure_bed_slope=pressure_bed_slope, breaking_model=breaking_model,
                boundary_diagnostics=first_ledger if boundary_at_time is not None else None,
                shoreline_limiter=shoreline_limiter, **boundary(elapsed, current))
        except (ValueError, FloatingPointError) as error:
            if steps == 0: raise  # Invalid supplied input is not an accepted state.
            h = current[..., 0]
            raise ReplayInvalidRate(current, dict(elapsed_s=elapsed, steps=steps, rejected_trials=rejected,
                error=str(error), minimum_depth_m=float(h.min()),
                minimum_positive_depth_m=float(h[h > 0].min()) if np.any(h > 0) else None,
                maximum_depth_m=float(h.max()), maximum_speed_mps=diagnostics(current)[0],
                pressure_solver=pressure_diagnostics.copy(), **mass_budget(current))) from error
        dt = min(1/120, seconds-elapsed, bound)
        while True:
            # Integrate a final representable remainder even below the safety
            # floor; only a CFL/rejection-imposed tiny step is exhaustion.
            if steps+rejected >= max_trials or (dt < 1e-9 and dt != seconds-elapsed):
                speed, energy = diagnostics(current)
                h = current[..., 0]
                velocity = np.divide(current[..., 1:], h[..., None], out=np.zeros_like(current[..., 1:]), where=h[..., None] > 0)
                index = np.unravel_index(np.sum(velocity*velocity, axis=-1).argmax(), h.shape)
                raise ReplayExhausted(current, dict(elapsed_s=elapsed, steps=steps,
                    exhaustion_reason='trial_budget' if steps+rejected >= max_trials else 'minimum_step',
                    rejected_trials=rejected, requested_step_s=dt, initial_cfl_bound_s=bound,
                    last_rejection=last_rejection, maximum_speed_mps=speed,
                    minimum_depth_m=float(h.min()), maximum_depth_m=float(h.max()),
                    pressure_solver=pressure_diagnostics.copy(), energy_per_density_m5s2=energy,
                    fastest_cell_yx=[int(i) for i in index], fastest_cell_depth_m=float(h[index]),
                    fastest_cell_momentum=[float(v) for v in current[index][1:]],
                    fastest_cell_bed_m=float(bed[index]), **mass_budget(current)))
            try:
                stage = current+dt*first
                second_ledger = {}
                second, stage_bound = rate(stage, bed, dx, second_order=second_order, periodic=periodic, dispersive=dispersive,
                    pressure_model=pressure_model, pressure_diagnostics=pressure_diagnostics, pressure_interpolation=pressure_interpolation,
                    pressure_formulation=pressure_formulation, pressure_bed_slope=pressure_bed_slope, breaking_model=breaking_model,
                    boundary_diagnostics=second_ledger if boundary_at_time is not None else None,
                    shoreline_limiter=shoreline_limiter, **boundary(elapsed+dt, stage))
                if dt > stage_bound*(1+1e-12): raise ValueError('Stage CFL')
                candidate = .5*(current+stage+dt*second)
                if np.any(candidate[..., 0] < 0) or not np.all(np.isfinite(candidate)):
                    raise ValueError('Invalid candidate')
                break
            except ValueError as error:
                last_rejection = str(error)
                dt *= .5; rejected += 1
        previous = current
        if boundary_at_time is not None:
            outward_volume += .5*dt*(first_ledger['outward_rate'][0]+second_ledger['outward_rate'][0])
        current = candidate; elapsed += dt; steps += 1
        speed, energy = diagnostics(current)
        peak_speed = max(peak_speed, speed); peak_energy = max(peak_energy, energy)
        if on_step is not None:
            on_step(previous.copy(), current.copy(), dict(elapsed_s=elapsed, step_s=dt,
                steps=steps, rejected_trials=rejected, maximum_speed_mps=speed, **mass_budget(current)))
        if (on_progress is not None or on_checkpoint is not None) and progress_every_seconds > 0 and (elapsed >= next_progress or elapsed == seconds):
            progress = dict(elapsed_s=elapsed, steps=steps, rejected_trials=rejected,
                maximum_depth_m=float(current[..., 0].max()), maximum_speed_mps=speed,
                peak_accepted_state_speed_mps=peak_speed, pressure_solver=pressure_diagnostics.copy(), **mass_budget(current))
            if on_checkpoint is not None: on_checkpoint(current.copy(), progress.copy())
            if on_progress is not None: on_progress(progress)
            while next_progress <= elapsed: next_progress += progress_every_seconds
    velocity = np.divide(current[..., 1:], current[..., 0, None],
        out=np.zeros_like(current[..., 1:]), where=current[..., 0, None] > 0)
    return current, dict(elapsed_s=elapsed, steps=steps, rejected_trials=rejected,
        minimum_depth_m=float(current[..., 0].min()), maximum_depth_m=float(current[..., 0].max()),
        maximum_speed_mps=float(np.linalg.norm(velocity, axis=-1).max()),
        peak_accepted_state_speed_mps=peak_speed,
        initial_energy_per_density_m5s2=initial_energy,
        final_energy_per_density_m5s2=diagnostics(current)[1],
        peak_energy_per_density_m5s2=peak_energy,
        pressure_solver=pressure_diagnostics,
        **mass_budget(current))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('snapshot', type=Path)
    parser.add_argument('--seconds', type=float, default=5.)
    parser.add_argument('--second-order', action='store_true')
    parser.add_argument('--dispersive', action='store_true', help='Experimental local-depth pressure correction, not full nonlinear GN')
    parser.add_argument('--pressure-model', choices=('linear', 'sgn', 'rational_sgn'), default='linear')
    parser.add_argument('--pressure-interpolation', choices=('centered', 'depth_weighted'), default='centered')
    parser.add_argument('--pressure-formulation', choices=('expanded', 'kinematic'), default='expanded')
    parser.add_argument('--pressure-bed-slope', choices=('weighted', 'geometry'), default='weighted')
    parser.add_argument('--breaking-model', choices=('none','hybrid_front'), default='none')
    parser.add_argument('--progress-every-seconds', type=float, default=0.)
    parser.add_argument('--save-progress-states', action='store_true', help='Preserve accepted diagnostic checkpoints without restarting evolution')
    parser.add_argument('--initial-total-state', type=Path, help='Explicit saved total h/hu/hv state on the supplied snapshot bed; not a repaired input')
    parser.add_argument('--max-trials', type=int, default=10000, help='Bound diagnostic work; exhaustion is not a completed replay')
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    if args.pressure_model != 'linear' and not args.dispersive:
        parser.error('--pressure-model requires --dispersive')
    if args.pressure_interpolation != 'centered' and (not args.dispersive or args.pressure_model == 'linear'):
        parser.error('--pressure-interpolation requires a nonlinear dispersive model')
    if args.pressure_formulation != 'expanded' and (not args.dispersive or args.pressure_model == 'linear'):
        parser.error('--pressure-formulation requires a nonlinear dispersive model')
    if args.pressure_bed_slope != 'weighted' and (not args.dispersive or args.pressure_model == 'linear'):
        parser.error('--pressure-bed-slope requires a nonlinear dispersive model')
    if args.breaking_model != 'none' and (not args.dispersive or args.pressure_model == 'linear'
            or args.pressure_formulation != 'kinematic' or args.pressure_bed_slope != 'geometry'):
        parser.error('--breaking-model requires nonlinear kinematic pressure and physical bed slopes')
    if args.save_progress_states and args.progress_every_seconds <= 0:
        parser.error('--save-progress-states requires a positive progress interval')
    if args.report.exists(): raise FileExistsError(args.report)
    meta, arrays, hashes = read_snapshot(args.snapshot)
    if 'mean_geometry' not in arrays: raise ValueError('Actual paired bed geometry required; do not invent it')
    geometry, flow, detail = (arrays[k].astype(float) for k in ('mean_geometry', 'flow', 'state'))
    h = flow[..., 0]+detail[..., 0]
    initial = np.concatenate((h[..., None], h[..., None]*flow[..., 1:3]+detail[..., 1:3]), axis=-1)
    if args.initial_total_state is not None:
        initial = np.load(args.initial_total_state, allow_pickle=False)
        hashes[str(args.initial_total_state)] = hashlib.sha256(args.initial_total_state.read_bytes()).hexdigest()
    report = dict(schema='raftsim.total_depth_bank_replay.v2', scope=__doc__, source_hashes=hashes,
        implementation_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        pressure_implementation_sha256=hashlib.sha256(Path(__file__).with_name('total_depth_pressure.py').read_bytes()).hexdigest(),
        pressure_coefficients_sha256=hashlib.sha256(Path(__file__).with_name('finite_depth_pressure_reference.py').read_bytes()).hexdigest(),
        nonlinear_pressure_sha256=hashlib.sha256(Path(__file__).with_name('total_depth_nonlinear_pressure.py').read_bytes()).hexdigest(),
        breaking_implementation_sha256=hashlib.sha256(Path(__file__).with_name('breaking_front_reference.py').read_bytes()).hexdigest(),
        spatial_order=2 if args.second_order else 1,
        dispersive=args.dispersive, pressure_iterations=40 if args.dispersive else 0,
        pressure_model=args.pressure_model,
        pressure_interpolation=args.pressure_interpolation,
        pressure_formulation=args.pressure_formulation,
        pressure_bed_slope=args.pressure_bed_slope,
        breaking_model=args.breaking_model,
        energy_diagnostic='hydrostatic only; excludes nonlocal pressure contribution',
        requested_seconds=args.seconds, integrated=False, scene_accepted=False,
        initial_total_state=str(args.initial_total_state) if args.initial_total_state else None,
        maximum_trials=args.max_trials,
        maximum_sampled_surface_depth_residual_m=float(abs(geometry[..., 1]-geometry[..., 0]-geometry[..., 2]).max()),
        maximum_flow_depth_mask_difference_m=float(abs(flow[..., 0]-geometry[..., 2]).max()))
    report['checkpoints'] = []
    def checkpoint(state, progress):
        output = args.report.with_suffix(f'.step-{progress["steps"]:06d}.npy')
        with output.open('xb') as f: np.save(f, state)
        progress.update(state=str(output.resolve()), sha256=hashlib.sha256(output.read_bytes()).hexdigest())
        report['checkpoints'].append(progress)
        # Persist the state/time pair before a later failure can interrupt main.
        with output.with_suffix('.json').open('x') as f: json.dump(progress, f, indent=2, allow_nan=False)
    try:
        final, stats = advance(initial, geometry[..., 0], meta['cell_m'], args.seconds,
            max_trials=args.max_trials,
            second_order=args.second_order, dispersive=args.dispersive, pressure_model=args.pressure_model,
            pressure_interpolation=args.pressure_interpolation,
            pressure_formulation=args.pressure_formulation,
            pressure_bed_slope=args.pressure_bed_slope, breaking_model=args.breaking_model,
            progress_every_seconds=args.progress_every_seconds,
            on_checkpoint=checkpoint if args.save_progress_states else None,
            on_progress=lambda state: print(json.dumps(dict(progress=state)), flush=True))
        output = args.report.with_suffix('.total-state.npy')
        with output.open('xb') as f: np.save(f, final)
        report.update(completed=True, statistics=stats, final_state=str(output.resolve()))
    except ReplayExhausted as error:
        output = args.report.with_suffix('.last-admissible-state.npy')
        with output.open('xb') as f: np.save(f, error.state)
        report.update(completed=False, error=str(error), failure=error.diagnostics,
            last_admissible_state=str(output.resolve()))
    except ReplayInvalidRate as error:
        output = args.report.with_suffix('.last-accepted-state.npy')
        with output.open('xb') as f: np.save(f, error.state)
        report.update(completed=False, error=str(error), failure=error.diagnostics,
            last_accepted_state=str(output.resolve()))
    except (ValueError, RuntimeError) as error:
        report.update(completed=False, error=str(error))
    with args.report.open('x') as f: json.dump(report, f, indent=2, allow_nan=False)
    print(json.dumps(report, indent=2))


if __name__ == '__main__': main()
