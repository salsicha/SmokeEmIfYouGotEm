"""Frozen-network draining candidate with conservative implicit mixing.

The event mass law is piecewise constant capacity, not nonlinear depth-dependent
Rusanov evolution. Body forces follow source-volume exposure; side-owned
pressure follows the active time of its directed donor. This is
an explicit research alternative; finite energy and full-model gates still apply.
"""
from fractions import Fraction as F
import math
import numpy as np

from subcell_transfer_events import integrate


def event_update(assembled, duration):
    if assembled.get('face_scheme') != 'donor' or assembled.get('gross_donor_transfers') is None:
        raise ValueError('Original donor-face assembly required for event transport')
    pools, receipts = assembled['partition'].pools, assembled['new_region_rates']
    old_count, count = len(pools), len(pools)+len(receipts)
    volume = [p['volume'] for p in pools]+[0.]*len(receipts)
    momentum = np.array([p['momentum'] for p in pools]+[np.zeros(2) for _ in receipts])
    transfers = assembled['gross_donor_transfers']
    # Check the original graph, before applying any availability event.
    dv = np.zeros(count)
    dp = np.zeros((count, 2))
    for a, b, rate in transfers:
        dv[a] -= rate; dv[b] += rate
        advected = rate*(momentum[a]/volume[a])
        dp[a] -= advected; dp[b] += advected
    expected_v = np.r_[assembled['volume_rate'], [r['volume_rate'] for r in receipts]]
    expected_p = np.concatenate((assembled['momentum_rate'], np.array([r['momentum_rate'] for r in receipts]).reshape(-1, 2)))
    parts = assembled['explicit_force_parts']
    base_force = np.zeros((count, 2))
    base_force[:old_count] = parts['bed']+parts['wall']
    for origin, a, b, force in assembled['pressure_forces']:
        base_force[a] -= force; base_force[b] += force
    for a, b, force in assembled['front_forces']:
        base_force[a] -= force; base_force[b] += force
    if np.max(abs(dv-expected_v)) >= 1e-10 or np.max(abs(dp+base_force-expected_p)) >= 1e-10:
        raise ValueError('Event face ledger does not reproduce original rates')
    result = integrate(volume, transfers, duration)
    exact_v = result['volume']
    new_v = np.array(list(map(float, exact_v)))
    if not np.isfinite(new_v).all() or any(v > 0 and n <= 0 for v, n in zip(exact_v, new_v)):
        raise ValueError('Positive event volume exceeds represented range; no deletion')
    weights = [result['exposure'][i]/result['original'][i] for i in range(old_count)]
    impulse = [[F(0), F(0)] for _ in range(count)]
    boundary = [F(0), F(0)]
    for i in range(old_count):
        for axis in range(2):
            value = (F(float(parts['bed'][i, axis]))+F(float(parts['wall'][i, axis])))*weights[i]
            impulse[i][axis] += value
            boundary[axis] += value
    for origin, a, b, force in assembled['pressure_forces']:
        if not np.any(force):
            continue
        if result['capacity'][origin] <= 0:
            raise ValueError('Positive side pressure requires its original positive donor')
        active_time = result['outgoing'][origin]/result['capacity'][origin]
        for axis in range(2):
            value = F(float(force[axis]))*active_time
            impulse[a][axis] -= value; impulse[b][axis] += value
    for a, b, force in assembled['front_forces']:
        # A Riemann front's nonadvective impulse is specified per emitted
        # parcel. Growing owner volume must not amplify it independently of
        # the frozen mass capacity. This is the actual integrated active time.
        active_time = result['outgoing'][a]/result['capacity'][a]
        for axis in range(2):
            value = F(float(force[axis]))*active_time
            impulse[a][axis] -= value; impulse[b][axis] += value
    # Implicit mixing of the exactly transferred parcels. D=Vold+incoming
    # equals Vnew+outgoing, including nodes that have dried. No 1/Vnew occurs.
    diagonal = [a+b for a, b in zip(result['original'], result['incoming'])]
    active = [i for i, d in enumerate(diagonal) if d > 0]
    positions = {node: i for i, node in enumerate(active)}
    matrix = np.eye(len(active))
    rhs = np.zeros((len(active), 2))
    for i in active:
        for axis in range(2):
            rhs[positions[i], axis] = float((F(float(momentum[i, axis]))+impulse[i][axis])/diagonal[i])
    for a, b, amount in result['transfers']:
        matrix[positions[b], positions[a]] -= float(amount/diagonal[b])
    if not np.isfinite(matrix).all() or not np.isfinite(rhs).all():
        raise ValueError('Event mixing exceeds represented range')
    velocity = np.zeros((count, 2))
    try:
        velocity[active] = np.linalg.solve(matrix, rhs)
    except np.linalg.LinAlgError as exc:
        raise ValueError('Event mixing solve failed') from exc
    new_p = new_v[:, None]*velocity
    if not np.isfinite(velocity).all() or not np.isfinite(new_p).all():
        raise ValueError('Nonfinite event momentum; no velocity cap')
    residual_terms = [[[-F(float(momentum[i, axis]))-impulse[i][axis],
                       F(float(velocity[i, axis]))*diagonal[i]] for axis in range(2)] for i in range(count)]
    for a, b, amount in result['transfers']:
        for axis in range(2):
            residual_terms[b][axis].append(-amount*F(float(velocity[a, axis])))
    error = max(abs(float(sum(terms, F(0)))) for row in residual_terms for terms in row)
    if error >= 1e-10:
        raise ValueError('Event mixing original-momentum residual failed')
    positive = np.flatnonzero(new_v > 0)
    fastest = int(positive[np.argmax(np.linalg.norm(velocity[positive], axis=1))])
    local = dict(index=fastest, old_region=fastest < old_count, old_volume=volume[fastest],
        new_volume=float(new_v[fastest]), new_velocity=velocity[fastest].tolist(),
        integrated_impulse=[float(x) for x in impulse[fastest]],
        mixture_amount=float(diagonal[fastest]), normalized_rhs=rhs[positions[fastest]].tolist())
    return dict(volume=new_v, momentum=new_p, boundary_impulse=np.array(list(map(float, boundary))),
        audit=dict(mass_law='exact constant-capacity network events; not nonlinear face evolution',
            momentum_law='implicit mixing of integrated directed transfers',
            force_law='body force uses volume exposure; side pressure uses donor active time',
            front_force_law='same integrated active time as emitted front mass',
            fastest_region_budget=local,
            original_mass_rate_error=float(np.max(abs(dv-expected_v))),
            original_momentum_rate_error=float(np.max(abs(dp+base_force-expected_p))),
            solve_residual=error, exact_mass_ledger_passed=True,
            dry_events=[dict(time_seconds=float(e['time']), exact_time=str(e['time']), regions=e['regions']) for e in result['events']],
            zero_regions=[i for i, v in enumerate(exact_v) if v == 0],
            full_rational_or_energy_or_gameplay_accepted=False))
