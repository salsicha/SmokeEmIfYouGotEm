"""Read original VDBs and refine a liquid/obstacle interface-volume integral."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import time
import bpy
import numpy as np
import openvdb

sys.path.insert(0, str(Path(__file__).resolve().parent))
from water_feature_cell_volume import reconstructed_volume, reconstructed_volume_bounds


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--frames', type=int, nargs='+', required=True)
    parser.add_argument('--subdivisions', type=int, nargs='+', default=[2, 4, 8, 16])
    parser.add_argument('--bounds', action='store_true', help='Also bound each reconstructed-field integral using subinterval corners')
    args = parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    if args.output.exists():
        raise FileExistsError(args.output)
    root = Path(bpy.data.filepath).parent
    setup = json.loads((root/'setup.json').read_text())
    rows = []
    for frame in args.frames:
        bpy.context.scene.frame_set(frame)
        obj = bpy.data.objects['Feature liquid'].evaluated_get(bpy.context.evaluated_depsgraph_get())
        state = obj.modifiers[0].domain_settings
        path = root/'cache'/'data'/f'fluid_data_{frame:04d}.vdb'
        phi = openvdb.read(str(path), 'phi')
        dims = tuple(phi.metadata['file_base_resolution'])
        assert dims == tuple(state.domain_resolution)
        spacing = np.asarray(state.cell_size)
        np.testing.assert_allclose(np.asarray(obj.dimensions)/dims, spacing, rtol=1e-5)
        np.testing.assert_allclose(np.asarray(obj.dimensions), setup['dimensions_m'], rtol=1e-5)
        np.testing.assert_allclose(np.asarray(obj.matrix_world.to_3x3()), np.eye(3), atol=1e-6)
        arrays = []
        for grid in (phi, openvdb.read(str(path), 'phi_obstacle')):
            array = np.empty(dims, np.float32)
            grid.copyToArray(array)
            arrays.append(array)
        start = time.monotonic()
        refined = [reconstructed_volume(*arrays, spacing, n) for n in args.subdivisions]
        bounds = [reconstructed_volume_bounds(*arrays, spacing, n) for n in args.subdivisions] if args.bounds else []
        row = dict(frame=frame, original_vdb_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                   engine_cell_size_m=spacing.tolist(), storage_cell_size_m=list(phi.transform.voxelSize()),
                   center_sign_volume_engine_m3=float(np.sum((arrays[0] < 0)&(arrays[1] >= 0))*np.prod(spacing)),
                   refinement=refined, bounds=bounds, evaluation_seconds=time.monotonic()-start)
        rows.append(row)
        print('PARTIAL_CELL_VOLUME', json.dumps(row), flush=True)
    report = dict(case=str(root), frames=rows, accepted=False,
                  scope='Midpoint integration of trilinearly reconstructed cell-center phi intersected with nonnegative obstacle phi. Constant extension through domain-edge half cells. Quadrature refinement is not solver spatial convergence, conserved mass, resolved gas, or hydraulic acceptance.')
    args.output.write_text(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
