"""Compare independent MAC extension with installed native code and cache data.

Only private in-memory grids are modified. No scene/cache/velocity correction,
new bake or enabled foam driver. Interior provenance is not physical validity.
"""
import argparse
import ctypes
import gc
import hashlib
import json
from pathlib import Path
import re
import sys
import time

import bpy
import manta
import numpy as np
import openvdb

sys.path.insert(0, str(Path(__file__).resolve().parent))
from water_feature_native_mac_extension import reconstruct_extension, corner_provenance, INTERIOR
from water_feature_dense_mac import trilinear


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def native_view(grid, shape, integer=False):
    """Borrow grid-only contiguous x-fastest ABI; never particle-vector ABI.

Refuse double builds and wrong sizes. All borrowed views die before grids;
the caller checks copied payload against independent OpenVDB before use.
"""
    if manta.DOUBLEPRECISION or (grid.getSizeX(), grid.getSizeY(), grid.getSizeZ()) != tuple(shape):
        raise ValueError('Only matched float32 native 3D grid ABI supported')
    pointer = grid.getDataPointer()
    if not isinstance(pointer, str) or not re.fullmatch(r'(?:0x)?[0-9a-fA-F]+', pointer):
        raise ValueError('Unexpected native grid address format')
    address = int(pointer, 16)
    if address <= 0:
        raise ValueError('Null native grid payload')
    components, scalar = (1, ctypes.c_int32) if integer else (3, ctypes.c_float)
    buffer = (scalar*int(np.prod(shape)*components)).from_address(address)
    array = np.ctypeslib.as_array(buffer)
    return (array.reshape(shape[::-1]).transpose(2, 1, 0) if integer else
            array.reshape((*shape[::-1], 3)).transpose(2, 1, 0, 3))


def native_replay(flags, velocity, distance, into_obstacle, name, data=None, world_size=None):
    """Native isolated extension, with input/output/flags readback checks."""
    shape = flags.shape
    solver = manta.Solver(name=name, gridSize=manta.vec3(*shape), dim=3)
    fg = solver.create(manta.FlagGrid, name='flags')
    vg = solver.create(manta.MACGrid, name='velocity')
    error, result = None, None
    try:
        if data is not None:
            if manta.load(name=str(data.resolve()), objects=[fg, vg], worldSize=world_size) != 1:
                raise ValueError('Native VDB load failed')
        else:
            # Manufactured values are written only to our new in-memory grids.
            view = native_view(fg, shape, integer=True); view[:] = flags; del view
            view = native_view(vg, shape); view[:] = velocity; del view
        np.testing.assert_array_equal(native_view(fg, shape, integer=True).copy(), flags)
        np.testing.assert_array_equal(native_view(vg, shape).copy(), velocity)
        manta.extrapolateMACSimple(flags=fg, vel=vg, distance=distance, intoObs=into_obstacle)
        result = native_view(vg, shape).copy()
        np.testing.assert_array_equal(native_view(fg, shape, integer=True).copy(), flags)
        if not np.isfinite(result).all():
            raise ValueError('Nonfinite native output')
    except Exception as exc:
        # A retained traceback can keep a grid child alive past solver cleanup.
        # Preserve the error text, not borrowed grid references in stack frames.
        error = f'{type(exc).__name__}: {exc}'
        exc.__traceback__ = None
    finally:
        manta.releaseMG(solver)
        del vg, fg
        gc.collect()
        del solver
        gc.collect()
    if error is not None:
        raise ValueError(error)
    return result


def compare(flags, velocity, distance, into_obstacle, name, **kwargs):
    independent = reconstruct_extension(flags, velocity, distance, into_obstacle)
    native = native_replay(flags, velocity, distance, into_obstacle, name, **kwargs)
    a, b = independent['velocity'][INTERIOR], native[INTERIOR]
    # No fitted tolerance or subset selection: every interior scalar must match.
    np.testing.assert_array_equal(a, b)
    return independent, dict(name=name, shape=list(flags.shape), distance=distance,
        into_obstacle=into_obstacle, interior_scalars=a.size,
        bitexact_interior=True, boundary_parity_claimed=False,
        native_modified_private_grid_only=True)


