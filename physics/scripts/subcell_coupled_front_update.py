"""Conservative frozen-transfer linearization for source-front experiments.

Not the full rational dynamics or a native integrator. The exact assembled
face flux defines each donor rate G[j,i]=F/V[i], with zero column sums. Volume
uses backward-Euler transport. Momentum uses that same donor transport plus a
conservative implicit positive velocity-exchange graph. The remaining momentum
rate (including pressure/bed work) is held explicit. Thus
the infinitesimal rate is unchanged, but finite energy is NOT guaranteed and
must still be rejected by the caller. No mass caps or post-solve correction.

The velocity graph acts on NEW momentum divided by NEW volume, preserving
constant velocity when volumes change. It removes the frozen net-mass-only
scheme's explicitly stiff diffusion. Pressure and negative exchange remainders
still need qualification; positive volume is not local velocity stability.

The optional gross-donor form instead freezes both original Rusanov donors and
uses the SAME matrix on conserved mass and momentum. Their counterflow is
already present in that matrix; it must not be added as a second velocity graph.
"""
import math
import numpy as np


class SourceUpdateFailure(ValueError):
    def __init__(self, message, details):
        super().__init__(message)
        self.details = details


def front_timed_remainder(assembled, old_volume, new_volume):
    """Average each dry-front force with its donor's integrated mass weight.

    The BE mass transfer is dt*Fmass*Vnew/Vold. Using the same weight on the
    paired front force avoids spending a full-step pressure impulse after the
    donor's available water has already fallen. No transferred mass is capped.
    """
    count, old_count = len(old_volume), len(assembled['partition'].pools)
    parts = [v for k, v in assembled['explicit_force_parts'].items() if k != 'dry_front']
    terms = [[[float(p[i, axis]) for p in parts] if i < old_count else []
              for axis in range(2)] for i in range(count)]
    for owner, other, force in assembled['front_forces']:
        force = np.asarray(force, float)
        if (not 0 <= owner < old_count or not old_count <= other < count
                or force.shape != (2,) or not np.isfinite(force).all() or old_volume[owner] <= 0):
            raise ValueError('Original donor and explicit receiving region required for front force')
        weight = new_volume[owner]/old_volume[owner]
        for axis in range(2):
            value = float(force[axis])*weight
            terms[owner][axis].append(-value)
            terms[other][axis].append(value)
    result = np.array([[math.fsum(v) for v in row] for row in terms])
    if not np.isfinite(result).all():
        raise ValueError('Timed front force exceeds represented range')
    return result


