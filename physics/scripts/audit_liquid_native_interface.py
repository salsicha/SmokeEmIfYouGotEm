"""Verify a retained native interface's paired transport and shared halo copies.

This verifies transport, not interface coverage, volume conservation, pressure
accuracy, visual acceptance or FPS. Pressure coupling is explicit metadata;
its captured fields are checked by diagnose_liquid_projection_packet. The
current prototype retains fixed exterior/Z data.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from diagnose_liquid_projection_packet import load_field
from liquid_interface_transport import advect
from liquid_dataset import resolve
from liquid_stage_journal import stage_groups


def exchange_scalars(fields, columns):
    result = [f.copy() for f in fields]
    written = set()
    for source, dest, sx, sy, dx, dy in columns:
        if (source == dest or not 0 <= source < len(fields) or not 0 <= dest < len(fields) or
                (dest, dx, dy) in written):
            raise ValueError('Unique cross-owner interface halo destinations required')
        s, d = fields[source].shape, fields[dest].shape
        if (s[0] != d[0] or not (2 <= sx < s[2]-2 and 2 <= sy < s[1]-2) or
                not (0 <= dx < d[2] and 0 <= dy < d[1]) or (2 <= dx < d[2]-2 and 2 <= dy < d[1]-2)):
            raise ValueError('Interface exchange must copy physical owner into a halo')
        written.add((dest, dx, dy))
        result[dest][:, dy, dx] = fields[source][:, sy, sx]
    return result


def validate_ledger(words, sizes, steps, high_order=False):
    w = np.asarray(words)
    width = 8 if high_order else 3
    if (w.shape != (steps*len(sizes)*width,) or not np.issubdtype(w.dtype, np.integer) or (w<0).any()):
        raise ValueError('Complete native interface per-step diagnostic ledger required')
    w = w.reshape(steps, len(sizes), width)
    expected = np.prod(np.asarray(sizes)-4, axis=1)
    failures = w[..., [1, 2, 7]] if high_order else w[..., 1:]
    if np.any(failures != 0) or not np.array_equal(w[..., 0], np.broadcast_to(expected, w[..., 0].shape)):
        raise ValueError('Native interface step rejected a trace, contains invalid scalar/solid data, or skipped owned cells')
    if high_order and (np.any(w[..., 3]+w[..., 5] != w[..., 0]) or np.any(w[..., 4] > w[..., 3]) or np.any(w[..., 6] > w[..., 5])):
        raise ValueError('High-order use, limiter or reverse fallback accounting is inconsistent')
    return int(w[..., 0].sum())


def validate_transport_schedule(groups, steps, transport_stage='Project Pressure'):
    if transport_stage not in ('Project Pressure','Extrapolate Velocities Again'):
        raise ValueError('Unknown native transport stage')
    native_step, resets, projected, transported = 0, [], [], []
    for group in groups:
        entries = group['entries']
        if (not group['complete'] or not group['aligned'] or
                sorted(e['owner'] for e in entries) != list(range(12))):
            raise ValueError('Complete aligned twelve-owner transport schedule required')
        entry = entries[0]
        for e in entries:
            if any(e[k] != entry[k] for k in ('name', 'first', 'reset')):
                raise ValueError('Transport owner stages disagree')
        if entry['first']:
            native_step += 1
            if entry['reset']:
                resets.append(native_step)
        if entry['name'] == 'Project Pressure':
            projected.append(native_step)
        if entry['name'] == transport_stage:
            if transport_stage!='Project Pressure' and (not projected or projected[-1]!=native_step):
                raise ValueError('Interface cannot move before this step projects velocity')
            transported.append(native_step)
    # The game thread may enqueue later ticks before observing packet readiness.
    # Validate the whole journal, but compare the selected immutable packet.
    if native_step < steps or resets != [1] or projected != list(range(2, native_step+1)) or transported!=projected:
        raise ValueError('Exactly one initial reset and one projection per following native step required')
    return steps-1


def audit(directory):
    directory = Path(directory).resolve()
    d = json.loads((directory/'stages.json').read_text())
    capture = json.loads((directory/'capture.json').read_text())
    if (not capture['complete'] or d['exchange_error'] or not d.get('native_interface_transport_requested') or
            not d['native_transfer_packet_saved'] or not d['scheduler_alignment_observed']):
        raise ValueError('Complete aligned successful native interface capture required')
    resolve(d)  # Check current source dataset provenance.
    interface = d['native_interface_transport']
    pressure_coupled = interface.get('pressure_coupled', False)
    compact=interface.get('compact_transport',False)
    high_order=interface.get('high_order_transport',False)
    transport_stage='Extrapolate Velocities Again' if compact else 'Project Pressure'
    if (interface['schema'] != ('raftsim.native_liquid_interface.v2' if high_order else 'raftsim.native_liquid_interface.v1') or interface.get('renderer_coupled', False) or
            interface['pressure_or_renderer_coupled'] != pressure_coupled or
            compact!=d.get('native_unified_transport_requested',False) or
            interface.get('velocity_interpolation','trilinear')!=('averaged-quadratic-normal-tent-transverse-v1' if compact else 'trilinear') or
            interface['update_stage'] != transport_stage+': after stage; internal interface halos exchanged after transport'):
        raise ValueError('Unknown live interface capture contract')
    if high_order and (not compact or not d.get('native_high_order_interface_requested') or
            not d.get('native_advection_velocity_halo_exchange') or interface.get('diagnostic_width') != 8 or
            interface.get('scalar_transport') != 'limited-bfecc-rk2-regional-v1' or
            not interface.get('intermediate_scalar_validity_halos_exchanged') or
            interface.get('solid_source') != 'same-step-native-boundary-w-1-or-3'):
        raise ValueError('Complete native high-order solid/halo contract required')
    repo = Path(__file__).resolve().parents[2]
    initial_directory = repo/'tmp/south-fork-liquid-interface-20260911'
    manifest_path = initial_directory/'manifest.json'
    if hashlib.sha256(manifest_path.read_bytes()).hexdigest() != interface['initial_manifest_sha256']:
        raise ValueError('Initial interface package changed')
    initial = json.loads(manifest_path.read_text())
    steps = interface['native_steps']
    transport_steps = validate_transport_schedule(stage_groups(d), steps, transport_stage)
    dt = np.asarray(interface['fluid_delta_seconds'], dtype=float)
    engine_dt = np.asarray(interface['engine_delta_seconds'], dtype=float)
    if (not isinstance(steps, int) or steps != d['native_transfer_packet_step'] or steps < 2 or
            interface['initial_reset_native_step'] != 1 or interface['first_transport_native_step'] != 2 or
            interface['transport_steps'] != transport_steps or
            dt.shape != (transport_steps,) or engine_dt.shape != (transport_steps,) or not np.isfinite(dt).all() or
            not np.isfinite(engine_dt).all() or (dt<0).any() or (engine_dt<0).any() or
            dt.sum() != interface['fluid_elapsed_seconds'] or (compact and not np.array_equal(dt,engine_dt))):
        raise ValueError('Missing current tick fluid/engine clocks')
    records = d['native_transfer_packet']
    if (len(initial['regions']) != 12 or [r['region_id'] for r in records] != list(range(12)) or
            [r['region_id'] for r in interface['regions']] != list(range(12))):
        raise ValueError('All native interface owners required')
    updated = validate_ledger(interface['diagnostic_words'], [r['cells'] for r in records], transport_steps, high_order)
    predicted, actual, differences, files = [], [], [], {}
    before_fields, velocities, solids = [], [], []

    def read_scalar(base, name, cells):
        path = (base/name).resolve()
        if path.parent != base.resolve():
            raise ValueError('Interface file escapes its capture directory')
        data = np.fromfile(path, dtype='<f4').astype(float)
        if data.size != np.prod(cells) or not np.isfinite(data).all():
            raise ValueError('Truncated or nonfinite interface scalar')
        files[str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
        return data.reshape(tuple(cells[::-1]))

    for r, pair, original in zip(records, interface['regions'], initial['regions']):
        cells = np.asarray(r['cells'])
        if r['projection_native_step'] != steps or r['projection_output_stage'] != 'Project Pressure: after stage':
            raise ValueError('Transport is not paired with actual post-pressure velocity')
        before = read_scalar(directory, pair['before'], cells)
        after = read_scalar(directory, pair['after'], cells)
        first = read_scalar(initial_directory, original['initial_phi'], cells)
        if files[str((initial_directory/original['initial_phi']).resolve())] != original['initial_phi_sha256']:
            raise ValueError('Changed initial scalar')
        field='advection_velocity' if compact else 'projection_velocity_after'
        if compact and (r.get('advection_native_step')!=steps or r.get('advection_velocity_stage')!='Extrapolate Velocities Again: after stage'):
            raise ValueError('Unified interface requires same-step post-extrapolation velocity')
        velocity = load_field(directory, r, field, 4)[..., :3]
        h = np.asarray(original['spacing_cm'], dtype=np.float32).astype(float)
        if not np.allclose(h, np.asarray(r['extent_cm'])/cells, atol=2e-6, rtol=0):
            raise ValueError('Interface and native velocity metrics differ')
        if high_order:
            phase = load_field(directory, r, 'projection_boundary', 4)[..., 3]
            if not np.isin(phase, [0, 1, 2, 3]).all():
                raise ValueError('Invalid captured native solid classification')
            if len(before_fields) and not np.array_equal(h, np.asarray(initial['regions'][0]['spacing_cm'], dtype='<f4').astype(float)):
                raise ValueError('Regional high-order cell metrics differ')
            before_fields.append(before);velocities.append(velocity);solids.append(np.isin(phase, [1, 3]))
            for name in (r[field], r['projection_boundary']):
                path = directory/name;files[str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
        else:
            expected, status = advect(before, velocity, h, dt[-1], np.full(3, 2), cells-2,compact)
            if not status['candidate_step_valid']:
                raise ValueError('Independent native-step backtrace leaves the available stencil')
            predicted.append(expected)
        actual.append(after)
        changes = before-first
        differences.append(dict(region_id=r['region_id'], retained_changed_samples=int(np.count_nonzero(changes)),
                                max_retained_change_cm=float(np.abs(changes).max())))
    if high_order:
        from liquid_interface_regional_highorder import advect_regions
        predicted, status = advect_regions(before_fields, velocities, solids, h, dt[-1], d['halo_columns_niagara'], compact)
        validate_ledger(status.ravel(), [r['cells'] for r in records], 1, True)
    else:
        predicted = exchange_scalars(predicted, d['halo_columns_niagara'])
    errors = np.concatenate([(a-p).ravel() for a,p in zip(actual, predicted)])
    worst = float(np.abs(errors).max())
    if worst > .02:
        raise ValueError(f'Native interface differs from paired CPU transport/halo reference: {worst} cm')
    changed = sum(r['retained_changed_samples'] for r in differences)
    if not changed:
        raise ValueError('Interface remained at its initial data rather than being retained/advanced')
    shared_velocity_verified = False
    if d.get('native_advection_velocity_halo_exchange', False):
        # A paired arithmetic match alone cannot prove adjacent owners trace
        # through the same flow. Verify the new native exchange independently.
        from audit_liquid_velocity_halos import audit as audit_velocity_halos
        shared_velocity_verified = audit_velocity_halos(directory)['native_shared_velocity_verified']
        if not shared_velocity_verified:
            raise ValueError('Declared native shared velocity has mismatched halos or stage counts')
    usage = None
    if high_order:
        ledger = np.asarray(interface['diagnostic_words'], dtype=np.int64).reshape(transport_steps, 12, 8)
        usage = dict(higher_order_samples=int(ledger[..., 3].sum()),
                     extrema_limited_samples=int(ledger[..., 4].sum()),
                     explicit_accuracy_fallback_samples=int(ledger[..., 5].sum()),
                     reverse_trace_failures=int(ledger[..., 6].sum()),
                     selected_native_counters=ledger[-1].tolist(),
                     selected_cpu_counters=status.tolist(),
                     counter_bit_equality_is_not_scalar_arithmetic_gate=True)
    return dict(native_steps=steps, transport_steps=transport_steps, fluid_elapsed_seconds=float(dt.sum()),
                fluid_delta_range_seconds=[float(dt.min()), float(dt.max())],
                engine_delta_range_seconds=[float(engine_dt.min()), float(engine_dt.max())],
                updated_owned_samples_across_steps=updated, paired_compared_samples=len(errors),
                max_paired_cpu_error_cm=worst, paired_rms_error_cm=float(np.sqrt(np.mean(errors**2))),
                retained_changed_samples=changed, regions=differences, source_files_sha256=files,
                internal_interface_halos_verified=True, native_step_ledger_verified=True,
                boundary_model=interface['boundary_model'], pressure_coupled=pressure_coupled,
                compact_transport=compact,velocity_stage=transport_stage,
                shared_velocity_verified=shared_velocity_verified,
                high_order_transport=high_order,
                high_order_usage=usage,
                renderer_coupled=False,
                physical_visual_or_performance_acceptance=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    result = audit(args.directory)
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('regions','source_files_sha256')}, indent=2))