def controls():
    rows = []
    rng = np.random.default_rng(20260930)
    # Empty, single fluid cell, planar front, combined flags, obstacle mixtures.
    for index in range(5):
        shape = (11, 9, 7)
        flags = np.full(shape, 4, np.int32)
        velocity = rng.uniform(-5, 5, (*shape, 3)).astype(np.float32)
        if index == 1:
            flags[5, 4, 3] = 1
        elif index == 2:
            flags[2:4, :, :] = 1
        elif index >= 3:
            flags = rng.choice(np.array([1, 2, 4, 9, 17], np.int32), size=shape)
        if index == 4:
            velocity[2:4, 2, 3, 0] = [1e8, -1e8]
        for distance, into in ((0, False), (1, False), (4, False), (4, True)):
            name = f'mac_extension_control_{index}_{distance}_{int(into)}'
            _, row = compare(flags, velocity, distance, into, name)
            rows.append(row)
    return rows


def quantiles(values):
    return np.quantile(np.asarray(values, float), [0, .05, .5, .95, 1]).tolist() if len(values) else None


def diagnostic_velocity(velocity, coordinate, scale):
    """Audit-only interpolation, never an enabled foam field or transport API."""
    result = []
    for axis in range(3):
        offset = np.full(3, .5); offset[axis] = 0
        value = trilinear(velocity[..., axis], coordinate-offset)
        if value is None:
            return None
        result.append(float(value)*scale)
    return np.asarray(result)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case-dir', type=Path, required=True)
    parser.add_argument('--calibration', type=Path, required=True)
    parser.add_argument('--reference', type=Path, required=True)
    parser.add_argument('--frames', type=int, nargs='+', default=[168, 192, 214])
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    if args.output.exists():
        raise FileExistsError(args.output)
    started = time.perf_counter()
    setup, cal, reference = [json.loads(p.read_text()) for p in
                            (args.case_dir/'setup.json', args.calibration, args.reference)]
    if (bpy.app.build_hash != b'fbe6228777e7' or setup['case'] != 'eddy'
            or not setup['grid_aligned_domain'] or setup['fractional_obstacles']
            or not cal['passed'] or cal['blender'] != bpy.app.version_string
            or cal['domain_dimensions_m'] != setup['dimensions_m']
            or any(cal[k] != setup[k] for k in ('fps', 'resolution'))
            or not reference['complete'] or not reference['originals_unchanged']
            or reference['accepted'] or reference['domain_time_scale'] != 1.
            or len(set(args.frames)) != len(args.frames)
            or any(not 1 <= f <= setup['frames'] for f in args.frames)):
        raise ValueError('Exact installed build, matched captured FLIP case and diagnostic reference required')
    hashes = dict(reference['original_input_sha256'])
    scene = args.case_dir/'feature-mesh.blend'
    if Path(bpy.data.filepath).resolve() != scene.resolve():
        raise ValueError('Open the preserved mesh scene to initialize native Manta inheritance before probing')
    # Blender installs grid inheritance methods when a fluid domain initializes.
    # The bare imported Manta wrappers do not expose base-grid ABI methods.
    bpy.context.scene.frame_set(reference['frame'])
    domain = bpy.data.objects['Feature liquid'].evaluated_get(bpy.context.evaluated_depsgraph_get())
    state = domain.modifiers[0].domain_settings
    if (state.time_scale != 1. or state.simulation_method != 'FLIP'
            or bpy.context.scene.render.fps != setup['fps']
            or bpy.context.scene.render.fps_base != 1.
            or tuple(state.domain_resolution) != tuple(setup['grid_alignment']['expected_grid_cells'])
            or not all(hasattr(kind, 'getDataPointer') for kind in (manta.FlagGrid, manta.MACGrid))):
        raise ValueError('Matched native scene/clock and initialized grid API required')
    for path in (scene, args.case_dir/'setup.json', args.calibration, args.reference):
        hashes[str(path.resolve())] = digest(path)
    modules = [Path(__file__), Path(__file__).with_name('water_feature_native_mac_extension.py'),
               Path(__file__).with_name('test_water_feature_native_mac_extension.py'),
               Path(__file__).with_name('water_feature_dense_mac.py')]
    code_hashes = {str(p.resolve()): digest(p) for p in modules}
    if any(digest(path) != sha for path, sha in hashes.items()):
        raise ValueError('Preserved source input changed')
    control_rows = controls()
    print('NATIVE_MAC_CONTROLS', len(control_rows), 'bitexact interior comparisons', flush=True)
    h = max(setup['dimensions_m'])/setup['resolution']
    origin = np.asarray(domain.matrix_world.translation)-np.asarray(state.domain_resolution)*h/2
    np.testing.assert_allclose(origin, setup['grid_alignment']['lower_m'], atol=1e-7, rtol=0)
    scale = cal['inferred_raw_velocity_to_mps']/setup['resolution']
    frames = []
    for frame in args.frames:
        data = args.case_dir/'cache'/'data'/f'fluid_data_{frame:04d}.vdb'
        hashes[str(data.resolve())] = digest(data)
        grids = [openvdb.read(str(data), name) for name in ('flags', 'velocity')]
        shape = tuple(grids[0].metadata['file_base_resolution'])
        if (shape != tuple(setup['grid_alignment']['expected_grid_cells'])
                or tuple(grids[1].metadata['file_base_resolution']) != shape
                or grids[1].metadata['class'] != 'staggered'):
            raise ValueError('Native flags/staggered-velocity mapping mismatch')
        flags = np.empty(shape, np.int32)
        velocity = np.empty((*shape, 3), np.float32)
        for grid, array in zip(grids, (flags, velocity)):
            grid.copyToArray(array)
        if frame == reference['frame']:
            np.testing.assert_array_equal(np.asarray(state.velocity_grid[:]).reshape((*shape[::-1], 3)).transpose(2, 1, 0, 3), velocity)
        independent, parity = compare(flags, velocity, 4, False, f'mac_extension_cache_{frame}',
                                      data=data, world_size=max(setup['dimensions_m']))
        delta = np.abs(independent['velocity'].astype(float)-velocity)*scale
        ls, lineage = independent['layers'], independent['obstacle_contact_lineage']
        values, counts = np.unique(flags, return_counts=True)
        row = dict(frame=frame, native_parity=parity, flag_value_counts=dict(zip(map(str, values), map(int, counts))),
            layer_component_counts=[dict(zip(map(str, v), map(int, c))) for v, c in
                (np.unique(ls[..., axis], return_counts=True) for axis in range(3))],
            obstacle_lineage_component_counts=[int(lineage[..., axis].sum()) for axis in range(3)],
            cache_replay_bitexact_supported=bool(np.array_equal(independent['velocity'][ls > 0], velocity[ls > 0])),
            cache_replay_supported_absolute_difference_mps_quantiles=quantiles(delta[ls > 0]),
            cache_replay_extension_absolute_difference_mps_quantiles=quantiles(delta[ls > 1]),
            cache_replay_seed_absolute_difference_mps_quantiles=quantiles(delta[ls == 1]),
            cache_precision_note='Serialized seed and extension rounding can break replay idempotence; no bound or physical validity inferred from small differences.',
            samples=[])
        if frame == reference['frame']:
            for old in reference['rows']:
                p = np.asarray(old['position_m'])
                provenance = corner_provenance(independent, (p-origin)/h)
                maximum_difference = None
                comparison = None
                if provenance is not None:
                    maximum_difference = max(float(delta[(*np.array(c['corner_indices']).T,
                                                       np.full(8, c['component']))].max()) for c in provenance['components'])
                if provenance is not None and provenance['all_corners_supported']:
                    coord = (p-origin)/h
                    cached = diagnostic_velocity(velocity, coord, scale)
                    rebuilt = diagnostic_velocity(independent['velocity'], coord, scale)
                    previous = old['unqualified_raw_mac_comparison']['velocity_mps']
                    np.testing.assert_allclose(cached, previous, atol=1e-12, rtol=0)
                    condition = old['unqualified_raw_mac_condition']
                    normal = np.asarray(condition['normal'])
                    required = condition['required_surface_normal_velocity_mps']
                    mismatch = float(rebuilt @ normal)-required
                    comparison = dict(rebuilt_velocity_mps=rebuilt.tolist(), cached_velocity_mps=cached.tolist(),
                        replay_cache_velocity_vector_difference_mps=float(np.linalg.norm(rebuilt-cached)),
                        replay_cache_normal_speed_difference_mps=abs(float((rebuilt-cached) @ normal)),
                        cached_signed_normal_mismatch_mps=condition['signed_normal_mismatch_mps'],
                        rebuilt_signed_normal_mismatch_mps=mismatch, accepted=False)
                row['samples'].append(dict(index=old['index'], column=old['column'], position_m=p.tolist(),
                    prior_normal_neighborhood_supported=old['prior_normal_neighborhood_supported'],
                    native_extension_provenance=provenance,
                    maximum_stencil_replay_cache_difference_mps=maximum_difference,
                    audit_only_kinematic_comparison=comparison,
                    prior_both_affine_fits_supported=old['status'] == 'measured',
                    physical_velocity_qualified=False))
            samples = row['samples']
            row['sample_summary'] = dict(prespecified_queries=len(samples),
                all_corners_supported=sum(bool(s['native_extension_provenance'] and s['native_extension_provenance']['all_corners_supported']) for s in samples),
                any_obstacle_lineage=sum(bool(s['native_extension_provenance'] and s['native_extension_provenance']['any_obstacle_lineage']) for s in samples),
                maximum_stencil_replay_cache_difference_mps_quantiles=quantiles([s['maximum_stencil_replay_cache_difference_mps'] for s in samples if s['maximum_stencil_replay_cache_difference_mps'] is not None]),
                normal_neighborhood_failures_retained=sum(not s['prior_normal_neighborhood_supported'] for s in samples))
            row['paired_kinematic_cohorts'] = []
            for label, cohort in (
                    ('all_prespecified_supported', samples),
                    ('prior_both_affine_fits_supported', [s for s in samples if s['prior_both_affine_fits_supported']]),
                    ('no_obstacle_contact_lineage', [s for s in samples if s['native_extension_provenance'] and not s['native_extension_provenance']['any_obstacle_lineage']]),
                    ('prior_normal_neighborhood_supported', [s for s in samples if s['prior_normal_neighborhood_supported']])):
                comparisons = [s['audit_only_kinematic_comparison'] for s in cohort if s['audit_only_kinematic_comparison'] is not None]
                row['paired_kinematic_cohorts'].append(dict(label=label, prespecified_queries=len(cohort), measured_queries=len(comparisons),
                    cached_absolute_normal_mismatch_mps_quantiles=quantiles([abs(c['cached_signed_normal_mismatch_mps']) for c in comparisons]),
                    rebuilt_absolute_normal_mismatch_mps_quantiles=quantiles([abs(c['rebuilt_signed_normal_mismatch_mps']) for c in comparisons]),
                    replay_cache_normal_speed_difference_mps_quantiles=quantiles([c['replay_cache_normal_speed_difference_mps'] for c in comparisons]),
                    replay_cache_velocity_vector_difference_mps_quantiles=quantiles([c['replay_cache_velocity_vector_difference_mps'] for c in comparisons]),
                    accepted=False))
        frames.append(row)
        print('NATIVE_MAC_FRAME', json.dumps({k: v for k, v in row.items() if k != 'samples'}), flush=True)
    if any(digest(path) != sha for path, sha in {**hashes, **code_hashes}.items()):
        raise ValueError('Input or executed module changed during audit')
    report = dict(complete=True, accepted=False, originals_unchanged=True,
        blender=bpy.app.version_string, blender_build_hash=bpy.app.build_hash.decode(),
        origin_m=origin.tolist(), cell_m=h, calibrated_grid_velocity_to_mps=scale,
        controls=control_rows, frames=frames, original_input_sha256=hashes, source_code_sha256=code_hashes,
        source_algorithm_url='https://raw.githubusercontent.com/blender/blender/fbe6228777e7/extern/mantaflow/preprocessed/fastmarch.cpp',
        source_algorithm_sha256='60013aabf3632d8a599a11885c3050fa7d44fc6e4d4b04c94b0a875596cd5c3a',
        elapsed_s=time.perf_counter()-started,
        limitations='Native code parity only for all interior components of manufactured/private loaded grids. Boundary copy and obstacle-normal unprojection are omitted, boundary provenance unsupported. Replaying a final extension is not a full frame reproduction or same-time mesh/velocity qualification. Native support is not physical validity. No field/mesh/cache correction, foam motion, render, clip, scene save or acceptance.')
    with args.output.open('x') as stream:
        json.dump(report, stream, indent=2)
    print('NATIVE_MAC_RESULT', json.dumps(dict(complete=True, accepted=False, originals_unchanged=True,
        controls=len(control_rows), frames=len(frames), elapsed_s=report['elapsed_s'], output=str(args.output))), flush=True)


if __name__ == '__main__':
    main()
