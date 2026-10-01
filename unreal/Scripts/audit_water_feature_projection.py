"""Read cached MAC divergence away from free surfaces and solids.

This distinguishes cached interior velocity consistency from interface-volume
drift. It is not a record of substep pressure residuals or an exact mass budget.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import bpy
import numpy as np
import openvdb

sys.path.insert(0, str(Path(__file__).resolve().parent))
from water_feature_mac_divergence import mac_divergence, interior_liquid_mask


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--calibration', type=Path, required=True)
    parser.add_argument('--frames', type=int, nargs='+', required=True)
    args = parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    if args.output.exists():
        raise FileExistsError(args.output)
    root = Path(bpy.data.filepath).parent
    setup = json.loads((root/'setup.json').read_text())
    cal = json.loads(args.calibration.read_text())
    assert cal['passed'] and cal['blender'] == bpy.app.version_string
    assert cal['resolution'] == setup['resolution'] and cal['fps'] == setup['fps']
    assert cal['domain_dimensions_m'] == setup['dimensions_m']
    assert cal.get('simulation_method', 'FLIP') == setup.get('simulation_method', 'FLIP')
    scale = cal['inferred_raw_velocity_to_mps']/setup['resolution']
    rows = []
    for frame in args.frames:
        bpy.context.scene.frame_set(frame)
        obj = bpy.data.objects['Feature liquid'].evaluated_get(bpy.context.evaluated_depsgraph_get())
        state = obj.modifiers[0].domain_settings
        dims = tuple(state.domain_resolution)
        path = root/'cache'/'data'/f'fluid_data_{frame:04d}.vdb'
        grids = [openvdb.read(str(path), name) for name in ('phi', 'phi_obstacle', 'velocity')]
        assert grids[2].metadata['class'] == 'staggered'
        arrays = [np.empty(dims, np.float32), np.empty(dims, np.float32), np.empty((*dims, 3), np.float32)]
        for grid, array in zip(grids, arrays):
            assert tuple(grid.metadata['file_base_resolution']) == dims
            grid.copyToArray(array)
        np.testing.assert_array_equal(np.asarray(state.velocity_grid[:]).reshape((*dims[::-1], 3)).transpose(2, 1, 0, 3), arrays[2])
        mask = interior_liquid_mask(*arrays[:2])
        spacing = np.asarray(state.cell_size)
        np.testing.assert_allclose(np.asarray(obj.dimensions)/dims, spacing, rtol=1e-5)
        measures = []
        # Isotropic solver coordinates versus physical-axis interpretation.
        # Neither calibration nor cached end-frame divergence establishes the
        # exact pressure residual or volume-conservation mechanism at substeps.
        for name, h in (('isotropic_solver_grid_scaled', [spacing[2]]*3),
                        ('engine_anisotropic_same_velocity_scale', spacing)):
            div = mac_divergence(arrays[2]*scale, h)[mask]
            if not len(div):
                raise ValueError('No fully supported interior liquid cells')
            measures.append(dict(mapping=name, cells=len(div), mean_per_second=float(div.mean()),
                                 rms_per_second=float(np.sqrt(np.mean(div**2))),
                                 absolute_quantiles_per_second=np.quantile(np.abs(div), [.5, .95, .99, 1.]).tolist()))
        row = dict(frame=frame, original_vdb_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                   native_velocity_matches=True, measures=measures)
        rows.append(row)
        print('CACHED_INTERIOR_DIVERGENCE', json.dumps(row), flush=True)
    args.output.write_text(json.dumps(dict(frames=rows, accepted=False,
        scope='Cached end-frame MAC divergence only, excluding interfaces/solids. Isotropic and same-scale anisotropic mappings are distinguished. Not substep pressure residuals, full boundary flux, mass conservation or proof of a reconstruction defect.'), indent=2))


if __name__ == '__main__':
    main()
