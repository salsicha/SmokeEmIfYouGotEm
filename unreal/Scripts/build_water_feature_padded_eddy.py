"""Fresh native eddy: three cells below the SAME bed; preserve old evidence.

Padding is a computational-boundary change, not a changed physical bed or
contact thickness. This is a controlled candidate, never automatic acceptance.
"""
import argparse
import hashlib
import json
from pathlib import Path
import runpy
import sys
import bpy
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from prepare_modular_water_feature import settings_snapshot


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def boundaries():
    result = {}
    for obj in bpy.data.objects:
        mods = [m for m in obj.modifiers if m.type == 'FLUID' and m.fluid_type != 'DOMAIN']
        if not mods:
            continue
        mesh = obj.data
        geometry = dict(vertices=[v.co[:] for v in mesh.vertices],
                        polygons=[list(p.vertices) for p in mesh.polygons],
                        matrix=[list(row) for row in obj.matrix_world])
        result[obj.name] = dict(geometry_sha256=hashlib.sha256(
            json.dumps(geometry, sort_keys=True).encode()).hexdigest(),
            fluid_type=mods[0].fluid_type,
            settings=settings_snapshot(mods[0].effector_settings
                if mods[0].fluid_type == 'EFFECTOR' else mods[0].flow_settings))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reference', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    if args.output.exists():
        raise FileExistsError(args.output)
    if bpy.app.build_hash != b'fbe6228777e7':
        raise ValueError('Pinned native Blender build required')
    scripts = Path(__file__).resolve().parent
    deps = [Path(__file__), args.reference,
            scripts/'build_water_feature_lab.py', scripts/'prepare_modular_water_feature.py',
            scripts/'liquid_review_geometry.py', scripts/'water_feature_grid_alignment.py']
    hashes = {str(p.resolve()): digest(p) for p in deps}
    bpy.ops.wm.open_mainfile(filepath=str(args.reference.resolve()))
    old_boundaries = boundaries()
    old_domain = bpy.data.objects['Feature liquid']
    old_settings = settings_snapshot(old_domain.modifiers[0].domain_settings)
    old_gravity = list(bpy.context.scene.gravity)
    old_center = list(old_domain.location)
    # Object.dimensions can reflect an evaluated cached liquid mesh. Measure
    # the authored domain cage, not the already-baked free-surface bounds.
    cage = np.array([list(old_domain.matrix_world @ v.co) for v in old_domain.data.vertices])
    old_dimensions = (cage.max(0)-cage.min(0)).tolist()
    sys.argv = [str(scripts/'build_water_feature_lab.py'), '--', '--case', 'eddy',
                '--output', str(args.output.resolve()), '--resolution', '80', '--frames', '192',
                '--approach-height', '.45', '--inlet-speed', '2', '--tailwater', '.3',
                '--grid-aligned-domain', '--modular']
    runpy.run_path(str(scripts/'build_water_feature_lab.py'), run_name='__main__')
    if boundaries() != old_boundaries or list(bpy.context.scene.gravity) != old_gravity:
        raise ValueError('Physical sources/solids/gravity differ: candidate rejected before bake')
    domain = bpy.data.objects['Feature liquid']
    state = domain.modifiers[0].domain_settings
    expected = settings_snapshot(state)
    differences = {k: [old_settings[k], v] for k, v in expected.items() if old_settings[k] != v}
    if any(not (k.startswith('cache_frame_') or (k.startswith('has_cache_baked_') and v[1] is False))
           for k, v in differences.items()):
        raise ValueError('Unexpected physical-domain setting difference: '+str(differences))
    h = .075
    if not np.allclose(old_dimensions, (6., 1.575, 2.925), atol=1e-6, rtol=0):
        raise ValueError('Matched original domain required')
    # Fresh empty cache is already assigned. Never mutate a preserved cache.
    if any(p.is_file() for p in (args.output/'cache').rglob('*')):
        raise ValueError('Fresh empty candidate cache required')
    domain.dimensions.z = old_dimensions[2] + 3*h
    domain.location.z = old_center[2] - 1.5*h
    bpy.context.view_layer.objects.active = domain
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if boundaries() != old_boundaries or settings_snapshot(state) != expected:
        raise ValueError('Padding changed physical boundaries or solver settings')
    bpy.context.view_layer.update()
    shape = (80, 21, 42)
    origin = np.asarray(domain.location) - np.array(shape)*h/2
    old_origin = np.asarray(old_center) - np.array((80, 21, 39))*h/2
    if not np.allclose(origin + (0,0,3*h), old_origin, atol=2e-7, rtol=0):
        raise ValueError('Original world grid knots not preserved by padding')
    setup_path = args.output/'setup.json'
    setup = json.loads(setup_path.read_text())
    setup.update(dimensions_m=list(domain.dimensions),
                 grid_alignment=dict(lower_m=origin.tolist(),
                     upper_m=(origin+np.array(shape)*h).tolist(), dimensions_m=list(domain.dimensions),
                     allocated_shape=list(shape), cell_m=h, bottom_padding_cells=3),
                 boundary_control='Three extra computational cells below unchanged authored bed; same cell size and physics.',
                 physical_boundaries_unchanged=True, reference_blend=str(args.reference.resolve()))
    setup_path.write_text(json.dumps(setup, indent=2))
    (args.output/'domain-settings.json').write_text(json.dumps(settings_snapshot(state), indent=2))
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=str((args.output/'feature.blend').resolve()))
    if any(digest(p) != sha for p, sha in hashes.items()):
        raise ValueError('Preserved dependencies changed during preparation')
    receipt = dict(complete=True, accepted=False, dependency_sha256=hashes,
        physical_boundaries=old_boundaries, physical_boundaries_unchanged=True,
        gravity_unchanged=True, original_center_m=old_center, original_dimensions_m=old_dimensions,
        center_m=list(domain.location), dimensions_m=list(domain.dimensions), origin_m=origin.tolist(),
        shape=list(shape), cell_m=h, original_grid_knots_preserved=True,
        domain_setting_differences=differences, scope=__doc__)
    (args.output/'padding-preflight.json').write_text(json.dumps(receipt, indent=2))
    print('PADDED_EDDY_PREPARED', json.dumps(dict(shape=shape, origin_m=origin.tolist(),
          physical_boundaries_unchanged=True)), flush=True)


if __name__ == '__main__':
    main()
