"""Compare a new aligned scene with preserved original geometry and calibration."""
import argparse
import json
from pathlib import Path
import sys

import bpy
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from audit_water_feature_stage_volumes import sha256
from prepare_modular_water_feature import settings_snapshot


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--original', type=Path, required=True)
    parser.add_argument('--calibration', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--require-data', action='store_true')
    args = parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    if args.output.exists():
        raise FileExistsError(args.output)
    root = Path(bpy.data.filepath).parent
    setup = json.loads((root/'setup.json').read_text())
    baseline = json.loads((args.original.parent/'setup.json').read_text())
    cal = json.loads(args.calibration.read_text())
    if not (setup['grid_aligned_domain'] and cal['passed'] and cal['grid_aligned_domain']
            and cal['domain_dimensions_m'] == setup['dimensions_m']
            and cal['resolution'] == setup['resolution'] and cal['fps'] == setup['fps']
            and cal['blender'] == bpy.app.version_string):
        raise ValueError('Need aligned scene and matching passed native calibration')
    for key in ('case', 'resolution', 'frames', 'fps', 'gravity_mps2', 'fractional_obstacles',
                'inlet_velocity_mps', 'inlet_depth_m', 'approach_height_m', 'nominal_tailwater_m',
                'obstacle_bounds_m', 'nominal_section_flux_m3s'):
        assert setup[key] == baseline[key], key
    original_hash = sha256(args.original)
    candidates = {obj.name: obj for obj in bpy.context.scene.objects}
    with bpy.data.libraries.load(str(args.original.resolve()), link=False) as (source, target):
        original_names = list(source.objects)
        target.objects = list(original_names)
    # Blender may rename appended IDs. Match exact original names recorded by
    # the library list, instead of guessing suffixes for legitimately dotted names.
    originals = dict(zip(original_names, target.objects))
    original_settings = settings_snapshot(originals['Feature liquid'].modifiers[0].domain_settings)
    domain = candidates['Feature liquid']
    current_settings = settings_snapshot(domain.modifiers[0].domain_settings)
    physical = lambda values: {k: v for k, v in values.items()
                               if not k.startswith(('cache_', 'has_cache_', 'is_cache_'))}
    assert physical(current_settings) == physical(original_settings), 'Other physical domain settings changed'
    geometry = []
    for name, original in originals.items():
        if name == 'Feature liquid' or original.type != 'MESH':
            continue
        current = candidates[name]
        # Appended, unlinked objects have no evaluated world matrix. All these
        # builder meshes are unparented/constraint-free, so compare their saved
        # transform components exactly instead of an unevaluated identity.
        assert current.parent is None and original.parent is None
        assert len(current.constraints) == len(original.constraints) == 0
        for attribute in ('location', 'rotation_euler', 'scale'):
            np.testing.assert_array_equal(getattr(current, attribute), getattr(original, attribute))
        a = np.array([vertex.co[:] for vertex in current.data.vertices])
        b = np.array([vertex.co[:] for vertex in original.data.vertices])
        np.testing.assert_array_equal(a, b)
        assert [tuple(p.vertices) for p in current.data.polygons] == [tuple(p.vertices) for p in original.data.polygons]
        geometry.append(dict(name=name, vertices=len(a), original_mesh_and_world_transform_match=True))
    np.testing.assert_allclose(domain.dimensions, setup['dimensions_m'], atol=1e-6)
    alignment = setup['grid_alignment']
    np.testing.assert_allclose(domain.matrix_world.translation, alignment['center_m'], atol=1e-6)
    rows = []
    if args.require_data:
        for frame in (1, 168, 288):
            bpy.context.scene.frame_set(frame)
            evaluated = domain.evaluated_get(bpy.context.evaluated_depsgraph_get())
            native = evaluated.modifiers[0].domain_settings
            assert list(native.domain_resolution) == alignment['expected_grid_cells']
            np.testing.assert_allclose(native.cell_size, [alignment['isotropic_cell_m']]*3, atol=1e-7)
            origin = np.asarray(evaluated.matrix_world @ native.start_point)
            np.testing.assert_allclose(origin, alignment['lower_m'], atol=1e-6)
            count = len(next(ps for ps in evaluated.particle_systems if ps.name.lower() == 'liquid').particles)
            assert count > 0
            rows.append(dict(frame=frame, cells=list(native.domain_resolution),
                             cell_size_m=list(native.cell_size), origin_m=origin.tolist(), primary_count=count))
    if sha256(args.original) != original_hash:
        raise ValueError('Original scene changed')
    report = dict(complete=True, accepted=False, original_blend_sha256=original_hash,
                  original_unchanged=True, calibration_sha256=sha256(args.calibration),
                  other_physical_domain_settings_match=True, geometry=geometry, native_data_checks=rows,
                  scope='Only domain shorter-axis bounds and cache schedule change; other meshes and physical settings match. Native coordinate checks when data is present. Not mass, mesh collision, secondary optics, trajectory persistence or hydraulic acceptance.')
    with args.output.open('x') as stream:
        json.dump(report, stream, indent=2)
    print('ALIGNED_SCENE_AUDIT', json.dumps(report), flush=True)


if __name__ == '__main__':
    main()
