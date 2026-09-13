"""Test a volume-kernel interface against actual South Fork native particles.

The initial state uses every captured original birth position and fixed volume.
The evolved state uses the same-step native P2G totals, particles and boundary.
This assesses a candidate, not a change to native phase/pressure or scene assets.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from audit_liquid_native_handoff import read
from audit_liquid_native_compact import verify_summary
from liquid_stage_journal import stage_groups
from diagnose_liquid_projection_packet import load_field
from liquid_dataset import resolve as resolve_dataset
from liquid_volume_interface import deposit_volume, implicit_from_volume, measure_interface, sample_centred
from south_fork_registered_mesh import RegisteredMeshSampler


def bed_clearance(points_world_cm, outside, sampler):
    bed = sampler.sample(points_world_cm[:, 0]/100, -points_world_cm[:, 1]/100)
    clearance = points_world_cm[:, 2]/100-bed
    edges = [-float('inf'), 0, .05, .1, .25, .5, float('inf')]
    return [dict(lower_exclusive_m=lo if np.isfinite(lo) else None,
                 upper_inclusive_m=hi if np.isfinite(hi) else None,
                 all_particles=int(((clearance>lo) & (clearance<=hi)).sum()),
                 outside_candidate=int((outside & (clearance>lo) & (clearance<=hi)).sum()))
            for lo, hi in zip(edges[:-1], edges[1:])]


def diagnose(directory):
    directory = Path(directory).resolve()
    stages_path = directory/'stages.json'
    report = json.loads(stages_path.read_text())
    capture = json.loads((directory/'capture.json').read_text())
    if (not capture['complete'] or report['exchange_error'] or report['zero_water'] or
            not report['native_transfer_packet_saved'] or not report['scheduler_alignment_observed'] or
            not report.get('native_projection_packet_requested')):
        raise ValueError('Complete aligned native capture with paired pressure fields required')
    dataset = resolve_dataset(report)
    parent = json.loads((dataset['parent']/'manifest.json').read_text())
    mesh_hash = hashlib.sha256(dataset['mesh'].read_bytes()).hexdigest()
    if mesh_hash != parent['source_geometry_sha256']:
        raise ValueError('Registered terrain mesh changed')
    with np.load(dataset['mesh']) as mesh:
        sampler = RegisteredMeshSampler(mesh)
    records = sorted(report['native_transfer_packet'], key=lambda r:r['region_id'])
    if [r['region_id'] for r in records] != list(range(12)):
        raise ValueError('All twelve native owners required')
    step = report['native_transfer_packet_step']
    history = report['native_particle_handoff_history']
    if (len(history) != report['native_particle_handoff_count'] or not history or
            history[-1]['native_step']+1 != step):
        raise ValueError('Continuous successful compact history through the captured state required')
    planned = {s:{e['owner']:e['native_rate_spawns']+e['native_event_spawns'] for e in g['entries']}
               for s, g in enumerate([g for g in stage_groups(report) if g['entries'][0]['first']][:step], 1)}
    if len(planned) != step or any(set(p) != set(range(12)) for p in planned.values()):
        raise ValueError('Complete all-owner native source plan required')
    live, _ = verify_summary(history, planned, sum(r['birth_particle_count'] for r in records))
    if live+sum(planned[step].values()) != sum(r['particle_count'] for r in records):
        raise ValueError('Capture particle count disagrees with successful native history')
    initial = []
    results = []
    source_hashes = {}
    axes = np.asarray([records[0]['world_axis_x'], records[0]['world_axis_y'], [0, 0, 1]])
    if not np.allclose(axes@axes.T, np.eye(3), atol=1e-9, rtol=0):
        raise ValueError('Common orthonormal native world frame required')
    lower_corners = []
    upper_corners = []
    spacing = np.asarray(records[0]['extent_cm'])/np.asarray(records[0]['cells'])/100
    volume = float(np.float32(records[0]['particle_volume_m3']))
    for r in records:
        if (r.get('projection_native_step') != step or
                r.get('projection_input_stage') != 'Compute Divergence: after stage' or
                not np.array_equal(np.asarray([r['world_axis_x'], r['world_axis_y'], [0, 0, 1]]), axes) or
                not np.allclose(np.asarray(r['extent_cm'])/r['cells']/100, spacing, atol=1e-12, rtol=0) or
                float(np.float32(r['particle_volume_m3'])) != volume):
            raise ValueError('Paired stages and common parent metric/volume required')
        origin = np.asarray(r['world_origin_cm']) @ axes.T/100
        extent = np.asarray(r['extent_cm'])/100
        lower = origin-extent*[.5, .5, 0]
        lower_corners.append(lower)
        upper_corners.append(lower+extent)
        birth = read(directory, r, 'birth_positions', (r['birth_particle_count'], 4)).view('<f4')[:, :3].astype(float)
        prepared = json.loads((dataset['regions']/f"region-{r['region_id']:03d}.json").read_text())
        birth_ids = read(directory, r, 'birth_identities', (len(birth), 4))
        if (planned[1][r['region_id']] != len(birth) or
                r['particle_count'] != history[-1]['counts'][r['region_id']]+planned[step][r['region_id']] or
                np.any(birth_ids[:, 0] != r['region_id']) or
                not np.array_equal(np.sort(birth_ids[:, 1]), np.arange(len(birth))) or
                not np.array_equal(birth[np.argsort(birth_ids[:, 1])],
                                   np.asarray(prepared['positions_canonical_cm'], dtype='<f4').reshape(-1, 3)*[1, -1, 1])):
            raise ValueError('Original prepared South Fork birth positions/identities differ')
        initial.append(birth @ axes.T/100)
        positions = read(directory, r, 'positions', (r['particle_count'], 4)).view('<f4')[:, :3].astype(float)
        if not np.isfinite(positions).all() or not np.isfinite(birth).all():
            raise ValueError('Nonfinite native particle positions')
        total_path = (directory/r['total']).resolve()
        if total_path.parent != directory:
            raise ValueError('P2G volume file leaves capture directory')
        total = np.fromfile(total_path, dtype='<f4')
        if total.size != int(np.prod(r['cells']))*4:
            raise ValueError('Truncated native P2G total')
        mass = total.reshape((*r['cells'][::-1], 4))[..., 3].astype(float)
        physical = np.zeros(mass.shape, bool)
        physical[:, 2:-2, 2:-2] = True
        metrics = measure_interface(mass, spacing, positions@axes.T/100-lower, physical)
        b = load_field(directory, r, 'projection_boundary', 4)
        phi = implicit_from_volume(mass, spacing)
        fluid = (np.rint(b[..., 3]) == 0) & physical
        sampled_phi, valid = sample_centred(phi, positions@axes.T/100-lower, spacing)
        metrics.update(region_id=r['region_id'], native_pressure_fluid_cells=int(fluid.sum()),
                       native_fluid_cells_candidate_calls_air=int((fluid & (phi>0)).sum()),
                       particle_volume_deposited_into_native_solid_m3=float(mass[physical & (np.rint(b[..., 3])==1)].sum()),
                       bed_clearance_bins=bed_clearance(positions, valid & (sampled_phi>0), sampler))
        results.append(metrics)
        for key in ('birth_positions', 'birth_identities', 'positions', 'total', 'projection_boundary'):
            path = (directory/r[key]).resolve()
            if path.parent != directory:
                raise ValueError('Source file leaves capture')
            source_hashes[r[key]] = hashlib.sha256(path.read_bytes()).hexdigest()
    # Initial reference is assembled in one parent frame, not twelve isolated
    # surfaces. This prevents internal ownership cuts becoming surface edges.
    lower = np.min(lower_corners, axis=0)
    upper = np.max(upper_corners, axis=0)
    counts = (upper-lower)/spacing
    if not np.allclose(counts, np.rint(counts), atol=1e-8, rtol=0):
        raise ValueError('Regional grids do not form an integer parent lattice')
    counts = np.rint(counts).astype(int)
    initial = np.concatenate(initial)-lower
    mass = deposit_volume(initial, counts, spacing, volume)
    physical = np.zeros(mass.shape, bool)
    physical[:, 2:-2, 2:-2] = True
    initial_metrics = measure_interface(mass, spacing, initial, physical)
    initial_phi, valid = sample_centred(implicit_from_volume(mass, spacing), initial, spacing)
    initial_metrics.update(nominal_particle_volume_m3=len(initial)*volume,
                           all_grid_deposited_volume_m3=float(mass.sum()),
                           off_grid_kernel_volume_m3=float(len(initial)*volume-mass.sum()),
                           bed_clearance_bins=bed_clearance((initial+lower)@axes*100, valid & (initial_phi>0), sampler))
    summed = ('particle_count', 'sampled_particles', 'particles_without_complete_stencil',
              'particles_outside_candidate_interface', 'deposited_volume_m3', 'candidate_wet_cell_count',
              'candidate_centre_classified_volume_m3', 'supported_cell_count',
              'supported_columns_without_candidate_water', 'native_pressure_fluid_cells',
              'particle_occupied_columns', 'particle_occupied_columns_without_candidate_water',
              'native_fluid_cells_candidate_calls_air', 'particle_volume_deposited_into_native_solid_m3')
    evolved = {key:sum(r[key] for r in results) for key in summed}
    evolved['sampled_particles_outside_fraction'] = evolved['particles_outside_candidate_interface']/evolved['sampled_particles']
    evolved['maximum_density'] = max(r['maximum_density'] for r in results)
    evolved['bed_clearance_bins'] = [{**results[0]['bed_clearance_bins'][i],
                                    **{k:sum(r['bed_clearance_bins'][i][k] for r in results)
                                       for k in ('all_particles', 'outside_candidate')}} for i in range(6)]
    return dict(source_directory=str(directory), stages_sha256=hashlib.sha256(stages_path.read_bytes()).hexdigest(),
                source_files_sha256=source_hashes, source_geometry_sha256=mesh_hash,
                native_dataset=report['native_dataset'], native_p2g_step=step,
                parent_cells_xyz=counts.tolist(), cell_size_m=spacing.tolist(), initial=initial_metrics,
                evolved=evolved, regions=results,
                verified_compact_commits=len(history),
                initial_reference='CPU centred tent deposit of every verified prepared original birth position',
                evolved_reference='Actual same-step native shared P2G total and live positions',
                candidate='Fixed nominal particle-volume tent density, isovalue 0.5',
                original_particles_modified=False, native_phase_or_pressure_modified=False,
                classification_volume_is_not_surface_volume=True,
                physical_visual_or_performance_acceptance=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    result = diagnose(args.directory)
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')
    print(json.dumps({k:result[k] for k in ('native_p2g_step', 'parent_cells_xyz', 'initial', 'evolved')}, indent=2))
