"""Decode actual Niagara grid readback; no particle-count volume assumption."""
from pathlib import Path
import argparse
import json
import numpy as np


def load_fields(directory):
    directory = Path(directory)
    metadata = json.loads((directory/'grids.json').read_text())
    fields = {}
    for grid in metadata['grids']:
        if not grid['readback_saved']:
            continue
        nx, ny, nz = grid['texture_size']
        float32 = grid.get('encoding') == 'r32f'
        channels = 1 if float32 else 4
        raw = np.fromfile(directory/grid['file'], dtype='<f4' if float32 else '<f2')
        if raw.size != nx*ny*nz*channels:
            raise ValueError('Grid byte count mismatch')
        pixels = raw.reshape(nz, ny, nx, channels).astype(float)
        cx, cy, cz = grid['cells']
        tx, ty, tz = grid['tiles']
        for attribute in grid['attributes']:
            count = {'NiagaraFloat': 1, 'Vector2f': 2, 'Vector3f': 3, 'Vector4f': 4}.get(attribute['type'])
            if count is None:
                raise ValueError(f'Unknown attribute type {attribute}')
            index = attribute['offset']
            if grid['rgba_texture']:
                value = pixels[..., index:index+count]
            else:
                channels = []
                for channel in range(index, index+count):
                    x, y, z = channel % tx, channel//tx % ty, channel//(tx*ty)
                    channels.append(pixels[z*cz:(z+1)*cz, y*cy:(y+1)*cy, x*cx:(x+1)*cx, 0])
                value = np.stack(channels, axis=-1)
            if attribute['name'] in fields:
                raise ValueError('Ambiguous grid attribute name')
            fields[attribute['name']] = value
    return fields


