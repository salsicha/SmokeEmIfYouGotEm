"""Finite source-front controls, never full nonlinear or gameplay acceptance."""
import math

from subcell_source_activation import assembly, attempt


def audit_activation(partition):
    assembled = assembly(partition)
    records = [attempt(partition, duration, assembled=assembled)['audit']
               for duration in (.02, .001, .0001, .00001, .000001)]
    return dict(original_region_count=len(partition.pools),
        receiving_regions=len(assembled['new_region_rates']),
        receiving_parent_cells=sorted(set(r['parent'] for r in assembled['new_region_rates'])),
        positive_dry_front_entries=len(assembled['fronts']),
        net_mass_rate=assembled['net_mass_rate'],
        momentum_boundary_bed_error=assembled['momentum_boundary_bed_error'],
        net_volume_limit=assembled['net_volume_limit'],
        receiving_rate_records=[dict(parent=r['parent'], source_triangle_indices=r['source_triangle_indices'],
            volume_rate=r['volume_rate'], momentum_rate=r['momentum_rate'].tolist(),
            incoming_energy_flux=r['incoming_energy_flux']) for r in assembled['new_region_rates']],
        front_records=assembled['fronts'], attempts=records,
        twenty_ms_candidate_passed=records[0]['candidate_accepted'],
        probe='Independent attempts from the same source snapshot, NOT successive accepted history or a selected tiny production timestep',
        nonlinear_model_or_time_history_or_native_or_gameplay_accepted=False)


def audit_history(partition, steps, duration=.02, scheme='explicit'):
    """Advance only accepted candidates, stop at the first failure, never retry.

    This exposes subsequent-step failures hidden by independent snapshot probes.
    Its fixed requested duration is not replaced with a positivity-bound step.
    """
    if isinstance(steps, bool) or not isinstance(steps, int) or steps <= 0:
        raise ValueError('Positive integer step count required')
    if not math.isfinite(duration) or duration <= 0:
        raise ValueError('Positive finite duration required')
    if scheme not in ('explicit', 'coupled-frozen'):
        raise ValueError('Unknown source-front update scheme')
    current, records = partition, []
    accepted = 0
    for index in range(steps):
        try:
            result = attempt(current, duration, scheme=scheme)
        except ValueError as exc:
            records.append(dict(step=index+1, start_time=index*duration,
                candidate_accepted=False, rejection=str(exc), failure_phase='assembly'))
            break
        records.append(dict(result['audit'], step=index+1, start_time=index*duration))
        if not result['audit']['candidate_accepted']:
            break
        if result['state'] is None:
            raise ValueError('Accepted candidate must supply its actual state')
        current = result['state']
        accepted += 1
    return dict(requested_steps=steps, duration=duration, scheme=scheme, accepted_steps=accepted,
        advanced_seconds=accepted*duration, all_requested_steps_passed=accepted == steps,
        original_region_count=len(partition.pools), final_region_count=len(current.pools),
        attempts=records,
        probe='Successive nondispersive candidates; stop at first failure without timestep reduction or state repair',
        nonlinear_model_or_native_or_gameplay_accepted=False)
