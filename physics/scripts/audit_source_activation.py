"""Independent finite-duration attempts from the unchanged captured source state."""
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