def analyze(directory):
    fields = load_fields(directory)
    result = {'source': str(directory), 'readback_precision': 'see per-grid encoding in grids.json', 'fields': {},
              'physical_volume_calibrated': False, 'passed': False}
    for name, array in fields.items():
        finite = array[np.isfinite(array)]
        result['fields'][name] = dict(shape=list(array.shape), nonfinite=int((~np.isfinite(array)).sum()),
                                     min=float(finite.min()), max=float(finite.max()))
    boundary = fields['SolidVelocity_Boundary']
    velocity = fields['Velocity']
    if boundary.shape != (24, 68, 68, 4) or velocity.shape != (24, 68, 68, 3):
        raise ValueError('Expected registered 68x68x24 fixture')
    dx, dz = 21/64, 8/24
    mask = np.rint(boundary[..., 3]).astype(int)
    native = mask[:, 2:66, 2:66]
    result['physical_grid_classification_counts'] = {str(i): int((native == i).sum()) for i in np.unique(native)}
    result['fluid_cell_volume_m3_not_subcell_volume'] = float((native == 0).sum()*dx*dx*dz)
    sdf = fields.get('SDF')
    if sdf is not None and sdf.shape == (48, 136, 136, 1):
        result['render_sdf_negative_voxel_volume_m3_not_calibrated'] = float((sdf[:, 4:132, 4:132, 0] < 0).sum()*(dx/2)**2*(dz/2))
    faces = []
    for face, axis, sign, ghost, inner in [('west', 0, 1, 1, 2), ('east', 0, -1, 66, 65),
                                           ('south', 1, 1, 1, 2), ('north', 1, -1, 66, 65)]:
        b = boundary[:, 2:66, ghost, :] if axis == 0 else boundary[:, ghost, 2:66, :]
        v = velocity[:, 2:66, inner, :] if axis == 0 else velocity[:, inner, 2:66, :]
        inner_type = mask[:, 2:66, inner] if axis == 0 else mask[:, inner, 2:66]
        # Ghost normal speed is nonzero only for the prescribed wet virtual
        # boundary. The adjacent-cell measure is reported separately: not yet
        # asserted to be the exact staggered face flux of the pressure operator.
        wet = (np.rint(b[..., 3]) == 1) & (abs(b[..., axis]) > 0)
        faces.append(dict(face=face, driven_ghost_count=int(wet.sum()),
                          driven_ghost_adjacent_solid_count=int((wet & (inner_type == 1)).sum()),
                          driven_ghost_adjacent_empty_count=int((wet & (inner_type == 2)).sum()),
                          ghost_inward_flux_m3s=float((sign*b[..., axis]*wet).sum()/100*dx*dz),
                          adjacent_cell_inward_flux_m3s=float((sign*v[..., axis]*wet).sum()/100*dx*dz),
                          normal_velocity_difference_max_cm_s=float(abs(v[..., axis]-b[..., axis])[wet].max()) if wet.any() else 0.))
    result['faces'] = faces
    fluid = mask == 0
    interior = (fluid[1:-1, 1:-1, 1:-1] & fluid[1:-1, 1:-1, 2:] & fluid[1:-1, 1:-1, :-2] &
                fluid[1:-1, 2:, 1:-1] & fluid[1:-1, :-2, 1:-1] & fluid[2:, 1:-1, 1:-1] & fluid[:-2, 1:-1, 1:-1])
    divergence = (velocity[1:-1, 1:-1, 2:, 0]-velocity[1:-1, 1:-1, :-2, 0]+
                  velocity[1:-1, 2:, 1:-1, 1]-velocity[1:-1, :-2, 1:-1, 1]+
                  velocity[2:, 1:-1, 1:-1, 2]-velocity[:-2, 1:-1, 1:-1, 2])/(2*dx*100)
    before = fields['SimFloat'][1:-1, 1:-1, 1:-1, 0]
    rms = lambda a: float(np.sqrt(np.mean(a*a)))
    result['all_six_neighbors_fluid'] = dict(cell_count=int(interior.sum()),
        pre_projection_divergence_rms_per_s=rms(before[interior]),
        final_velocity_central_divergence_rms_per_s=rms(divergence[interior]))
    pressure = fields['Pressure'][..., 0]
    if np.isfinite(pressure).all():
        laplace = (pressure[1:-1, 1:-1, 2:]+pressure[1:-1, 1:-1, :-2]+
                   pressure[1:-1, 2:, 1:-1]+pressure[1:-1, :-2, 1:-1]+
                   pressure[2:, 1:-1, 1:-1]+pressure[:-2, 1:-1, 1:-1]-6*pressure[1:-1, 1:-1, 1:-1])/(dx*100)**2
        result['all_six_neighbors_fluid']['pressure_poisson_residual_times_dt_rms_per_s'] = rms((laplace/60-before)[interior])
        far = fluid.copy()
        for axis in range(3):
            for shift in (-2, -1, 1, 2):
                far &= np.roll(fluid, shift, axis=axis)
        far[:2] = far[-2:] = False
        far[:, :2] = far[:, -2:] = False
        far[:, :, :2] = far[:, :, -2:] = False
        wide = sum(np.roll(pressure, -2, axis=i)+np.roll(pressure, 2, axis=i)-2*pressure for i in range(3))/(4*(dx*100)**2)
        predicted = fields['SimFloat'][..., 0]-wide/60
        inner_far = far[1:-1, 1:-1, 1:-1]
        result['two_cell_fluid_interior'] = dict(cell_count=int(far.sum()),
            observed_divergence_rms_per_s=rms(divergence[inner_far]),
            central_operator_predicted_divergence_rms_per_s=rms(predicted[far]),
            observed_minus_predicted_rms_per_s=rms(divergence[inner_far]-predicted[far]))
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('directory', type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    result = analyze(args.directory)
    text = json.dumps(result, indent=2, allow_nan=False)+'\n'
    if args.output:
        if args.output.exists():
            raise FileExistsError(args.output)
        args.output.write_text(text)
    print(text)
