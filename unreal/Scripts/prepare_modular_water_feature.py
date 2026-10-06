"""Copy a pristine prepared case for staged baking; preserve physical settings."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import bpy


def settings_snapshot(settings):
    result = {}
    for prop in settings.bl_rna.properties:
        name = prop.identifier
        if prop.is_readonly or name in ('cache_type', 'cache_directory'):
            continue
        if prop.type not in ('BOOLEAN', 'INT', 'FLOAT', 'STRING', 'ENUM'):
            continue
        value = getattr(settings, name)
        if getattr(prop, 'is_array', False):
            value = list(value)
        elif isinstance(value, set):
            value = sorted(value)
        result[name] = value
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    source = Path(bpy.data.filepath).resolve()
    setup = json.loads((source.parent/'setup.json').read_text())
    settings = bpy.data.objects['Feature liquid'].modifiers[0].domain_settings
    original_cache = Path(bpy.path.abspath(settings.cache_directory)).resolve()
    if any(path.is_file() for path in original_cache.rglob('*')):
        raise ValueError('Only a pristine prepared source may be copied')
    if settings.has_cache_baked_data or settings.has_cache_baked_mesh or settings.has_cache_baked_particles:
        raise ValueError('Source already baked')
    before = settings_snapshot(settings)
    args.output.mkdir(parents=True, exist_ok=False)
    settings.cache_type = 'MODULAR'
    settings.cache_directory = str((args.output/'cache').resolve())
    after = settings_snapshot(settings)
    if before != after:
        raise RuntimeError('Changing cache schedule altered other domain settings')
    blend = (args.output/'feature.blend').resolve()
    bpy.ops.wm.save_as_mainfile(filepath=str(blend))
    setup.update(blend=str(blend), bake_schedule='MODULAR',
                 staged_from_blend=str(source),
                 staged_from_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                 physical_settings_unchanged=True,
                 staging_scope='Base liquid first; mesh and secondary phases still enabled but not yet baked. Not a replacement liquid-only deliverable.')
    (args.output/'setup.json').write_text(json.dumps(setup, indent=2))
    (args.output/'domain-settings.json').write_text(json.dumps(after, indent=2))
    print('MODULAR_PREPARED', json.dumps(setup), flush=True)


if __name__ == '__main__':
    main()
