"""Inspect cached solver level sets independently of the rendered liquid mesh.

Run in Blender Python, which supplies openvdb. Negative-voxel volume is a
grid-resolution diagnostic, not an exact conservative cut-cell mass integral.
"""
import argparse
import json
from pathlib import Path
import sys

import numpy as np
import openvdb


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--case-dir', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--frames', type=int, nargs='+', required=True)
    args = p.parse_args(sys.argv[sys.argv.index('--')+1:])
    if args.output.exists():
        raise FileExistsError(args.output)
    rows = []
    for frame in args.frames:
        path = args.case_dir/'cache'/'data'/f'fluid_data_{frame:04d}.vdb'
        phi = openvdb.read(str(path), 'phi')
        dims = tuple(phi.metadata['file_base_resolution'])
        voxel_volume = float(np.prod(phi.transform.voxelSize()))
        arrays = {}
        for name in ('phi', 'phi_previous', 'phi_inflow', 'phi_obstacle', 'flags'):
            grid = phi if name == 'phi' else openvdb.read(str(path), name)
            array = np.empty(dims, np.int32 if name == 'flags' else np.float32)
            grid.copyToArray(array)
            if not np.isfinite(array).all():
                raise ValueError(f'Nonfinite field {name}')
            arrays[name] = array
        flags, counts = np.unique(arrays['flags'], return_counts=True)
        outside_solid = arrays['phi_obstacle'] >= 0
        rows.append(dict(frame=frame, grid_dimensions=list(dims), voxel_volume_m3=voxel_volume,
            negative_phi_volume_m3=float(np.sum(arrays['phi'] < 0)*voxel_volume),
            negative_phi_outside_solid_volume_m3=float(np.sum((arrays['phi'] < 0)&outside_solid)*voxel_volume),
            negative_previous_phi_volume_m3=float(np.sum(arrays['phi_previous'] < 0)*voxel_volume),
            negative_inflow_phi_volume_m3=float(np.sum(arrays['phi_inflow'] < 0)*voxel_volume),
            flag_histogram={str(int(v)):int(n) for v,n in zip(flags, counts)},
            phi_range=[float(arrays['phi'].min()), float(arrays['phi'].max())]))
        print('SOLVER_VOLUME', json.dumps(rows[-1]), flush=True)
    args.output.write_text(json.dumps(dict(frames=rows, accepted=False,
        scope='Negative level-set voxel counts from original VDB, independent of render mesh. Not exact solver mass or a measured air fraction.'), indent=2))


if __name__ == '__main__':
    main()
