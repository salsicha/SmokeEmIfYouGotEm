"""GPU operator cases: actual river fields plus explicit analytic failure cases.

Combining initial phi with a captured later velocity tests the transport
operator/metric, NOT a reconstructed step-600 surface or coupled trajectory.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from diagnose_liquid_projection_packet import load_field
from diagnose_liquid_volume_interface import diagnose
from liquid_interface_transport import advect


def prepare(interface, capture, output, compact=False):
    if output.exists():
        raise FileExistsError(output)
    proof = diagnose(capture)  # Reject failed trajectories/changed source data.
    source = json.loads((interface/'manifest.json').read_text())
    native = json.loads((capture/'stages.json').read_text())
    if source['native_dataset'] != native['native_dataset']['key']:
        raise ValueError('Interface and velocity datasets differ')
    output.mkdir(parents=True)
    records = []
    sha = lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

    def emit(name, phi, velocity, spacing, dt, origin):
        phi = np.asarray(phi, dtype='<f4')
        velocity = np.asarray(velocity, dtype='<f2')
        spacing, dt = np.asarray(spacing, dtype='<f4'), float(np.float32(dt))
        cells = np.asarray(phi.shape[::-1])
        lo, hi = np.full(3, 2), cells-2
        expected, details = advect(phi, velocity[..., :3].astype(float), spacing, dt, lo, hi,compact)
        arrays = {'phi':phi, 'velocity':velocity, 'expected':expected.astype('<f4')}
        files = {}
        for key, data in arrays.items():
            path = output/f'{name}-{key}.bin'
            data.tofile(path)
            files[key] = dict(file=path.name, sha256=sha(path))
        records.append(dict(name=name, cells=cells.tolist(), spacing_cm=spacing.tolist(), dt=dt,
                            update_min=lo.tolist(), update_max=hi.tolist(), files=files, **details, **origin))

    for r, n in zip(source['regions'], native['native_transfer_packet']):
        if r['region_id'] != n['region_id'] or r['cells'] != n['cells']:
            raise ValueError('Region layout/order mismatch')
        path = interface/r['initial_phi']
        if path.parent != interface or sha(path) != r['initial_phi_sha256']:
            raise ValueError('Initial interface changed or path escaped')
        phi = np.fromfile(path, dtype='<f4').reshape(tuple(r['cells'][::-1]))
        field='advection_velocity' if compact else 'projection_velocity_after'
        v = load_field(capture, n, field, 4)
        if n['projection_native_step'] != native['native_transfer_packet_step']:
            raise ValueError('Unpaired native velocity')
        emit(f'region-{r["region_id"]:03d}', phi, v, r['spacing_cm'], 1/60,
             dict(source='actual South Fork initial phi and captured '+field,
                  source_phi_sha256=sha(path), source_velocity_sha256=sha(capture/n[field])))
    z, y, x = np.indices((8, 10, 12))
    h = np.array([50, 50, 100/3], dtype='<f4')
    phi = (z+.5)*h[2]-.1*(x+.5)*h[0]+.2*(y+.5)*h[1]-120
    for name, v in [('stationary', [0, 0, 0, 0]), ('translated', [130, -75, 21, 0]), ('outside-trace', [60000, 0, 0, 0])]:
        velocity = np.empty((*phi.shape, 4), dtype='<f2')
        velocity[:] = v
        emit(name, phi, velocity, h, 1 if name=='outside-trace' else 1/60, dict(source='analytic operator regression'))
    manifest = dict(schema='raftsim.liquid_interface_transport_cases.v1', cases=records,
                    compact_transport=compact,
                    interface_manifest_sha256=sha(interface/'manifest.json'),
                    native_stages_sha256=sha(capture/'stages.json'),
                    verified_native_commits=proof['verified_compact_commits'],
                    cpu_reference='float64 RK2; '+('compact compatible velocity, trilinear scalar' if compact else 'trilinear interpolation')+' of exact float32/float16 uploaded inputs',
                    gpu_error_tolerance_cm=.02,
                    acceptance_scope='Transport operator only; not a coupled native trajectory, scene render or FPS proof')
    (output/'manifest.json').write_text(json.dumps(manifest, indent=2, allow_nan=False)+'\n')
    return [dict(name=r['name'], updated=r['updated_cells'], rejected=r['rejected_trace_cells']) for r in records]


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('interface', type=Path)
    parser.add_argument('capture', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--compact',action='store_true')
    args = parser.parse_args()
    print(json.dumps(prepare(args.interface.resolve(), args.capture.resolve(), args.output.resolve(),args.compact), indent=2))
