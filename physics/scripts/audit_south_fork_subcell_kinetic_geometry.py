"""Captured-cell pressure kinetic coefficients, NOT evolved river acceptance."""
import argparse
import json
from pathlib import Path
from fractions import Fraction

import numpy as np

from audit_south_fork_subcell_energy_flux import ROOT, read, sha, exact_cells
from south_fork_registered_mesh import RegisteredMeshSampler
from subcell_geometry_patch import SubcellGeometryPatch
from subcell_pressure_kinetic_geometry import local_form, quadrature
from subcell_wet_connectivity import components
from subcell_wet_pool_partition import WetPoolPartition
from subcell_wet_pool_pressure import WetPoolPressureSystem
from audit_wet_pool_pressure_rate import audit_direction
from audit_wet_pool_transport import audit_transport, audit_internal_regions
from audit_source_activation import audit_activation, audit_history
from audit_source_time_refinement import audit_refinement
from audit_primal_metric_direction import audit_direction as audit_primal_direction
from audit_source_auxiliary_transport import audit_components as audit_auxiliary_components
from audit_source_representation import audit_representation
from finite_depth_pressure_reference import LENGTHS, WEIGHTS


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--atlas', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--pool-pressure', action='store_true', help='Also audit both original poles on separated fixed wet pools')
    parser.add_argument('--source-representation', action='store_true', help='Audit exact source polygons and relative metrics against rational integrals')
    parser.add_argument('--exact-pool-geometry', action='store_true', help='Use exact source storage, datums, traces and internal edges throughout the pool path; implies --pool-pressure')
    parser.add_argument('--pool-direction', action='store_true', help='Also verify analytic volume/velocity directions; implies --pool-pressure')
    parser.add_argument('--pool-primal-direction', action='store_true', help='Verify changing-volume physical/canonical inverse metric on the original moving state; implies --pool-pressure')
    parser.add_argument('--pool-auxiliary-components', action='store_true', help='Verify original-source auxiliary face transport and geometric commutator; NOT a full force; implies --pool-pressure')
    parser.add_argument('--pool-transport', action='store_true', help='Audit physical energy and pool-aware base flux support; implies --pool-pressure')
    parser.add_argument('--pool-internal', action='store_true', help='Also audit controlled internal source-region subdivision; implies --pool-transport')
    parser.add_argument('--pool-activation', action='store_true', help='Attempt finite source-front activation with strict state/energy rejection; implies --pool-pressure')
    parser.add_argument('--pool-history-steps', type=int, default=0, help='Successive 20ms source-front attempts, stopping on rejection; implies --pool-pressure')
    parser.add_argument('--pool-history-scheme', choices=('explicit', 'coupled-frozen', 'coupled-donor', 'coupled-gross-donor', 'coupled-events'), default='explicit')
    parser.add_argument('--pool-refinement-steps', type=int, default=0, help='Compare this many 20ms steps with twice/four times as many steps over the SAME horizon; implies --pool-pressure')
    parser.add_argument('--pool-refinement-levels', type=int, default=3, help='Number of successive timestep halvings including the original level (at least three)')
    args = parser.parse_args()
    if args.pool_history_steps < 0:
        parser.error('--pool-history-steps must be nonnegative')
    if args.pool_refinement_steps < 0:
        parser.error('--pool-refinement-steps must be nonnegative')
    if args.pool_refinement_levels < 3:
        parser.error('--pool-refinement-levels must be at least three')
    args.pool_transport = args.pool_transport or args.pool_internal
    args.pool_pressure = args.pool_pressure or args.pool_direction or args.pool_primal_direction or args.pool_auxiliary_components or args.pool_transport or args.pool_activation or args.pool_history_steps > 0 or args.pool_refinement_steps > 0 or args.exact_pool_geometry
    if args.report.exists():
        raise FileExistsError(args.report)
    base = ROOT/'physics/data/real_world/south_fork_american_chili_bar/reconstruction_2026_09/full_reach'
    geometry_path = base/'composite_terrain/manifest.json'
    coordinate_path = base/'hydraulic_regions_context/coordinate_map.json'
    mesh_path = base/'composite_terrain/troublemaker_registered_source.npz'
    geometry, coordinates, atlas = read(geometry_path), read(coordinate_path), read(args.atlas)
    if (sha(mesh_path) != geometry['registered_rapid_sha256']
            or atlas['schema'] != 'raftsim.cartesian_state_atlas.v1' or atlas['grid_spacing_m'] != 1.
            or atlas['source_elevation_datum_m'] != coordinates['vertical_datum_m']):
        raise ValueError('Changed registered source or unsupported grid/datum')
    yy, xx = np.indices((16, 16))
    offsets = np.stack((xx.ravel(), yy.ravel()), axis=1)
    cells = exact_cells(np.array([-5439., 3593.])+offsets,
        [tile['origin_m'] for tile in atlas['tiles']], atlas['tile_shape'], 1.)
    if (cells < 0).any():
        raise ValueError('Missing actual source cell')
    origins = np.array([tile['origin_m'] for tile in atlas['tiles']])[cells[:, 0]]+cells[:, [2, 1]]
    if not np.array_equal(origins, origins[0]+offsets):
        raise ValueError('Source is not the original regular lattice')
    paths = [args.atlas, geometry_path, coordinate_path, mesh_path, Path(__file__)]
    paths += [ROOT/'physics/scripts'/name for name in (
        'subcell_pressure_kinetic_geometry.py', 'triangle_cell_storage.py', 'subcell_geometry_patch.py',
        'triangle_face_section.py', 'south_fork_registered_mesh.py', 'audit_south_fork_subcell_energy_flux.py',
        'subcell_wet_connectivity.py', 'subcell_wet_pool_partition.py', 'subcell_wet_pool_pressure.py',
        'subcell_wet_pool_pressure_rate.py', 'audit_wet_pool_pressure_rate.py', 'subcell_mechanical_energy.py',
        'subcell_wet_pool_primal_energy.py', 'subcell_wet_pool_transport.py', 'audit_wet_pool_transport.py',
        'rational_primal_energy.py', 'subcell_energy_flux.py',
        'subcell_source_region_faces.py',
        'subcell_dry_front_flux.py', 'subcell_source_activation.py', 'audit_source_activation.py',
        'audit_source_time_refinement.py',
        'subcell_primal_metric_rate.py', 'audit_primal_metric_direction.py',
        'subcell_auxiliary_transport.py', 'audit_source_auxiliary_transport.py',
        'subcell_source_curvature.py',
        'subcell_exact_source_faces.py',
        'subcell_coupled_front_update.py',
        'subcell_transfer_events.py', 'subcell_event_front_update.py',
        'subcell_donor_face_flux.py',
        'subcell_exact_geometry.py', 'audit_source_representation.py',
        'subcell_source_face_section.py',
        'subcell_source_frames.py',
        'subcell_implicit_transport.py',
        'finite_depth_pressure_reference.py', 'pressure_cg_range_reference.py')]
    hashes = {str(path.resolve()): sha(path) for path in paths}
    fields = {}
    for key in (('h', 'bed', 'u', 'v') if args.pool_pressure else ('h', 'bed')):
        record = atlas['arrays'][key]
        path = (args.atlas.parent/record['file']).resolve()
        if sha(path) != record['sha256']:
            raise ValueError('Changed source array '+key)
        source = np.load(path, mmap_mode='r', allow_pickle=False)
        if source.shape != tuple(record['shape']) or source.dtype != np.dtype('<f8'):
            raise ValueError('Malformed source array '+key)
        tile, row, col = cells.T
        fields[key] = np.array(source[tile*atlas['tile_shape'][0]+row, col])
        if not np.isfinite(fields[key]).all():
            raise ValueError('Nonfinite actual source cell')
        hashes[str(path)] = record['sha256']
    with np.load(mesh_path, allow_pickle=False) as mesh:
        terrain = RegisteredMeshSampler(mesh)
        authority = np.asarray(mesh['authority']).ravel().copy()
    shift = np.array(coordinates['world_origin_utm_m'])-geometry['rapid_origin_utm_m']
    patch = SubcellGeometryPatch(terrain, origins[0]+shift, (16, 16), relative_stages=True,
                                 exact_sources=args.exact_pool_geometry)
    representation = (audit_representation(terrain, origins[0]+shift, (16, 16), [1., 1.], fields['h'])
                      if args.source_representation else None)
    source_bed = fields['bed']+atlas['source_elevation_datum_m']-geometry['rapid_datum_navd88_m']
    exact_bed = terrain.sample(*(origins+shift).T)
    if not np.allclose(source_bed, exact_bed, atol=1e-9, rtol=0):
        raise ValueError('Captured and hydraulic center beds differ')
    records, unsupported, provenance = [], [], {}
    for index, (cell, volume) in enumerate(zip(patch.cells, fields['h'])):
        if volume < 0:
            raise ValueError('Negative original source volume is not a dry cell')
        if volume == 0:
            unsupported.append(dict(index=index, reason='dry; no inverse-mass or wet-front closure'))
            continue
        form = local_form(cell, volume)
        connectivity = components(terrain, cell, origins[index]+shift, [1., 1.], form['stage_offset'])
        triangle_volume, triangle_wet_area = cell._triangle_volume_and_wet_area(form['stage_offset'], cell.relative_levels)
        cell_codes = set()
        for source_id, tv, tw in zip(cell.source_triangle_indices, triangle_volume, triangle_wet_area):
            if tw == 0:
                continue
            codes = sorted(set(map(int, authority[terrain.faces[source_id]])))
            cell_codes.update(codes)
            key = ','.join(map(str, codes))
            entry = provenance.setdefault(key, dict(wet_projected_area_m2=0., volume_m3=0.))
            entry['wet_projected_area_m2'] += float(tw)
            entry['volume_m3'] += float(tv)
        weights, h, slopes = quadrature(cell, form['stage_offset'])
        average_slope = np.sum((weights*h)[:, None]*slopes, axis=0)/volume
        slope_gram = form['gram'][1:, 1:]
        collapsed_slope_gram = 3*volume*np.outer(average_slope, average_slope)
        covariance = slope_gram-collapsed_slope_gram
        # This exact wet-volume-weighted mean is a best aggregate diagnostic,
        # NOT an assertion that it is the actual runtime coarse slope stencil.
        slope_trace = float(np.trace(slope_gram))
        lost_fraction = float(np.trace(covariance)/slope_trace) if slope_trace > 0 else 0.
        step = volume*1e-5
        low, high = local_form(cell, volume-step), local_form(cell, volume+step)
        fd = (high['gram']-low['gram'])/(2*step)
        derivative_error = float(np.max(abs(fd-form['volume_derivative']))
                                 /max(1., np.max(abs(form['volume_derivative']))))
        relative_volume_error = form['volume_error']/volume
        if relative_volume_error > 1e-10 or derivative_error > 1e-6:
            raise ValueError('Actual exact-volume/kinetic-tangent geometry control failed')
        mean_wet_depth_cubic = volume*(volume/form['wet_area'])**2
        records.append(dict(index=index, volume_m3=float(volume), wet_area_m2=form['wet_area'],
            wet_connectivity=connectivity,
            wet_source_vertex_authority_codes=sorted(cell_codes),
            original_triangle_count=len(cell.areas), factor_row_count=len(form['factor']),
            relative_volume_error=relative_volume_error, relative_kinetic_tangent_error=derivative_error,
            slope_variance_energy_fraction=lost_fraction,
            minimum_slope_covariance_eigenvalue=float(np.linalg.eigvalsh(covariance).min()),
            exact_cubic_depth_moment=float(form['depth_moments'][3]),
            mean_wet_depth_cubic_moment=mean_wet_depth_cubic,
            mean_depth_cubic_loss_fraction=float(1-mean_wet_depth_cubic/form['depth_moments'][3]),
            gram=form['gram'].tolist(), volume_derivative=form['volume_derivative'].tolist()))
    if not records:
        raise ValueError('No positive actual cells evaluated')
    pressure, direction, transport, internal, activation, history, refinement, primal_direction, auxiliary_components = (None,)*9
    if args.pool_pressure:
        volume = fields['h'].reshape(patch.shape)
        momentum = volume[..., None]*np.stack((fields['u'], fields['v']), axis=-1).reshape(*patch.shape, 2)
        pools = WetPoolPartition(patch, terrain, origins[0]+shift, volume, momentum)
        rhs = np.array([pool['momentum']/np.sqrt(pool['volume']) for pool in pools.pools])[:, None, :]
        pole_records = []
        for length, weight in zip(LENGTHS, WEIGHTS):
            system = WetPoolPressureSystem(pools, float(length))
            value, stats = system.solve(rhs)
            # Independent bounded dense assembly from the local Gram tensors,
            # not the factor-action routine used by CG. This is an audit oracle
            # only and never replaces the 40-iteration result.
            if len(pools.pools) > 1024:
                raise ValueError('Dense pressure oracle exceeds its bounded audit scope')
            dense = np.eye(2*len(pools.pools))
            for index, pool in enumerate(pools.pools):
                mapping = system.row_maps[index]
                cols = sorted(set(mapping) | {2*index, 2*index+1})
                jet = np.zeros((3, len(cols)))
                for j, col in enumerate(cols):
                    jet[0, j] = mapping.get(col, 0.)/system.root[col//2]
                    if col//2 == index:
                        jet[1+col%2, j] = 1/system.root[index]
                dense[np.ix_(cols, cols)] += length*(jet.T@pool['form']['gram']@jet)
            expected = np.linalg.solve(dense, rhs.ravel()).reshape(rhs.shape)
            error = float(np.max(abs(expected-value))/max(1., np.max(abs(expected))))
            action_error = float(np.max(abs(dense@rhs.ravel()-system.apply(rhs).ravel()))
                                 /max(1., np.max(abs(dense@rhs.ravel()))))
            pole_records.append(dict(length=float(length), weight=float(weight), **stats,
                scaled_dense_solution_error=error, scaled_dense_action_error=action_error,
                solve_gate_passed=stats['relative_residual'] < 2e-5,
                independent_solution_gate_passed=error < 1e-10,
                shared_column_partition_error=system.maximum_shared_column_partition_error,
                wall_column_partition_error=system.maximum_wall_column_partition_error,
                shared_wet_subsegments=len(system.connections), reflecting_wall_subsegments=len(system.walls),
                direct_same_cell_pool_connections=sum(pools.pools[f['left']]['parent'] == pools.pools[f['right']]['parent']
                                                     for f in system.connections)))
        pressure = dict(pool_count=len(pools.pools), original_wet_cells=int(np.sum(volume > 0)),
            maximum_partition_volume_error=pools.maximum_volume_error,
            maximum_partition_momentum_error=pools.maximum_momentum_error,
            maximum_gram_partition_error=pools.maximum_gram_partition_error,
            maximum_volume_tangent_partition_error=pools.maximum_volume_tangent_partition_error,
            probe='Source-velocity-shaped normalized RHS, NOT an acceleration or evolved state',
            poles=pole_records,
            fixed_pressure_controls_passed=(max(pools.maximum_volume_error, pools.maximum_momentum_error,
                pools.maximum_gram_partition_error, pools.maximum_volume_tangent_partition_error) < 1e-10
                and all(p['solve_gate_passed'] and p['independent_solution_gate_passed']
                    and max(p['scaled_dense_action_error'], p['shared_column_partition_error'],
                            p['wall_column_partition_error']) < 1e-10
                    and p['direct_same_cell_pool_connections'] == 0 for p in pole_records)),
            nonlinear_or_wetting_or_time_or_gameplay_accepted=False)
        if args.pool_direction:
            direction = audit_direction(pools)
        if args.pool_transport:
            transport = audit_transport(pools)
        if args.pool_internal:
            internal = audit_internal_regions(pools)
        if args.pool_activation:
            activation = audit_activation(pools)
        if args.pool_history_steps:
            history = audit_history(pools, args.pool_history_steps, scheme=args.pool_history_scheme)
        if args.pool_primal_direction:
            primal_direction = audit_primal_direction(pools)
        if args.pool_auxiliary_components:
            auxiliary_components = audit_auxiliary_components(pools)
        if args.pool_refinement_steps:
            refinement = audit_refinement(pools, .02*args.pool_refinement_steps,
                args.pool_refinement_steps, args.pool_refinement_levels, scheme=args.pool_history_scheme)
    for path, expected in hashes.items():
        if sha(Path(path)) != expected:
            raise ValueError('Source changed during geometry audit')
    quantiles = lambda key: np.quantile([r[key] for r in records], [0, .5, .95, 1]).tolist()
    result = dict(schema='raftsim.south_fork.subcell_pressure_kinetic_geometry.v1',
        accepted=False, positive_cell_geometry_controls_passed=True, total_cells=256,
        pool_geometry='exact-source-relative' if args.exact_pool_geometry else 'legacy-float-vertices',
        geometry_reporting_note='Exact datums and source segments are retained in memory; JSON elevations/traces are float projections. Source hashes preserve the original geometry, not additional measurement precision.',
        fixed_pool_pressure=pressure,
        exact_source_representation=representation,
        fixed_pool_direction=direction,
        fixed_pool_transport=transport,
        fixed_internal_source_regions=internal,
        source_activation_candidates=activation,
        source_activation_history=history,
        source_time_refinement=refinement,
        fixed_pool_primal_direction=primal_direction,
        fixed_pool_auxiliary_components=auxiliary_components,
        positive_cells=len(records), unsupported_cells=unsupported,
        multi_pool_cell_count=sum(r['wet_connectivity']['component_count'] > 1 for r in records),
        total_wet_component_count=sum(r['wet_connectivity']['component_count'] for r in records),
        one_pressure_unknown_per_cell_supported=all(r['wet_connectivity']['one_pressure_unknown_per_cell_supported'] for r in records),
        wet_geometry_by_source_vertex_authority_codes=provenance,
        provenance_note='Codes are preserved per original triangle vertex, not averaged or promoted. '
            '1=captured DEM ground; 3=original exposed-rock return support. Other codes are inference/'
            'interpolation, including 2=uncalibrated submerged prior and 5=inferred connecting flank. '
            'A triangle with mixed vertex authority is not wholly measured bathymetry.',
        source_time_seconds=atlas['source_time_seconds'], source_origin_m=origins[0].tolist(),
        source_center_error_m=float(np.max(abs(source_bed-exact_bed))),
        maximum_relative_volume_error=max(r['relative_volume_error'] for r in records),
        maximum_relative_kinetic_tangent_error=max(r['relative_kinetic_tangent_error'] for r in records),
        slope_variance_energy_fraction_min_median_p95_max=quantiles('slope_variance_energy_fraction'),
        mean_depth_cubic_loss_fraction_min_median_p95_max=quantiles('mean_depth_cubic_loss_fraction'),
        records=records, source_sha256=hashes,
        scope='Original wet source-triangle geometry and original cell volumes. Positive local kinetic '
              'factor and fixed-terrain volume derivative, plus optional separated-pool static two-pole '
              'pressure on shared wet faces and reflecting walls, and optional analytic controlled '
              'volume/velocity directions checked against independent perturbed states; optional physical-momentum '
              'energy/reverse volume gradient and nondispersive pool flux support. Optional finite source-front '
              'activation and successive candidate controls include support transitions and finite energy rejection. '
              'Optional equal-horizon timestep comparisons retain original source-triangle water and physical momentum. '
              'The selected pool_geometry reports whether exact source storage/datums/traces/internal edges are used throughout. '
              'No full rational nonlinear transport/bed-force, wet-front/open/time-refinement, native or gameplay qualification.')
    with args.report.open('x') as stream:
        json.dump(result, stream, indent=2, allow_nan=False, default=report_scalar)
    console = {k: v for k, v in result.items() if k not in ('records', 'source_sha256', 'fixed_pool_transport', 'fixed_internal_source_regions', 'source_activation_candidates', 'source_activation_history', 'source_time_refinement')}
    if history is not None:
        console['source_activation_history'] = {k: v for k, v in history.items() if k != 'attempts'}
    if refinement is not None:
        console['source_time_refinement'] = dict(refinement,
            runs=[{k: v for k, v in run.items() if k != 'attempts'} for run in refinement['runs']])
    if representation is not None:
        console['exact_source_representation'] = {k: v for k, v in representation.items() if k != 'records'}
    if activation is not None:
        console['source_activation_candidates'] = {k: v for k, v in activation.items() if k not in ('front_records', 'receiving_rate_records')}
    if internal is not None:
        console['fixed_internal_source_regions'] = {k: v for k, v in internal.items() if k != 'physical_energy_and_transport'}
    if transport is not None:
        pending = transport['central_base']['unresolved_activation_faces']
        console['fixed_pool_transport'] = dict(
            physical_energy_controls_passed=transport['physical_energy_controls_passed'],
            complete_fixed_topology_base_rates=transport['central_base']['complete_fixed_topology_base_rates'],
            unresolved_face_entries=len(pending),
            unresolved_parent_cells=sorted(set(face['dry_parent'] for face in pending)),
            nonlinear_or_wetting_or_time_or_gameplay_accepted=False)
    print(json.dumps(console, indent=2, default=report_scalar))
    return int((pressure is not None and not pressure['fixed_pressure_controls_passed'])
               or (representation is not None and not representation['exact_representation_controls_passed'])
               or (history is not None and not history['all_requested_steps_passed'])
               or (refinement is not None and not refinement['all_runs_completed'])
               or (primal_direction is not None and not primal_direction['fixed_topology_metric_direction_controls_passed'])
               or (auxiliary_components is not None and not auxiliary_components['source_auxiliary_component_controls_passed'])
               or (activation is not None and not activation['twenty_ms_candidate_passed'])
               or (internal is not None and not internal['internal_region_controls_passed'])
               or (direction is not None and not direction['fixed_topology_direction_controls_passed'])
               or (transport is not None and (not transport['physical_energy_controls_passed']
                   or not transport['central_base']['complete_fixed_topology_base_rates']
                   or not transport['dissipative_base']['complete_fixed_topology_base_rates']
                   or not transport['central_base']['base_balance_controls_passed']
                   or not transport['dissipative_base']['base_balance_controls_passed'])))


def report_scalar(value):
    if isinstance(value, Fraction):
        return float(value)
    raise TypeError(f'Unsupported audit value: {type(value).__name__}')


if __name__ == '__main__':
    raise SystemExit(main())
