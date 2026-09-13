"""Independent centered-tent P2G check against an actual native GPU snapshot.

This validates a selected-step transfer, not sustained regional fluid flow,
particle handoff, bathymetry, rendered appearance, or performance.
"""
import argparse
import json
import itertools
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[2]


def reference(record, positions, velocities):
    if len(positions) > 128:
        return reference_batched(record, positions, velocities)
    cells = np.asarray(record['cells'], dtype=int)
    origin = np.asarray(record['world_origin_cm'], dtype=float)
    axes = np.asarray([record['world_axis_x'], record['world_axis_y'], [0, 0, 1]], dtype=float)
    extent = np.asarray(record['extent_cm'], dtype=float)
    if not np.allclose(axes @ axes.T, np.eye(3), atol=1e-9, rtol=0):
        raise ValueError('Orthonormal common world frame required')
    spacing = extent / cells
    volume = float(np.float32(record['particle_volume_m3']))
    result = np.zeros((*cells[::-1], 4), dtype=float)
    error = np.zeros_like(result)
    # Predeclared forward error envelope for float32 affine cell construction
    # and projection: 16 operations at unit roundoff u. The tent product is
    # 1-Lipschitz per axis. This is numeric tolerance, not a tuned flow gate.
    u = 2.0**-24
    gamma = 16*u/(1-16*u)
    q_error = gamma*(np.max(np.abs(origin))+np.sum(extent))/np.min(spacing)
    for point, velocity in zip(positions, velocities):
        q = ((point-origin) @ axes.T)/spacing + [cells[0]/2-0.5, cells[1]/2-0.5, -0.5]
        local_velocity = velocity @ axes.T
        low = np.floor(q).astype(int)
        # Include zero-weight neighbors within the rounding envelope too.
        for z in range(low[2]-1, low[2]+3):
            for y in range(low[1]-1, low[1]+3):
                for x in range(low[0]-1, low[0]+3):
                    index = np.array([x, y, z])
                    if np.any(index < 0) or np.any(index >= cells):
                        continue
                    w = np.maximum(1-np.abs(q-index), 0)
                    weight = np.prod(w)
                    mass = volume*weight
                    result[z, y, x] += np.r_[local_velocity*mass, mass]
                    if np.all(np.abs(q-index) <= 1+q_error):
                        mass_error = volume*(3*q_error+gamma)
                        error[z, y, x] += np.r_[
                            mass_error*np.abs(local_velocity)+gamma*volume*np.max(np.abs(velocity)), mass_error]
    return result, error


def reference_batched(record, positions, velocities, chunk_size=8192):
    """Same float64 tent/reference envelope, bounded vectorized CPU accumulation."""
    cells = np.asarray(record['cells'], dtype=int)
    origin = np.asarray(record['world_origin_cm'], dtype=float)
    axes = np.asarray([record['world_axis_x'],record['world_axis_y'],[0,0,1]], dtype=float)
    extent = np.asarray(record['extent_cm'], dtype=float)
    if not np.allclose(axes@axes.T,np.eye(3),atol=1e-9,rtol=0):
        raise ValueError('Orthonormal common world frame required')
    positions, velocities = np.asarray(positions,dtype=float), np.asarray(velocities,dtype=float)
    if positions.shape != velocities.shape or positions.ndim != 2 or positions.shape[1] != 3 or chunk_size < 1:
        raise ValueError('Matched position/velocity arrays and positive batch size required')
    if not np.isfinite(positions).all() or not np.isfinite(velocities).all():
        raise ValueError('Finite native particles required')
    spacing = extent/cells;volume = float(np.float32(record['particle_volume_m3']))
    result = np.zeros((int(np.prod(cells)),4));error = np.zeros_like(result)
    u=2.0**-24;gamma=16*u/(1-16*u)
    q_error=gamma*(np.max(np.abs(origin))+np.sum(extent))/np.min(spacing)
    mass_error=volume*(3*q_error+gamma)
    for first in range(0,len(positions),chunk_size):
        p=positions[first:first+chunk_size];v=velocities[first:first+chunk_size]
        q=((p-origin)@axes.T)/spacing+[cells[0]/2-0.5,cells[1]/2-0.5,-0.5]
        local_v=v@axes.T;low=np.floor(q).astype(np.int64)
        tolerance=np.column_stack((mass_error*np.abs(local_v)+gamma*volume*np.max(np.abs(v),axis=1)[:,None],
                                   np.full(len(v),mass_error)))
        for offset in itertools.product(range(-1,3),repeat=3):
            index=low+offset;distance=np.abs(q-index)
            inside=np.all((index>=0)&(index<cells),axis=1)
            supported=inside & np.all(distance<1,axis=1)
            if np.any(supported):
                address=index[supported];flat=(address[:,2]*cells[1]+address[:,1])*cells[0]+address[:,0]
                mass=volume*np.prod(np.maximum(1-distance[supported],0),axis=1)
                np.add.at(result,flat,np.column_stack((local_v[supported]*mass[:,None],mass)))
            bounded=inside & np.all(distance<=1+q_error,axis=1)
            if np.any(bounded):
                address=index[bounded];flat=(address[:,2]*cells[1]+address[:,1])*cells[0]+address[:,0]
                np.add.at(error,flat,tolerance[bounded])
    return result.reshape((*cells[::-1],4)),error.reshape((*cells[::-1],4))