def coupled_update(assembled, duration, gross_donors=False):
    if not np.isfinite(duration) or duration <= 0:
        raise ValueError('Positive finite duration required')
    pools, new = assembled['partition'].pools, assembled['new_region_rates']
    count = len(pools)+len(new)
    volume, momentum = np.zeros(count), np.zeros((count, 2))
    volume[:len(pools)] = [p['volume'] for p in pools]
    momentum[:len(pools)] = [p['momentum'] for p in pools]
    generator = np.zeros((count, count))
    transfers = assembled.get('gross_donor_transfers') if gross_donors else assembled['transfers']
    if transfers is None:
        raise ValueError('Explicit original gross donor records required')
    for owner, other, flux in transfers:
        if (owner == other or not 0 <= owner < len(pools) or not 0 <= other < count
                or not np.isfinite(flux) or flux <= 0 or volume[owner] <= 0):
            raise ValueError('Positive original donor and conservative source transfer required')
        rate = flux/volume[owner]
        generator[owner, owner] -= rate
        generator[other, owner] += rate
    volume_rate = np.r_[assembled['volume_rate'], [r['volume_rate'] for r in new]]
    momentum_rate = np.concatenate((assembled['momentum_rate'],
        np.array([r['momentum_rate'] for r in new]).reshape(-1, 2)))
    exchange = np.zeros((count, count))
    for left, right, conductance in ([] if gross_donors else assembled.get('velocity_exchanges', [])):
        if (left == right or not 0 <= left < len(pools) or not 0 <= right < len(pools)
                or not np.isfinite(conductance) or conductance <= 0):
            raise ValueError('Positive conservative velocity exchange required')
        exchange[left, left] -= conductance
        exchange[right, right] -= conductance
        exchange[left, right] += conductance
        exchange[right, left] += conductance
    velocity = np.divide(momentum, volume[:, None], out=np.zeros_like(momentum), where=volume[:, None] > 0)
    subtracted_residual = momentum_rate-generator@momentum-exchange@velocity
    if 'explicit_force_parts' in assembled:
        # Subtracting large advective/exchange rates to recover an extremely
        # small physical force leaves an ulp-sized ghost force. Assemble it
        # directly from the same face/bed terms instead, without a state fix.
        parts = list(assembled['explicit_force_parts'].values())
        old_force = np.array([[math.fsum(float(part[i, axis]) for part in parts)
                              for axis in range(2)] for i in range(len(pools))])
        new_force = np.array([r['explicit_force_rate'] for r in new]).reshape(-1, 2)
        residual = np.concatenate((old_force, new_force))
        residual_assembly = 'direct-face-and-bed'
    else:
        residual, residual_assembly = subtracted_residual, 'supplied-rate-difference'
    momentum_rate_error = float(np.max(abs(generator@momentum+exchange@velocity+residual-momentum_rate)))
    if momentum_rate_error >= 1e-10:
        raise ValueError('Direct force ledger does not reproduce original momentum rates')
    if 'front_forces' in assembled:
        untimed = front_timed_remainder(assembled, volume, volume)
        if np.max(abs(untimed-residual)) >= 1e-10:
            raise ValueError('Front force ledger does not reproduce original forces')
    matrix = np.eye(count)-duration*generator
    if not np.isfinite(matrix).all() or not np.isfinite(residual).all():
        raise ValueError('Coupled source transfer exceeds represented range')
    rate_error = float(np.max(abs(generator@volume-volume_rate)))
    if rate_error >= 1e-10:
        raise ValueError('Source transfer ledger does not reproduce original mass rates')
    try:
        new_volume = np.linalg.solve(matrix, volume)
        if not np.isfinite(new_volume).all() or np.any(new_volume <= 0):
            indices = np.flatnonzero(~np.isfinite(new_volume) | (new_volume <= 0))
            records = []
            for i in indices:
                state = pools[i] if i < len(pools) else new[i-len(pools)]
                records.append(dict(index=int(i), parent=state.get('parent'),
                    source_triangle_indices=state.get('source_triangle_indices'),
                    old_volume=float(volume[i]), new_volume=float(new_volume[i]) if np.isfinite(new_volume[i]) else None,
                    incoming_volume_rate=float(assembled['incoming_volume_rate'][i]) if i < len(pools) and 'incoming_volume_rate' in assembled else None,
                    outgoing_volume_rate=float(assembled['outgoing_volume_rate'][i]) if i < len(pools) and 'outgoing_volume_rate' in assembled else None,
                    gross_incoming_volume_rate=float(assembled['gross_incoming_volume_rate'][i]) if 'gross_incoming_volume_rate' in assembled else None,
                    gross_outgoing_volume_rate=float(assembled['gross_outgoing_volume_rate'][i]) if 'gross_outgoing_volume_rate' in assembled else None))
            raise SourceUpdateFailure('Coupled source volume is not positive/finite; no repair', dict(regions=records))
        # Column j contains new_volume[j] times the donor operator. Dividing
        # rows by new_volume is a solve normalization, not a depth floor.
        timed_residual = front_timed_remainder(assembled, volume, new_volume) if 'front_forces' in assembled else residual
        rhs = momentum+duration*timed_residual
        if gross_donors:
            new_momentum = np.linalg.solve(matrix, rhs)
            new_velocity = new_momentum/new_volume[:, None]
            momentum_residual = matrix@new_momentum-rhs
            normalized = None
        else:
            velocity_matrix = matrix*new_volume[None, :]-duration*exchange
            normalized = velocity_matrix/new_volume[:, None]
            normalized_rhs = rhs/new_volume[:, None]
            if not np.isfinite(normalized).all() or not np.isfinite(normalized_rhs).all():
                raise ValueError('Coupled momentum normalization exceeds represented range')
            new_velocity = np.linalg.solve(normalized, normalized_rhs)
            new_momentum = new_volume[:, None]*new_velocity
            momentum_residual = velocity_matrix@new_velocity-rhs
        value = np.column_stack((new_volume, new_momentum))
    except np.linalg.LinAlgError as exc:
        raise ValueError('Coupled source transfer solve failed') from exc
    if not np.isfinite(value).all() or not np.isfinite(new_velocity).all() or np.any(value[:, 0] <= 0):
        raise ValueError('Coupled source state is not positive/finite; no repair')
    solve_error = max(float(np.max(abs(matrix@new_volume-volume))),
                      float(np.max(abs(momentum_residual))))
    if solve_error >= 1e-10:
        raise ValueError(f'Coupled source true residual failed: {solve_error:.17g}')
    fastest = int(np.argmax(np.linalg.norm(new_velocity, axis=1)))
    local = dict(index=fastest, old_volume=float(volume[fastest]), new_volume=float(new_volume[fastest]),
        old_velocity=velocity[fastest].tolist(), new_velocity=new_velocity[fastest].tolist(),
        explicit_remainder=residual[fastest].tolist(), momentum_rhs=rhs[fastest].tolist(),
        time_averaged_remainder=timed_residual[fastest].tolist(),
        normalized_diagonal=float(normalized[fastest, fastest]) if normalized is not None else None,
        normalized_row_sum=float(normalized[fastest].sum()) if normalized is not None else None,
        mass_matrix_diagonal=float(matrix[fastest, fastest]))
    if fastest < len(pools) and 'explicit_force_parts' in assembled:
        local['explicit_force_parts'] = {k: v[fastest].tolist() for k, v in assembled['explicit_force_parts'].items()}
    return dict(volume=value[:, 0], momentum=value[:, 1:],
        audit=dict(original_mass_rate_error=rate_error, solve_residual=solve_error,
            original_momentum_rate_error=momentum_rate_error, residual_assembly=residual_assembly,
            front_force_timing='matched-to-donor-mass' if 'front_forces' in assembled else 'supplied-explicit',
            matrix_size=count, transfer_count=len(transfers),
            momentum_uses_mass_matrix=gross_donors,
            mass_transport='gross-donor' if gross_donors else 'net-transfer',
            implicit_velocity_exchanges=0 if gross_donors else len(assembled.get('velocity_exchanges', [])),
            fastest_region_budget=local,
            minimum_volume=float(value[:, 0].min()),
            pressure_and_bed_work_remain_explicit=True,
            full_rational_or_energy_or_gameplay_accepted=False))
