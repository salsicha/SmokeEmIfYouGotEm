"""Full source-metric Gauss time candidate on unchanged complete wet support.

Three-stage, sixth-order Gauss collocation, solved by bounded fixed-point
iteration. Not an exactly energy-preserving method: finite energy is measured
and a failing step rejects, without projection, rescaling, retry or dt changes.
Every force evaluation retains the original 40-CG pressure solve. The outer
iteration cost is additional and has NO native/runtime-budget qualification.
Wet/front topology and actual open river boundaries remain unsupported.
"""
import numpy as np

from subcell_nonlinear_metric_stage import stage
from subcell_wet_pool_primal_energy import evaluate
from subcell_metric_force_ledger import Ledger, zero
from subcell_source_activation import base_energy


ROOT15 = np.sqrt(15.)
A = np.array([[5/36, 2/9-ROOT15/15, 5/36-ROOT15/30],
              [5/36+ROOT15/24, 2/9, 5/36-ROOT15/24],
              [5/36+ROOT15/30, 2/9+ROOT15/15, 5/36]])
B = np.array([5/18, 4/9, 5/18])


def state_at(partition, volume, momentum):
    """New source geometry and explicit physical state; input remains untouched."""
    result = partition.volume_probe(volume)
    p = np.asarray(momentum, float)
    if p.shape != (len(result.pools), 1, 2) or not np.isfinite(p).all():
        raise ValueError('Finite physical momentum per original pool required')
    result.reassembled_momenta = np.zeros((*partition.patch.shape, 2))
    for pool, value in zip(result.pools, p[:, 0]):
        pool['momentum'] = value.copy()
        result.reassembled_momenta.reshape(-1, 2)[pool['parent']] += value
    return result


def advance(partition, physical_momentum, dt):
    if not np.isfinite(dt) or dt <= 0:
        raise ValueError('Positive finite time step required')
    p = np.asarray(physical_momentum, float)
    n = len(partition.pools)
    if p.shape != (n, 1, 2) or not np.isfinite(p).all():
        raise ValueError('Finite physical momentum per original pool required')
    volume = np.array([pool['volume'] for pool in partition.pools])
    initial = state_at(partition, volume, p)
    initial_measurement = evaluate(initial, p)
    initial_energy = initial_measurement['total']
    initial_base_energy = base_energy(initial)['total']
    v_nodes = np.broadcast_to(volume, (3, n)).copy()
    p_nodes = np.broadcast_to(p, (3, n, 1, 2)).copy()
    maximum_pressure_residual = 0.
    for iteration in range(40):
        records = [stage(state_at(partition, v, q), q) for v, q in zip(v_nodes, p_nodes)]
        maximum_pressure_residual = max(maximum_pressure_residual,
                                        max(r['maximum_solve_residual'] for r in records))
        vd = np.array([r['volume_rate'][:, 0] for r in records])
        pd = np.array([r['physical_momentum_rate'] for r in records])
        next_v = volume+dt*np.einsum('ij,jn->in', A, vd)
        next_p = p+dt*np.einsum('ij,jnab->inab', A, pd)
        residual = max(float(np.max(abs(next_v-v_nodes))), float(np.max(abs(next_p-p_nodes))))
        if not np.isfinite(residual):
            raise ValueError('Nonlinear collocation exceeds represented range')
        if residual <= 1e-12:
            break
        v_nodes, p_nodes = next_v, next_p
    else:
        raise ValueError('Nonlinear collocation failed its original 40-sweep budget')
    new_v = volume+dt*np.einsum('i,in->n', B, vd)
    new_p = p+dt*np.einsum('i,inab->nab', B, pd)
    endpoint = state_at(partition, new_v, new_p)
    # Validate complete endpoint support too, not only the internal time nodes.
    endpoint_rate = stage(endpoint, new_p)
    final_measurement = evaluate(endpoint, new_p)
    final_energy = final_measurement['total']
    base_energy_change = base_energy(endpoint)['total']-initial_base_energy
    impulse = zero(partition)
    for weight, record in zip(B, records):
        impulse = impulse+Ledger(record['physical_momentum_faces'], record['bed_force'],
                                 record['wall_force'])*(dt*weight)
    errors = dict(mass_error=float(np.sum(new_v-volume)),
                  local_momentum_impulse_error=float(np.max(abs(new_p-p-impulse.action()))),
                  total_momentum_impulse_error=float(np.max(abs((new_p-p)[:, 0].sum(axis=0)
                                                              -(impulse.bed+impulse.wall).sum(axis=0)))),
                  energy_change=float(final_energy-initial_energy),
                  positive_energy_contraction_error=max(initial_measurement['positive_energy_contraction_error'],
                                                        final_measurement['positive_energy_contraction_error']))
    if not np.isfinite(list(errors.values())).all() or max(abs(v) for v in errors.values()) > 1e-10:
        raise ValueError(f'Finite nonlinear source step rejected; no state repair: {errors}')
    return dict(partition=endpoint, volume=new_v, physical_momentum=new_p,
                dt_seconds=float(dt), collocation_sweeps=iteration+1,
                collocation_residual=residual, initial_energy=float(initial_energy),
                final_energy=float(final_energy), integrated_face_impulses=impulse.faces,
                nondispersive_energy_change=float(base_energy_change),
                original_nondispersive_both_energy_control_passed=(base_energy_change <= 1e-10
                                                                    and errors['energy_change'] <= 1e-10),
                integrated_bed_impulse=impulse.bed, integrated_wall_impulse=impulse.wall,
                maximum_solve_residual=max(maximum_pressure_residual, endpoint_rate['maximum_solve_residual']),
                **errors, full_time_or_topology_or_open_or_native_or_gameplay_accepted=False)


