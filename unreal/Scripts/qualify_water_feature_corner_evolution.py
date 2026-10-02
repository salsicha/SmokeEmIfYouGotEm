"""Independently qualify matched corner experiments; reject, do not promote.

Checks every paired native output and all retained contact stencils. Volumes are
trilinear-field quadrature, not conserved mass or full-scene hydraulic evidence.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
from water_feature_field_surface import sample_centers
from water_feature_cell_volume import reconstructed_volume


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--standard-contact', type=Path, required=True)
    parser.add_argument('--fractional-contact', type=Path, required=True)
    parser.add_argument('--standard-evolution', type=Path, required=True)
    parser.add_argument('--fractional-evolution', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    hashes = {str(p.resolve()): digest(p) for p in (Path(__file__),
        Path(__file__).with_name('water_feature_field_surface.py'),
        Path(__file__).with_name('water_feature_cell_volume.py'))}
    controls = []; first_closest = None
    for label in ('standard', 'fractional'):
        contact_path = getattr(args, label+'_contact'); evolution_path = getattr(args, label+'_evolution')
        contact = json.loads(contact_path.read_text()); evolution = json.loads(evolution_path.read_text())
        if not all(d['complete'] and not d['accepted'] and d['originals_unchanged'] for d in (contact, evolution)):
            raise ValueError('Completed unaccepted source experiments required')
        for p in (contact_path, evolution_path):
            hashes[str(p.resolve())] = digest(p)
        for report in (contact, evolution):
            for p, sha in {**report['dependency_sha256'], **report.get('outputs_sha256', {})}.items():
                if digest(p) != sha:
                    raise ValueError('Pinned source/output changed: '+p)
                if p in hashes and hashes[p] != sha:
                    raise ValueError('Conflicting pins')
                hashes[p] = sha
        if not all(x['unchanged'] for x in evolution['live_fields']):
            raise ValueError('Engine field preservation failed')
        shape = tuple(evolution['shape']); origin = np.array(evolution['origin_m']); h = evolution['cell_m']
        if shape != (90, 31, 42) or abs(h-.075) > 1e-9:
            raise ValueError('Explicit-wall geometry required')
        closest = np.load(evolution_path.parent/'closest-mesh-obstacle.npy', allow_pickle=False)
        if first_closest is None:
            first_closest = closest.copy()
        else:
            np.testing.assert_array_equal(first_closest, closest)
        paired = []; stencils = []
        for frame in (145, 169, 191):
            rows = [r for r in evolution['rows'] if r['frame'] == frame]
            if len(rows) != 2 or [r['label'] for r in rows] != ['cached', 'closest-mesh']:
                raise ValueError('All matched baseline/changed controls required')
            for row in rows:
                if not row['matched_native_geometry_preparation'] or not row['exact_binding']['exact_code_object']:
                    raise ValueError('Matched native preparation/exact step missing')
                if not row['resume_verification']['primary_positions_velocities_match_native']:
                    raise ValueError('Native primary load mismatch')
            if rows[0]['native_timestep'] != rows[1]['native_timestep']:
                raise ValueError('Paired physical clock changed')
            if rows[0]['before'] != rows[1]['before']:
                raise ValueError('Paired starting state changed')
            if rows[0]['exact_binding']['code_sha256'] != rows[1]['exact_binding']['code_sha256']:
                raise ValueError('Native step implementation differs')
            after = []
            for row in rows:
                arrays = {k: np.load(p, allow_pickle=False) for k, p in row['arrays'].items()}
                if any(not np.isfinite(a).all() for a in arrays.values()):
                    raise ValueError('Nonfinite actual output')
                if any(arrays[k].shape != shape for k in ('phi', 'obstacle', 'pressure')) or arrays['velocity'].shape != (*shape, 3):
                    raise ValueError('Native output dimensions differ')
                if row['label'] == 'closest-mesh':
                    np.testing.assert_array_equal(arrays['obstacle'], closest)
                q8 = reconstructed_volume(arrays['phi'], arrays['obstacle'], (h, h, h), 8)
                expected = row['after_native_step']['liquid_field_volume']['volume_m3']
                if abs(q8['volume_m3']-expected) > 1e-12*max(1., abs(expected)):
                    raise ValueError('Independent post-step field-volume mismatch')
                q16 = reconstructed_volume(arrays['phi'], arrays['obstacle'], (h, h, h), 16)
                derived = {n: max(v['vertices']['deepest_inside_m'], v['triangle_centers']['deepest_inside_m'])
                           for n, v in row['derived_contact'].items()}
                after.append(dict(label=row['label'], field_volume_q8_m3=q8['volume_m3'],
                    field_volume_q16_m3=q16['volume_m3'], geometry_only_volume_q8_m3=row['after_geometry_before_step']['liquid_field_volume']['volume_m3'],
                    primary_after=row['after_native_step']['primary_authored_contact'],
                    derived_maximum_intrusion_m=derived,
                    full_sampled_contact_gate=all(v == 0 for v in derived.values()) and
                        all(v['deepest_inside_m'] == 0 for v in row['after_native_step']['primary_authored_contact'].values()),
                    native_geometry_changed_flag_cells=row['changed_flag_cells'],
                    native_uncached_fraction_scalars_reconstructed=row['changed_fraction_scalars']))
            original = np.load(rows[0]['arrays']['obstacle'], allow_pickle=False)
            cohort = next(f for f in contact['frames'] if f['frame'] == frame)
            for name, solids in cohort['cohorts'].items():
                for solid, data in solids.items():
                    for point in data['deepest_points']:
                        for sample in point['interpolation_stencil']:
                            i = tuple(sample['index'])
                            if abs(float(original[i]*h)-sample['final_obstacle_m']) > 1e-7:
                                raise ValueError('Cached native field/stencil mismatch')
                            if abs(float(closest[i]*h)-sample['exact_union_m']) > 4e-6:
                                raise ValueError('Closest actual node/closed-BVH stencil mismatch')
                        gp = (np.array(point['world_m'])-origin)/h
                        stencils.append(dict(frame=frame, cohort=name, solid=solid,
                            world_m=point['world_m'], authored_depth_inside_m=point['depth_inside_m'],
                            cached_interpolated_phi_m=float(sample_centers(original, gp[None, :])[0]*h),
                            closest_nodes_interpolated_phi_m=float(sample_centers(closest, gp[None, :])[0]*h),
                            maximum_cached_node_distance_error_m=max(abs(s['final_obstacle_m']-s['exact_union_m']) for s in point['interpolation_stencil'])))
            velocity = [np.load(r['arrays']['velocity'], allow_pickle=False) for r in rows]
            pressure = [np.load(r['arrays']['pressure'], allow_pickle=False) for r in rows]
            paired.append(dict(frame=frame, physical_substep_seconds=rows[0]['physical_substep_seconds'],
                matched_preparation_and_initial_state=True, unchanged_exact_native_step=True, controls=after,
                maximum_velocity_scalar_delta_native=float(np.max(np.abs(velocity[0]-velocity[1]))),
                maximum_pressure_scalar_delta_native=float(np.max(np.abs(pressure[0]-pressure[1])))))
            print('MATCHED_CORNER_QUALIFIED', label, frame, flush=True)
        controls.append(dict(label=label, shape=list(shape), cell_m=h, frames=paired, retained_contact_stencils=stencils,
            closest_node_geometry_error_allowance_m=4e-6,
            every_contact_gate_failed=all(not c['full_sampled_contact_gate'] for f in paired for c in f['controls'])))
    if not all(c['every_contact_gate_failed'] for c in controls):
        raise ValueError('Unexpected contact result requires review before describing rejection')
    if any(digest(p) != sha for p, sha in hashes.items()):
        raise ValueError('Source changed during qualification')
    report = dict(complete=True, accepted=False, originals_unchanged=True, dependency_sha256=hashes,
        closest_node_fields_bitexact_between_modes=True, controls=controls,
        scope=__doc__, conclusion='Reject closest-node distance replacement as complete coupled repair: all12 sampled contact gates fail. Improve subcell geometry/pressure/contact representation; no promotion or cosmetic clipping.',
        caveats='Only three independent late states per solver mode and one20.833ms native liquid step each control, not full host source/emission/solid reconstruction chronology or a fresh bake. Q8/Q16 are interface quadrature, not conserved mass or uncertainty bounds. Pressure/velocity deltas are native units and full-domain maxima, not isolated fluid error or physical pressure acceptance. Existing BVH/node float precision does not imply continuum geometric accuracy.')
    with args.output.open('x') as stream:
        json.dump(report, stream, indent=2)
    print('MATCHED_CORNER_ALL_QUALIFIED', len(hashes), flush=True)


if __name__ == '__main__':
    main()
