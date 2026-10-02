"""Finest qualified moving-tank samples and explicit chord-volume check.

Requires independent ALL-step readback and preliminary gates on EVERY local
trial. Never falls back to a coarser/easier trial to hide a failed refinement.
Still a short sloshing calibration, not an accepted through-flow standing wave.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from water_feature_quadratic_surface import surface_weights, triangle_volume


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ('audit', 'qualified', 'output'):
        parser.add_argument('--'+key, type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    audit, qualified = (json.loads(p.read_text()) for p in (args.audit, args.qualified))
    local = [r for r in audit['runs'] if r['pressure_mode'] == 'discontinuous_p1']
    if not qualified['complete'] or len(local) != 3 or any(not r['preliminary_motion_gate_passed'] or r['failure'] for r in local):
        raise ValueError('All local physics/refinement gates required before views; no coarser fallback')
    for r in local:
        q = next(x for x in qualified['runs'] if x['label'] == r['label'])
        if q['all_completed_steps_checked'] != r['requested_steps'] or not q['preliminary_motion_gate_passed']:
            raise ValueError('Incomplete independent all-step physical check')
    selected = max(local, key=lambda r: r['refinement']); arrays = selected['arrays']
    pins = {str(args.audit.resolve()): digest(args.audit), str(args.qualified.resolve()): digest(args.qualified),
        str(Path(__file__).resolve()): digest(__file__), str(Path(__file__).with_name('water_feature_quadratic_surface.py').resolve()): digest(Path(__file__).with_name('water_feature_quadratic_surface.py')),
        **qualified['dependency_sha256']}
    if any(digest(p) != sha for p, sha in pins.items()):
        raise ValueError('Qualified trajectory changed')
    positions = np.load(arrays['positions'], allow_pickle=False); times = np.load(arrays['times'], allow_pickle=False)
    cells = np.load(arrays['cells'], allow_pickle=False); vertex_cells = np.load(arrays['vertex_cells'], allow_pickle=False)
    w, faces = surface_weights(vertex_cells, cells, positions.shape[1], 8)
    indices = [int(np.argmin(np.abs(times-t))) for t in np.arange(21)*.02]
    if any(abs(times[i]-target) > 1e-12 for i, target in zip(indices, np.arange(21)*.02)):
        raise ValueError('Exact declared physical sample times required')
    poses = np.array([w@positions[i] for i in indices]); volumes = np.array([triangle_volume(p, faces) for p in poses])
    curve_volumes = np.array([selected['proofs'][i-1]['volume_m3'] if i else selected['material_mass_kg']/1000 for i in indices])
    error = float(np.max(np.abs(volumes-curve_volumes)))
    if error > 3e-5 or np.any(volumes <= 0):
        raise ValueError('Display triangle chords change excessive physical volume')
    # Explicitly colored material-node markers, NOT foam or native particles.
    reference = positions[0]; top = np.isclose(reference[:, 2], .5+.02*np.cos(np.pi*reference[:, 0]), rtol=0., atol=1e-12)
    available = np.flatnonzero(top); marker_ids = []
    for target_x in (.2, .4, .6, .8):
        distances = (reference[available, 0]-target_x)**2+(reference[available, 1]-.3)**2
        marker_ids.append(int(available[np.argmin(distances)]))
    markers = positions[indices][:, marker_ids]; args.output.mkdir(); outputs = {}; saved = {}
    for name, array in dict(poses=poses, faces=faces, times=times[indices], markers=markers, triangle_volumes=volumes,
                            curved_volumes=curve_volumes).items():
        p = args.output/(name+'.npy')
        with p.open('xb') as stream:
            np.save(stream, array, allow_pickle=False)
        saved[name] = str(p.resolve()); outputs[str(p.resolve())] = digest(p)
    if any(digest(p) != sha for p, sha in pins.items()):
        raise ValueError('Surface sampling changed actual liquid')
    result = dict(complete=True, accepted=False, selected_trial=selected['label'], arrays=saved,
        dependency_sha256=pins, outputs_sha256=outputs, display_vertices=poses.shape[1], display_triangles=len(faces),
        maximum_triangle_chord_volume_error_m3=error, marker_material_node_indices=marker_ids,
        physical_duration_s=.4, scope='Finest independently qualified preliminary 3D sloshing trial, welded samples of actual curved boundary. Markers are diagnostic material nodes, not foam. Not standing-wave/feature or visual acceptance.')
    with (args.output/'report.json').open('x') as stream:
        json.dump(result, stream, indent=2); stream.write('\n')


if __name__ == '__main__':
    main()
