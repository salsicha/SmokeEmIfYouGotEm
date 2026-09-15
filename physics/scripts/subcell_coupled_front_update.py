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
"""
import numpy as np


def coupled_update(assembled, duration):
    if not np.isfinite(duration) or duration <= 0:
        raise ValueError('Positive finite duration required')
    pools, new = assembled['partition'].pools, assembled['new_region_rates']
    count = len(pools)+len(new)
    volume, momentum = np.zeros(count), np.zeros((count, 2))
    volume[:len(pools)] = [p['volume'] for p in pools]
    momentum[:len(pools)] = [p['momentum'] for p in pools]
    generator = np.zeros((count, count))
    for owner, other, flux in assembled['transfers']:
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
    for left, right, conductance in assembled.get('velocity_exchanges', []):
        if (left == right or not 0 <= left < len(pools) or not 0 <= right < len(pools)
                or not np.isfinite(conductance) or conductance <= 0):
            raise ValueError('Positive conservative velocity exchange required')
        exchange[left, left] -= conductance
        exchange[right, right] -= conductance
        exchange[left, right] += conductance
        exchange[right, left] += conductance
    velocity = np.divide(momentum, volume[:, None], out=np.zeros_like(momentum), where=volume[:, None] > 0)
    residual = momentum_rate-generator@momentum-exchange@velocity
    matrix = np.eye(count)-duration*generator
    if not np.isfinite(matrix).all() or not np.isfinite(residual).all():
        raise ValueError('Coupled source transfer exceeds represented range')
    rate_error = float(np.max(abs(generator@volume-volume_rate)))
    if rate_error >= 1e-10:
        raise ValueError('Source transfer ledger does not reproduce original mass rates')
    try:
        new_volume = np.linalg.solve(matrix, volume)
        if not np.isfinite(new_volume).all() or np.any(new_volume <= 0):
            raise ValueError('Coupled source volume is not positive/finite; no repair')
        # Column j contains new_volume[j] times the donor operator. Dividing
        # rows by new_volume is a solve normalization, not a depth floor.
        velocity_matrix = matrix*new_volume[None, :]-duration*exchange
        rhs = momentum+duration*residual
        normalized = velocity_matrix/new_volume[:, None]
        normalized_rhs = rhs/new_volume[:, None]
        if not np.isfinite(normalized).all() or not np.isfinite(normalized_rhs).all():
            raise ValueError('Coupled momentum normalization exceeds represented range')
        new_velocity = np.linalg.solve(normalized, normalized_rhs)
        value = np.column_stack((new_volume, new_volume[:, None]*new_velocity))
    except np.linalg.LinAlgError as exc:
        raise ValueError('Coupled source transfer solve failed') from exc
    if not np.isfinite(value).all() or np.any(value[:, 0] <= 0):
        raise ValueError('Coupled source state is not positive/finite; no repair')
    solve_error = max(float(np.max(abs(matrix@new_volume-volume))),
                      float(np.max(abs(velocity_matrix@new_velocity-rhs))))
    if solve_error >= 1e-10:
        raise ValueError('Coupled source true residual failed')
    return dict(volume=value[:, 0], momentum=value[:, 1:],
        audit=dict(original_mass_rate_error=rate_error, solve_residual=solve_error,
            matrix_size=count, transfer_count=len(assembled['transfers']),
            implicit_velocity_exchanges=len(assembled.get('velocity_exchanges', [])),
            minimum_volume=float(value[:, 0].min()),
            pressure_and_bed_work_remain_explicit=True,
            full_rational_or_energy_or_gameplay_accepted=False))