def history(partition, steps, dt, *, on_step=None):
    """Bounded full-rate history; retain failures and cumulative original budgets."""
    if type(steps) is not int or steps < 1:
        raise ValueError('Positive integer time-step count required')
    if not np.isfinite(dt) or dt <= 0 or (on_step is not None and not callable(on_step)):
        raise ValueError('Positive finite duration and optional step observer required')
    original_p = np.array([p['momentum'] for p in partition.pools])[:, None, :]
    original_v = np.array([p['volume'] for p in partition.pools])
    original_energy = evaluate(partition, original_p)['total']
    current, momentum = partition, original_p
    impulse = np.zeros_like(original_p)
    base_change = 0.
    rows, failure = [], None
    for index in range(steps):
        try:
            result = advance(current, momentum, dt)
            integrated = Ledger(result['integrated_face_impulses'], result['integrated_bed_impulse'],
                                result['integrated_wall_impulse']).action()
            cumulative_impulse = impulse+integrated
            cumulative = dict(cumulative_mass_error=float((result['volume']-original_v).sum()),
                cumulative_momentum_impulse_error=float(np.max(abs(result['physical_momentum']-original_p-cumulative_impulse))),
                cumulative_full_energy_change=float(result['final_energy']-original_energy))
            if max(abs(value) for value in cumulative.values()) > 1e-10:
                raise ValueError(f'Cumulative original time budgets failed: {cumulative}')
            row = {k: v for k, v in result.items() if k not in ('partition', 'volume', 'physical_momentum',
                'integrated_face_impulses', 'integrated_bed_impulse', 'integrated_wall_impulse')}
            base_change += result['nondispersive_energy_change']
            row.update(step=index+1, time_seconds=(index+1)*dt, **cumulative,
                cumulative_nondispersive_energy_change=float(base_change),
                cumulative_original_both_energy_control_passed=(base_change <= 1e-10
                                                                 and cumulative['cumulative_full_energy_change'] <= 1e-10),
                maximum_speed_mps=float(np.max(np.linalg.norm(result['physical_momentum'][:, 0]
                                                              /result['volume'][:, None], axis=1))))
            rows.append(row)
            current, momentum, impulse = result['partition'], result['physical_momentum'], cumulative_impulse
        except ValueError as exc:
            failure = dict(step=index+1, reason=str(exc))
            break
        if on_step is not None:
            on_step(row)
    return dict(requested_steps=steps, completed_steps=len(rows), dt_seconds=float(dt),
                closed_fixed_support_time_controls_passed=failure is None, failure=failure,
                records=rows, final_volume=[p['volume'] for p in current.pools],
                final_physical_momentum=momentum[:, 0].tolist(),
                full_time_or_topology_or_open_or_native_or_gameplay_accepted=False)
