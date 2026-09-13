"""Locate disagreements between duplicated grid extensions without changing them."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from liquid_interface_global import layout
from diagnose_liquid_projection_packet import load_field


def compare(fields, offsets, shape):
    result = np.zeros((*shape, *fields[0].shape[3:]), dtype=float)
    written = np.zeros(shape, bool); rows = []
    for owner, (field, (ox, oy)) in enumerate(zip(fields, offsets, strict=True)):
        nz, ny, nx = field.shape[:3]; box = (slice(None), slice(oy, oy+ny), slice(ox, ox+nx))
        prior = written[box]; target = result[box]
        delta = np.abs(target-field)
        maximum = delta.max(axis=-1) if delta.ndim == 4 else delta
        z, y, x = np.indices((nz, ny, nx)); gx, gy = x+ox, y+oy
        physical_xy = (gx >= 2) & (gx < shape[2]-2) & (gy >= 2) & (gy < shape[1]-2)
        mismatch = prior & (maximum > 0)
        selected = np.argwhere(mismatch)
        peak = None
        if len(selected):
            p = selected[np.argmax(maximum[mismatch])]; iz, iy, ix = p
            peak = dict(global_xyz=[int(ix+ox), int(iy+oy), int(iz)],
                        earlier_value=np.asarray(target[tuple(p)]).tolist(),
                        owner_value=np.asarray(field[tuple(p)]).tolist())
        rows.append(dict(owner=owner, differing_samples=int(mismatch.sum()),
                         physical_xy_differing_samples=int((mismatch & physical_xy).sum()),
                         exterior_xy_differing_samples=int((mismatch & ~physical_xy).sum()),
                         max_difference=float(maximum[mismatch].max(initial=0)), peak=peak))
        # Keep the first observed value solely for comparison. Never use this
        # unresolved assembled field as a solver input or reference prediction.
        target[~prior] = field[~prior]; written[box] = True
    return dict(whole_grid_agrees=not any(r['differing_samples'] for r in rows),
                physical_xy_agrees=not any(r['physical_xy_differing_samples'] for r in rows), regions=rows)


def diagnose(directory):
    directory = directory.resolve(); m = json.loads((directory/'stages.json').read_text())
    records = m['native_transfer_packet']; pairs = m['native_interface_transport']['regions']
    offsets, shape = layout([r['cells'] for r in records], m['halo_columns_niagara'])
    result = {}; files = [directory/'stages.json']
    for name in ('velocity', 'boundary_phase', 'before_scalar'):
        if name == 'before_scalar':
            fields = [np.fromfile(directory/p['before'], dtype='<f4').reshape(r['cells'][::-1]) for p, r in zip(pairs, records, strict=True)]
            files.extend(directory/p['before'] for p in pairs)
        else:
            key = 'advection_velocity' if name == 'velocity' else 'projection_boundary'
            fields = [load_field(directory, r, key, 4) for r in records]
            fields = [f[..., :3] if name == 'velocity' else f[..., 3] for f in fields]
            files.extend(directory/r[key] for r in records)
        if any(not np.isfinite(f).all() for f in fields):
            raise ValueError('Finite original extension fields required')
        result[name] = compare(fields, offsets, shape)
    result.update(schema='raftsim.exterior_extension_diagnosis.v1', native_step=m['native_transfer_packet_step'],
                  samples_not_averaged_or_changed=True, whole_grid_reference_accepted=False,
                  physical_or_visual_acceptance=False,
                  source_files_sha256={str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in files})
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path); parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    result = diagnose(args.directory)
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')
    print(json.dumps({k: {a: b for a, b in result[k].items() if a != 'regions'} for k in ('velocity', 'boundary_phase', 'before_scalar')}, indent=2))
