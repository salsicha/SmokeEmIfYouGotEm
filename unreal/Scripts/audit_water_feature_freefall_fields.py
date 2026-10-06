"""Check a completed free-fall calibration using original cached VDB fields.

No particle readback is used to measure the liquid's centroid here. Whole-cell
volume/centroid is a coarse independent diagnostic, not spatial convergence.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import bpy
import numpy as np
import openvdb


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    if args.output.exists():
        raise FileExistsError(args.output)
    root = Path(bpy.data.filepath).parent
    reference = json.loads((root/'calibration.json').read_text())
    rows = []
    for source_row in reference['frames']:
        frame = source_row['frame']
        bpy.context.scene.frame_set(frame)
        obj = bpy.data.objects['Calibration domain'].evaluated_get(bpy.context.evaluated_depsgraph_get())
        state = obj.modifiers[0].domain_settings
        path = root/'cache'/'data'/f'fluid_data_{frame:04d}.vdb'
        phi = openvdb.read(str(path), 'phi')
        dims = tuple(phi.metadata['file_base_resolution'])
        assert dims == tuple(state.domain_resolution)
        spacing = np.asarray(state.cell_size)
        origin = np.asarray(obj.matrix_world @ state.start_point)
        values = np.empty(dims, np.float32)
        phi.copyToArray(values)
        indices = np.argwhere(values < 0)
        if not len(indices):
            raise ValueError('Empty calibration liquid')
        world = origin+(indices+.5)*spacing
        native = openvdb.read(str(path), 'velocity')
        velocity = np.empty((*dims, 3), np.float32)
        native.copyToArray(velocity)
        assert np.isfinite(values).all() and np.isfinite(velocity).all()
        center_index = np.floor((world.mean(axis=0)-origin)/spacing).astype(int)
        grid_center = velocity[tuple(center_index)]
        rows.append(dict(frame=frame, seconds=source_row['seconds'],
                         negative_phi_centroid_m=world.mean(axis=0).tolist(),
                         particle_api_centroid_m=source_row['centroid_m'],
                         center_raw_grid_velocity=grid_center.tolist(),
                         center_api_grid_velocity_div_resolution=source_row['interior_grid_velocity_div_resolution'],
                         negative_phi_volume_m3=float(len(indices)*np.prod(spacing)),
                         original_vdb_sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    t = np.asarray([r['seconds'] for r in rows])
    z = np.asarray([r['negative_phi_centroid_m'][2] for r in rows])
    fit = np.polyfit(t, z, 2)
    acceleration = float(2*fit[0])
    volume = np.asarray([r['negative_phi_volume_m3'] for r in rows])
    report = dict(simulation_method=reference.get('simulation_method', 'FLIP'),
                  fitted_field_centroid_acceleration_mps2=acceleration,
                  requested_gravity_mps2=reference['requested_gravity_mps2'],
                  gravity_relative_error=abs(acceleration-reference['requested_gravity_mps2'])/abs(reference['requested_gravity_mps2']),
                  maximum_position_fit_residual_m=float(np.max(np.abs(np.polyval(fit, t)-z))),
                  sign_volume_range_relative=float(np.ptp(volume)/volume[0]),
                  accepted=False,
                  scope='Independent sign-volume centroid of the cached level set, not particle weighting, exact liquid mass, or hydraulic acceptance.',
                  frames=rows)
    args.output.write_text(json.dumps(report, indent=2))
    print('INDEPENDENT_FREEFALL_FIELDS', json.dumps({k:v for k,v in report.items() if k != 'frames'}), flush=True)


if __name__ == '__main__':
    main()