def reduce_reference(raw, columns):
    total = {owner: values.copy() for owner, values in raw.items()}
    contributors = {}
    used = set()
    for owner, dest, sx, sy, dx, dy in columns:
        if (dest, dx, dy) in used or owner == dest:
            raise ValueError('Duplicate or self halo mapping')
        used.add((dest, dx, dy))
        contributors.setdefault((owner, sx, sy), []).append((dest, dx, dy))
    for (owner, sx, sy), others in contributors.items():
        if len({d for d, _, _ in others}) != len(others):
            raise ValueError('Duplicate contributor to physical cell')
        value = raw[owner][:, sy, sx].copy()
        for dest, dx, dy in sorted(others):
            value += raw[dest][:, dy, dx]
        total[owner][:, sy, sx] = value
        for dest, dx, dy in others:
            total[dest][:, dy, dx] = value
    return total


def audit(directory, log_path=None):
    directory = Path(directory)
    capture = json.loads((directory/'capture.json').read_text())
    report = json.loads((directory/'stages.json').read_text())
    if (not capture['complete'] or report['zero_water'] or report['exchange_error'] or
            not report['native_transfer_packet_saved'] or not report['scheduler_alignment_observed']):
        raise ValueError('Successful actual native nonempty transfer snapshot required')
    records = report['native_transfer_packet']
    handoff = None
    if report.get('native_particle_handoff_requested'):
        if report.get('native_dense_requested'):
            from audit_liquid_native_dense import audit as audit_handoff
            handoff = audit_handoff(directory, log_path=log_path)
        elif report.get('native_compact_handoff_requested'):
            from audit_liquid_native_compact import audit as audit_handoff
            handoff = audit_handoff(directory, log_path=log_path)
        elif report.get('native_particle_retirement_requested'):
            from audit_liquid_native_retirement import audit as audit_handoff
            handoff = audit_handoff(directory, log_path=log_path)
        else:
            from audit_liquid_native_handoff import audit as audit_handoff
            handoff = audit_handoff(directory)
    if sorted(r['region_id'] for r in records) != list(range(12)):
        raise ValueError('All twelve owners required')
    from liquid_dataset import resolve as resolve_dataset
    geometry = resolve_dataset(report)['geometry']
    pages = {i: json.loads((geometry/f'region-{i:03d}-boundary.json').read_text()) for i in range(12)}
    columns = []
    for dest, page in pages.items():
        for dx, dy, source, sx, sy in page['shared_halo_columns']:
            columns.append((source, dest, sx, pages[source]['computational_cells'][1]-1-sy,
                            dx, page['computational_cells'][1]-1-dy))
    if sorted(columns) != sorted(map(tuple, report['halo_columns_niagara'])):
        raise ValueError('Native map differs from independent prepared ownership')
    raw, total, ideal, errors = {}, {}, {}, {}
    particles = []; summaries = []
    def load(record, key, shape):
        path = (directory/record[key]).resolve()
        if path.parent != directory.resolve():
            raise ValueError('Snapshot path leaves capture directory')
        values = np.fromfile(path, dtype='<f4')
        if values.size != np.prod(shape) or not np.isfinite(values).all():
            raise ValueError('Complete finite full-precision snapshot required')
        return values.reshape(shape)
    for record in records:
        owner = record['region_id']; n = record['particle_count']
        expected_count = handoff['following_step_counts'][owner] if handoff else record['expected_count']
        if n != expected_count or n < 0:
            raise ValueError('Native seed count differs from selected packet')
        p = load(record, 'positions', (n, 4))[:, :3]
        v = load(record, 'velocities', (n, 4))[:, :3]
        shape = (*record['cells'][::-1], 4)
        raw[owner] = load(record, 'raw', shape); total[owner] = load(record, 'total', shape)
        ideal[owner], errors[owner] = reference(record, p.astype(float), v.astype(float))
        bad = np.abs(raw[owner].astype(float)-ideal[owner]) > errors[owner]
        summaries.append(dict(region_id=owner, particle_count=n,
                              raw_mismatched_components=int(bad.sum()),
                              max_raw_component_error=float(np.max(np.abs(raw[owner]-ideal[owner]))),
                              deposited_volume=float(raw[owner][..., 3].sum(dtype=float)),
                              expected_particle_volume=n*float(np.float32(record['particle_volume_m3']))))
        for point, velocity in zip(p, v):
            particles.append(dict(owner=owner, position_cm=point.tolist(), velocity_cm_s=velocity.tolist()))
    per_owner = report.get('native_transfer_packet_per_owner', 1)
    empty_receiver = report.get('native_empty_receiver_requested', False)
    if empty_receiver and (not handoff or not handoff.get('initially_empty_receiver_verified')):
        raise ValueError('Empty receiving requires actual verified native empty-to-nonempty handoff')
    additional_births = handoff.get('verified_new_births', 0) if handoff else 0
    expected_live = (3 if empty_receiver else 4)*per_owner+additional_births
    if report.get('native_particle_retirement_requested'):
        # The dedicated audit proves every original wet seed is in exactly one
        # native survivor or approved exit ledger, including the fourth outlet owner.
        if not handoff or not (handoff.get('native_outlet_retirement_verified') or handoff.get('compact_native_telemetry_verified') or handoff.get('dense_native_state_verified')):
            raise ValueError('Actual survivor/exit partition required before P2G audit')
        expected_live = handoff['initial_particles']+handoff['verified_new_births']-handoff['retired_particles']
    if (per_owner not in (1, 2, 3, 4) or len(particles) != expected_live or
            (not handoff and (sum(r['particle_count'] > 0 for r in summaries) != 4 or
             any(r['particle_count'] not in (0, per_owner) for r in summaries)))):
        raise ValueError('Bounded packet in four distinct live particle owners required')
    # Exact float32 reduction of actual raw inputs: no numerical tolerance is
    # needed here. The independent map defines the deterministic owner order.
    expected = reduce_reference(raw, columns)
    reduction_mismatch = sum(int(np.count_nonzero(total[i] != expected[i])) for i in raw)
    physical_volume = sum(float(t[:, 2:-2, 2:-2, 3].sum(dtype=float)) for t in total.values())
    expected_volume = sum(r['expected_particle_volume'] for r in summaries)
    # Sum the previously declared cell error envelopes over PHYSICAL owners;
    # do not count halo copies as extra water.
    reduced_error = reduce_reference(errors, columns)
    volume_bound = sum(float(e[:, 2:-2, 2:-2, 3].sum()) for e in reduced_error.values())
    shared_nonzero = sum(int(np.count_nonzero(total[o][:, sy, sx, 3])) for o, _, sx, sy, _, _ in columns)
    passed = (not any(r['raw_mismatched_components'] for r in summaries) and reduction_mismatch == 0 and
              abs(physical_volume-expected_volume) <= volume_bound and shared_nonzero > 0)
    return dict(native_packet_p2g_verified=passed, native_p2g_step=report.get('native_transfer_packet_step', 1),
                storage_owner_reference=handoff.get('storage_owner_reference') if handoff else None,
                survey_internal_storage_owner_disagreements=handoff.get('survey_internal_storage_owner_disagreements') if handoff else None,
                survey_physical_outer_bounds_preserved=handoff.get('survey_physical_outer_bounds_preserved') if handoff else None,
                particle_count=len(particles), particles=particles,
                raw_regions=summaries, reduction_mismatched_components=reduction_mismatch,
                nonzero_shared_column_cells=shared_nonzero, physical_volume_m3=physical_volume,
                expected_volume_m3=expected_volume, volume_numeric_bound_m3=volume_bound,
                sustained_flow_or_handoff_verified=False, visual_or_performance_acceptance=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path); parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--summary-only', action='store_true',
                        help='Verify every particle but omit redundant per-particle JSON details from the report')
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    result = audit(args.directory)
    if args.summary_only:
        result.pop('particles')
        result['particle_details_omitted_from_report'] = True
    args.output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({k: v for k, v in result.items() if k not in ('raw_regions', 'particles')}, indent=2))
    raise SystemExit(0 if result['native_packet_p2g_verified'] else 1)
