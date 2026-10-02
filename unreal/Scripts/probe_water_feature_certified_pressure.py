"""Changed certified-aperture/native-flags pressure experiment, not a bake."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import time
import bpy
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
from probe_water_feature_subcell_pressure import run, metrics
from probe_water_feature_pressure_boundary_response import native_response, cohorts, stats
from probe_water_feature_native_transport import actual_space, scalar_view
from water_feature_consistent_pressure import PressureBoundary, flux_divergence


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inputs', type=Path, required=True)
    parser.add_argument('--apertures', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    if args.output.exists():
        raise FileExistsError(args.output)
    inputs = json.loads(args.inputs.read_text()); apertures = json.loads(args.apertures.read_text())
    if Path(bpy.data.filepath).resolve() != Path(inputs['source_blend']).resolve():
        raise ValueError('Exact original native host required')
    hashes = {**inputs['dependency_sha256'], **inputs['outputs_sha256'],
        **apertures['dependency_sha256'], **apertures['outputs_sha256'],
        **{str(p.resolve()): digest(p) for p in (args.inputs, args.apertures, Path(__file__))}}
    for name in ('probe_water_feature_subcell_pressure.py', 'probe_water_feature_pressure_boundary_response.py',
        'probe_water_feature_native_transport.py', 'probe_water_feature_solver_stages.py',
        'audit_water_feature_native_mac_extension.py', 'water_feature_consistent_pressure.py', 'water_feature_mac_divergence.py'):
        p = Path(__file__).with_name(name); hashes[str(p.resolve())] = digest(p)
    if any(digest(p) != sha for p, sha in hashes.items()):
        raise ValueError('Pinned original/certificate input changed')
    shape = tuple(inputs['shape']); h = inputs['cell_m']; geometry = np.empty((*shape, 3), np.float32)
    for axis, path in enumerate(apertures['arrays']):
        slices = [slice(None)]*3; slices[axis] = slice(0, shape[axis])
        geometry[..., axis] = np.load(path, allow_pickle=False)[tuple(slices)]/(h*h)
    fields = {name: np.load(path, allow_pickle=False) for name, path in inputs['fields'].items()}
    bpy.context.scene.frame_set(inputs['frame']); source, identifier = actual_space(shape)
    settings = dict(boundaryWidth=source[f'boundaryWidth_s{identifier}'],
                    fracThreshold=source[f'fracThreshold_s{identifier}'], FlagFluid=int(source['FlagFluid']))
    empty_type, outflow_type = int(source['FlagEmpty']), int(source['FlagOutflow'])
    def fingerprint():
        return {k: hashlib.sha256(scalar_view(source[f'{k}_s{identifier}'], shape).copy().tobytes()).hexdigest()
                for k in ('phi', 'phiTmp', 'phiObs', 'phiObsIn')}
    host = fingerprint(); args.output.mkdir(); folder = args.output/'native-projection'; folder.mkdir()
    # Do NOT rerun the rejected fixed-cached-flags or old native-fraction solve.
    native, _ = run('geometry-native-rebuilt-flags', fields, geometry, shape, settings, None, folder)
    if not native['complete']:
        raise ValueError('Changed certified native projection did not complete: '+native['error'])
    flags, before = (np.load(native['arrays'][k], allow_pickle=False) for k in ('flags', 'velocity-before'))
    model = PressureBoundary(flags, fields['phi'], geometry, settings['FlagFluid'], empty_type, outflow_type)
    started = time.perf_counter(); candidate, pressure, solve = model.project(before); elapsed = time.perf_counter()-started
    cast, rhs = native_response(flags, fields['phi'], geometry, before, pressure, False, candidate)
    maximum_rhs = float(np.max(np.abs(rhs[model.fluid])))
    if maximum_rhs > 5e-5:
        raise ValueError('Changed candidate failed native float32 RHS allowance')
    np.testing.assert_array_equal(cast[model.inverse_distance == 0], before[model.inverse_distance == 0])
    outputs = dict(native['outputs_sha256']); arrays = {}
    for name, array in (('velocity-consistent-float64', candidate), ('velocity-consistent-native', cast),
                        ('pressure-consistent', pressure), ('native-consistent-rhs', rhs),
                        ('response-coefficient', model.inverse_distance)):
        path = args.output/(name+'.npy')
        with path.open('xb') as stream:
            np.save(stream, array, allow_pickle=False)
        arrays[name] = str(path.resolve()); outputs[str(path.resolve())] = digest(path)
    masks = cohorts(flags, geometry, settings['FlagFluid'], empty_type, outflow_type)
    projected = np.load(native['arrays']['velocity-projected'], allow_pickle=False)
    flow = {label: {name: stats(flux_divergence(v, geometry)*2.5, mask) for name, mask in masks.items()}
            for label, v in (('before', before), ('native_projected', projected), ('consistent_native', cast))}
    active = model.inverse_distance > 0
    flat = int(np.argmax(np.where(active, np.abs(cast), -1))); index = np.array(np.unravel_index(flat, cast.shape))
    face = np.array(inputs['origin_m'])+(index[:3]+.5)*h; face[index[3]] -= .5*h
    peak = dict(index=index.tolist(), face_world_m=face.tolist(), area_fraction=float(geometry[tuple(index)]),
                velocity_native=float(cast[tuple(index)]), velocity_m_per_second=float(cast[tuple(index)])*h*2.5)
    if fingerprint() != host or any(digest(p) != sha for p, sha in hashes.items()):
        raise ValueError('Owned certified pressure changed original inputs/host')
    report = dict(complete=True, accepted=False, originals_unchanged=True, frame=inputs['frame'],
        native=native, consistent_boundary=model.proof, projection=solve, reference_seconds=elapsed,
        native_rhs_maximum=maximum_rhs, fixed_native_rhs_allowance=5e-5, flux_cohorts=flow,
        arrays=arrays, outputs_sha256=outputs, dependency_sha256=hashes, peak_active_face=peak,
        native_projection_primary_particles_advanced=False, native_projection_surface_changed=False,
        frozen_response_faces_bitexact=True, candidate_scope='Uniform-density pressure reference loaded into owned native float32 grids, not the native CFD solver or a validated physical time step',
        caveat='Exact blocked box faces are closed without an aperture cutoff. Remaining partial apertures, volumes/inertia, source chronology, particle contact, surface reconstruction and spatial/temporal convergence remain unqualified. A small flux residual alone cannot accept physical velocities or a new bake.')
    (args.output/'report.json').write_text(json.dumps(report, indent=2)+'\n')
    print('CERTIFIED_PRESSURE_RESULT', solve['iterations'], maximum_rhs, flow['consistent_native']['all'], peak, flush=True)


if __name__ == '__main__':
    main()
