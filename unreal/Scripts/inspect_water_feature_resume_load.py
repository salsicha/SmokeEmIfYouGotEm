"""Read-only cache/native-loader diagnostic; no bake, save, or cache writes."""
import sys
from pathlib import Path
import bpy
import manta
import numpy as np
import openvdb

sys.path.insert(0, str(Path(__file__).resolve().parent))
from probe_water_feature_native_transport import actual_space, CACHE_NAMES
from probe_water_feature_solver_stages import grid_array
from audit_water_feature_native_mac_extension import native_view


def main():
    root = Path(bpy.data.filepath).resolve().parent
    domain = bpy.data.objects['Feature liquid']
    state = domain.modifiers[0].domain_settings
    # No cache-end/timestep setters here: they invoke native cache deletion.
    # This diagnostic may relocate a loaded path in memory, but never invalidate.
    if '--' in sys.argv:
        raise ValueError('Cache mutation/alternate-directory arguments are not supported')
    cache = root/'cache'
    state.cache_directory = str(cache)
    bpy.context.scene.frame_set(192)
    space, identifier = actual_space((80,21,39))
    path = cache/'data'/'fluid_data_0192.vdb'
    print('DOMAIN_SIZE', space[f'domainSize_s{identifier}'], flush=True)
    print('VDB_FIELDS', [(g.name, str(type(g))) for g in openvdb.readAllGridMetadata(str(path))], flush=True)
    space['set_manta_debuglevel'](1)
    for label, keys in [('all_grids', list(CACHE_NAMES)), ('velocity', ['vel']), ('liquid', ['phi','phiTmp','phiParts']),
        ('boundaries', ['phiObs','phiObsIn','phiIn','phiOut','phiOutIn','flags','velTmp'])]:
        result = manta.load(name=str(path), objects=[space[f'{k}_s{identifier}'] for k in keys], worldSize=6.)
        print('LOAD_RESULT', label, repr(result), flush=True)
        for key in keys:
            grid = openvdb.read(str(path), CACHE_NAMES[key])
            integer, vector = key=='flags', key.startswith('vel')
            expected = np.empty((80,21,39,3) if vector else (80,21,39), np.int32 if integer else np.float32)
            grid.copyToArray(expected)
            actual = (native_view(space[f'{key}_s{identifier}'],(80,21,39),integer=integer).copy()
                if vector or integer else grid_array(space[f'{key}_s{identifier}'],(80,21,39)))
            print('FIELD', key, int(np.count_nonzero(actual!=expected)), float(np.max(np.abs(actual-expected))), flush=True)
    print('PRIMARY_LOAD', manta.load(name=str(path), objects=[space[f'pVel_pp{identifier}'], space[f'pp_s{identifier}']], worldSize=6.), flush=True)
    print('PRIMARY_COUNT', space[f'pp_s{identifier}'].pySize(), flush=True)
    del space, domain


if __name__ == '__main__':
    error = None
    try:
        main()
    except Exception as exc:
        error = f'{type(exc).__name__}: {exc}'
        exc.__traceback__ = None
    if error:
        print('RESUME_INSPECTION_FAILED', error, flush=True)
        raise SystemExit(1)
