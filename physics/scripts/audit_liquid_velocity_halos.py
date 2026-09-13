"""Check actual same-step transport velocity against its physical-owner copies.

Exact storage equality is required: halo synchronization copies existing half
precision values, not an approximate physical operation. This does not establish
pressure accuracy, steady flow, interface volume, rendering or performance.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from audit_liquid_native_interface import exchange_scalars, validate_transport_schedule
from diagnose_liquid_projection_packet import load_field
from liquid_stage_journal import stage_groups


def compare(fields, columns):
    for value in fields:
        if value.ndim != 4 or value.shape[-1] != 4 or not np.isfinite(value).all():
            raise ValueError('Finite native RGBA velocity volumes required')
    expected = exchange_scalars(fields, columns)
    rows = []
    for owner, (a, b) in enumerate(zip(fields, expected)):
        delta = np.abs(a-b)
        rows.append(dict(region_id=owner, unequal_components=int(np.count_nonzero(delta)),
                         max_error_cm_s=float(delta[..., :3].max()),
                         physical_z_max_error_cm_s=float(delta[2:-2, ..., :3].max()),
                         unequal_auxiliary_components=int(np.count_nonzero(delta[..., 3]))))
    return dict(exact_owner_halos=all(r['unequal_components'] == 0 for r in rows), regions=rows,
                max_velocity_error_cm_s=max(r['max_error_cm_s'] for r in rows),
                unequal_components=sum(r['unequal_components'] for r in rows))


def audit(directory):
    directory = Path(directory).resolve()
    m = json.loads((directory/'stages.json').read_text())
    capture = json.loads((directory/'capture.json').read_text())
    if not capture['complete'] or m['exchange_error'] or not m['native_transfer_packet_saved']:
        raise ValueError('Complete successful paired native capture required')
    records = m['native_transfer_packet']
    if [r['region_id'] for r in records] != list(range(12)):
        raise ValueError('All twelve actual owners required')
    steps = m['native_transfer_packet_step']
    groups = list(stage_groups(m))
    validate_transport_schedule(groups, steps, 'Extrapolate Velocities Again')
    files = [directory/'stages.json']
    fields = []
    for r in records:
        if r['advection_native_step'] != steps or r['advection_velocity_stage'] != 'Extrapolate Velocities Again: after stage':
            raise ValueError('Mismatched velocity capture age/stage')
        path = (directory/r['advection_velocity']).resolve()
        if path.parent != directory:
            raise ValueError('Velocity path escapes capture')
        files.append(path)
        fields.append(load_field(directory, r, 'advection_velocity', 4))
    report = compare(fields, m['halo_columns_niagara'])
    exchange_requested = m.get('native_advection_velocity_halo_exchange', False)
    dispatches = m.get('advection_velocity_halo_dispatches', 0)
    observed = sum(g['entries'][0]['name'] == 'Extrapolate Velocities Again' for g in groups)
    schedule_verified = exchange_requested and dispatches == observed and observed >= steps-1
    report.update(schema='raftsim.advection_velocity_halo_audit.v1', native_step=steps,
                  exchange_requested=exchange_requested, recorded_dispatches=dispatches,
                  observed_transport_stages=observed, schedule_verified=schedule_verified,
                  native_shared_velocity_verified=report['exact_owner_halos'] and schedule_verified,
                  source_files_sha256={str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in files},
                  physical_visual_or_performance_acceptance=False)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    result = audit(args.directory)
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')
    print(json.dumps({k: v for k, v in result.items() if k not in ('regions', 'source_files_sha256')}, indent=2))
    raise SystemExit(0 if result['native_shared_velocity_verified'] else 1)
