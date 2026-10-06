"""Reconstructed eddy tracers from original dense MAC fields, not FLIP identities."""
import argparse
from collections import Counter
import json
from pathlib import Path
import sys

import bpy
import numpy as np
import openvdb

sys.path.insert(0, str(Path(__file__).resolve().parent))
from audit_water_feature_pathlines import advance
from audit_water_feature_stage_volumes import sha256
from water_feature_dense_mac import DenseMacField


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--calibration', type=Path, required=True)
    parser.add_argument('--start', type=int, default=168)
    parser.add_argument('--end', type=int, default=288)
    args = parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    if args.output.exists():
        raise FileExistsError(args.output)
    root = Path(bpy.data.filepath).parent
    setup, cal = [json.loads(p.read_text()) for p in (root/'setup.json', args.calibration)]
    if (setup['case'] != 'eddy' or not cal['passed'] or cal['blender'] != bpy.app.version_string
            or cal['domain_dimensions_m'] != setup['dimensions_m']
            or any(cal[k] != setup[k] for k in ('resolution', 'fps'))
            or cal.get('simulation_method', 'FLIP') != setup.get('simulation_method', 'FLIP')
            or not 1 <= args.start < args.end <= setup['frames']):
        raise ValueError('Require matched native eddy calibration and available frame interval')
    bpy.context.scene.frame_set(args.start)
    obj = bpy.data.objects['Feature liquid'].evaluated_get(bpy.context.evaluated_depsgraph_get())
    state = obj.modifiers[0].domain_settings
    shape = tuple(state.domain_resolution)
    engine_spacing = np.asarray(state.cell_size)
    engine_origin = np.asarray(obj.matrix_world @ state.start_point)
    isotropic_spacing = np.full(3, max(setup['dimensions_m'])/setup['resolution'])
    isotropic_origin = np.asarray(obj.matrix_world.translation)-np.array(shape)*isotropic_spacing/2
    mappings = dict(engine_field=(engine_origin, engine_spacing),
                    isotropic_object_centered=(isotropic_origin, isotropic_spacing))
    scale = cal['inferred_raw_velocity_to_mps']/setup['resolution']
    seeds = [[float(x), float(y), z] for x in np.linspace(3.2, 4.6, 6)
             for y in np.linspace(.05, .65, 4) for z in (.15, .25)]
    groups = {name: {str(n): [dict(seed_m=p, positions_m=[p], stopped=None) for p in seeds]
                     for n in (4, 8)} for name in mappings}
    receipts = []
    checks = {args.start, (args.start+args.end)//2, args.end}

    def fields(frame):
        path = root/'cache'/'data'/f'fluid_data_{frame:04d}.vdb'
        before = sha256(path)
        grids = [openvdb.read(str(path), name) for name in ('phi', 'phi_obstacle', 'velocity')]
        if grids[2].metadata['class'] != 'staggered':
            raise ValueError('Velocity must be native staggered MAC, not centered')
        arrays = [np.empty(shape, np.float32), np.empty(shape, np.float32), np.empty((*shape, 3), np.float32)]
        for grid, array in zip(grids, arrays):
            assert tuple(grid.metadata['file_base_resolution']) == shape
            grid.copyToArray(array)
        if frame in checks:
            bpy.context.scene.frame_set(frame)
            evaluated = bpy.data.objects['Feature liquid'].evaluated_get(bpy.context.evaluated_depsgraph_get())
            native = evaluated.modifiers[0].domain_settings
            np.testing.assert_array_equal(np.asarray(native.velocity_grid[:]).reshape((*shape[::-1], 3)).transpose(2, 1, 0, 3), arrays[2])
        if sha256(path) != before:
            raise ValueError('Original VDB changed during readback')
        receipts.append(dict(frame=frame, original_vdb_sha256=before, native_velocity_checked=frame in checks))
        return {name: DenseMacField(*arrays, origin, spacing, scale)
                for name, (origin, spacing) in mappings.items()}

    a = fields(args.start)
    for frame in range(args.start, args.end):
        b = fields(frame+1)
        for name in mappings:
            for substeps in (4, 8):
                for track in groups[name][str(substeps)]:
                    advance(track, a[name], b[name], frame, setup['fps'], substeps,
                            np.asarray(setup['obstacle_bounds_m']), support_description='liquid/MAC-face')
        a = b
        if frame % 24 == 0:
            print('DENSE_PATHLINE_FRAME', frame+1,
                  {name: sum(t['stopped'] is None for t in groups[name]['8']) for name in groups}, flush=True)
    comparisons = {}
    for name in groups:
        errors = []
        for coarse, fine in zip(groups[name]['4'], groups[name]['8']):
            count = min(len(coarse['positions_m']), len(fine['positions_m']))
            distance = np.linalg.norm(np.array(coarse['positions_m'][:count])-np.array(fine['positions_m'][:count]), axis=1)
            errors.append(dict(seed_m=coarse['seed_m'], common_frames=count, max_difference_m=float(distance.max())))
        comparisons[name] = errors
    mapping_comparisons = []
    for engine, isotropic in zip(groups['engine_field']['8'], groups['isotropic_object_centered']['8']):
        count = min(len(engine['positions_m']), len(isotropic['positions_m']))
        distance = np.linalg.norm(np.array(engine['positions_m'][:count])-np.array(isotropic['positions_m'][:count]), axis=1)
        mapping_comparisons.append(dict(seed_m=engine['seed_m'], common_frames=count, max_difference_m=float(distance.max())))
    for receipt in receipts:
        path = root/'cache'/'data'/f"fluid_data_{receipt['frame']:04d}.vdb"
        if sha256(path) != receipt['original_vdb_sha256']:
            raise ValueError('Original cache changed during audit')
    report = dict(complete=True, accepted=False, source_blend=bpy.data.filepath,
                  start_frame=args.start, end_frame=args.end, fps=setup['fps'], substeps=[4, 8],
                  mappings={name: dict(origin_m=o.tolist(), spacing_m=s.tolist()) for name, (o, s) in mappings.items()},
                  raw_grid_velocity_to_mps=scale, calibration_sha256=sha256(args.calibration),
                  source_code_sha256={p.name: sha256(p) for p in [Path(__file__),
                      Path(__file__).with_name('water_feature_dense_mac.py'),
                      Path(__file__).with_name('audit_water_feature_pathlines.py')]},
                  original_vdb_receipts=receipts, originals_unchanged=True, tracks=groups,
                  step_halving=comparisons, mapping_sensitivity=mapping_comparisons,
                  outcomes={name: dict(Counter(t['stopped'] or 'complete' for t in group['8'])) for name, group in groups.items()},
                  limitations='Diagnostic tracers, not persistent FLIP identities or surface foam. All eight liquid/solid center neighbors plus both liquid/solid neighbors of every interpolation face required. Staggered trilinear velocity and linear frame interpolation with midpoint time stepping; no support extension, projection or clamping. Engine-field and isotropic mappings compared, not conflated. No automatic closed-circulation or hydraulic acceptance.')
    with args.output.open('x') as stream:
        json.dump(report, stream, indent=2)
    print('DENSE_PATHLINE_COMPLETE', report['outcomes'], flush=True)


if __name__ == '__main__':
    main()
