"""Locate native secondary phase particles in preserved cached liquid fields."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import bpy
import numpy as np
import openvdb

sys.path.insert(0, str(Path(__file__).resolve().parent))
from water_feature_phase_samples import sample_centers


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def quantiles(values):
    return np.quantile(values, [.05, .5, .95]).tolist() if len(values) else None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--frames', type=int, nargs='+', default=[168, 192, 214, 240, 264, 288])
    args = parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    if args.output.exists():
        raise FileExistsError(args.output)
    source = Path(bpy.data.filepath)
    root = source.parent
    setup = json.loads((root/'setup.json').read_text())
    bake = json.loads((root/'bake-particles.json').read_text())
    if (setup['case'] != 'eddy' or not setup.get('grid_aligned_domain')
            or not bake['baked_particles'] or not bake['copied_data_mesh_unchanged']
            or Path(bake['blend']).resolve() != source.resolve()):
        raise ValueError('Completed copied aligned eddy phases required')
    hashes = {str(source): digest(source)}
    rows = []
    for frame in args.frames:
        if not 1 <= frame <= setup['frames']:
            raise ValueError('Frame outside cache')
        bpy.context.scene.frame_set(frame)
        obj = bpy.data.objects['Feature liquid'].evaluated_get(bpy.context.evaluated_depsgraph_get())
        state = obj.modifiers[0].domain_settings
        shape = tuple(state.domain_resolution)
        spacing = np.full(3, max(setup['dimensions_m'])/setup['resolution'])
        origin = np.asarray(obj.matrix_world.translation)-np.array(shape)*spacing/2
        data = root/'cache'/'data'/f'fluid_data_{frame:04d}.vdb'
        particle_file = root/'cache'/'particles'/f'fluid_particles_{frame:04d}.vdb'
        hashes.update({str(p): digest(p) for p in (data, particle_file)})
        arrays = []
        for name in ('phi', 'phi_obstacle'):
            grid = openvdb.read(str(data), name)
            if tuple(grid.metadata['file_base_resolution']) != shape:
                raise ValueError('Field shape mismatch')
            array = np.empty(shape, np.float32)
            grid.copyToArray(array)
            arrays.append(array)
        phases = []
        for ps in obj.particle_systems:
            if ps.name.lower() not in ('foam', 'spray', 'bubbles'):
                continue
            count = len(ps.particles)
            positions, velocity = np.empty(count*3, np.float32), np.empty(count*3, np.float32)
            sizes = np.empty(count, np.float32)
            ps.particles.foreach_get('location', positions)
            ps.particles.foreach_get('velocity', velocity)
            ps.particles.foreach_get('size', sizes)
            positions, velocity = positions.reshape(-1, 3), velocity.reshape(-1, 3)
            if not np.isfinite(velocity).all() or not np.isfinite(sizes).all():
                raise ValueError('Nonfinite native particle attributes')
            phi, supported = sample_centers(arrays[0], positions, origin, spacing)
            solid, _ = sample_centers(arrays[1], positions, origin, spacing)
            phases.append(dict(name=ps.name, count=count, supported_count=int(supported.sum()),
                unsupported_count=int((~supported).sum()),
                interpolated_phi_cells_quantiles=quantiles(phi[supported]),
                fraction_negative_phi=float(np.mean(phi[supported] < 0)) if supported.any() else None,
                fraction_near_interface_one_cell=float(np.mean(np.abs(phi[supported]) <= 1)) if supported.any() else None,
                fraction_negative_obstacle_phi=float(np.mean(solid[supported] < 0)) if supported.any() else None,
                native_api_size_quantiles=quantiles(sizes), particle_display_size=ps.settings.particle_size,
                raw_api_speed_quantiles=quantiles(np.linalg.norm(velocity, axis=1)),
                position_bounds_m=[positions.min(axis=0).tolist(), positions.max(axis=0).tolist()] if count else None))
        if {p['name'].lower() for p in phases} != {'foam', 'spray', 'bubbles'}:
            raise ValueError('Missing enabled phase system')
        rows.append(dict(frame=frame, phases=phases))
        print('EDDY_PHASE_FRAME', json.dumps(rows[-1]), flush=True)
    if any(digest(Path(path)) != value for path, value in hashes.items()):
        raise ValueError('Native evidence changed during phase readback')
    with args.output.open('x') as stream:
        json.dump(dict(complete=True, accepted=False, frames=rows, originals_unchanged=True,
            original_file_sha256=hashes,
            scope='Native secondary API locations/size/velocity and interpolated cached level-set classification. API sizes are display metadata, not measured bubble radii; raw API speed has no independent secondary free-fall calibration. Interpolated phi is not exact mesh distance/contact. Unsupported samples remain missing. No persistent IDs, closed eddy circulation, phase coupling, generation/optical calibration or hydraulic acceptance.'), stream, indent=2)


if __name__ == '__main__':
    main()
