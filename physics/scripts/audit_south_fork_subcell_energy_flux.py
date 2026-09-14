"""Actual-source instantaneous joint mass/pressure audit; not evolved gameplay."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import numpy as np
from south_fork_registered_mesh import RegisteredMeshSampler
from subcell_geometry_patch import SubcellGeometryPatch
from subcell_energy_flux import rates

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'unreal/Scripts'))
from audit_carrier_source_epochs import exact_cells


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--atlas', required=True, type=Path)
    p.add_argument('--report', required=True, type=Path)
    a = p.parse_args()
    if a.report.exists():
        raise FileExistsError(a.report)
    base = ROOT/'physics/data/real_world/south_fork_american_chili_bar/reconstruction_2026_09/full_reach'
    geometry_path = base/'composite_terrain/manifest.json'
    coordinate_path = base/'hydraulic_regions_context/coordinate_map.json'
    mesh_path = base/'composite_terrain/troublemaker_registered_source.npz'
    geometry, coordinates, atlas = read(geometry_path), read(coordinate_path), read(a.atlas)
    if (sha(mesh_path) != geometry['registered_rapid_sha256'] or
            atlas['schema'] != 'raftsim.cartesian_state_atlas.v1' or atlas['grid_spacing_m'] != 1. or
            atlas['source_elevation_datum_m'] != coordinates['vertical_datum_m']):
        raise ValueError('Changed registered source or unsupported atlas grid/datum')
    yy, xx = np.indices((16, 16))
    offsets = np.stack((xx.ravel(), yy.ravel()), 1)
    cells = exact_cells(np.array([-5439., 3593.])+offsets,
                        [tile['origin_m'] for tile in atlas['tiles']], atlas['tile_shape'], 1.)
    if (cells < 0).any():
        raise ValueError('Missing captured cell')
    origin = np.array([tile['origin_m'] for tile in atlas['tiles']])[cells[:, 0]]+cells[:, [2, 1]]
    if not np.array_equal(origin, origin[0]+offsets):
        raise ValueError('Not the original regular cell lattice')
    paths = [a.atlas, geometry_path, coordinate_path, mesh_path, Path(__file__)]
    paths += [ROOT/'physics/scripts'/name for name in ('subcell_energy_flux.py', 'triangle_cell_storage.py',
              'triangle_face_section.py', 'subcell_geometry_patch.py', 'south_fork_registered_mesh.py')]
    hashes = {str(path.resolve()): sha(path) for path in paths}
    fields = {}
    for key in ('bed', 'h', 'u', 'v'):
        record = atlas['arrays'][key]
        path = (a.atlas.parent/record['file']).resolve()
        if sha(path) != record['sha256']:
            raise ValueError('Changed source array '+key)
        values = np.load(path, mmap_mode='r', allow_pickle=False)
        if list(values.shape) != record['shape'] or values.dtype != np.dtype('<f8') or not np.isfinite(values).all():
            raise ValueError('Malformed source array '+key)
        tile, row, col = cells.T
        fields[key] = np.array(values[tile*atlas['tile_shape'][0]+row, col]).reshape(16, 16)
        hashes[str(path)] = record['sha256']
    with np.load(mesh_path, allow_pickle=False) as mesh:
        terrain = RegisteredMeshSampler(mesh)
    shift = np.array(coordinates['world_origin_utm_m'])-geometry['rapid_origin_utm_m']
    patch = SubcellGeometryPatch(terrain, origin[0]+shift, (16, 16), relative_stages=True)
    source_bed = fields['bed']+atlas['source_elevation_datum_m']-geometry['rapid_datum_navd88_m']
    exact_bed = terrain.sample(*(origin+shift).T).reshape(16, 16)
    if not np.allclose(source_bed, exact_bed, atol=1e-9, rtol=0):
        raise ValueError('Hydraulic and captured cell centers differ')
    controls = []
    for stage in (6.5, 7.5, 8.5, 10.):
        volume, momentum = patch.state_from_stages(stage)
        for stable in (False, True):
            r = rates(patch, volume, momentum, dissipative=stable)
            maximum = float(abs(r['momentum_rate']).max())
            if abs(r['volume_rate']).max() > 1e-11 or maximum > 1e-10:
                raise ValueError('Real-geometry lake at rest failed')
            controls.append(dict(stage_m=stage, dissipative=stable, wet_cells=int((volume > 0).sum()),
                maximum_volume_rate=float(abs(r['volume_rate']).max()), maximum_momentum_rate=maximum))
    volume = fields['h'].copy()  # Cell area is exactly 1 m2: preserve original volume.
    momentum = volume[..., None]*np.stack((fields['u'], fields['v']), axis=-1)
    cases = []
    for stable in (False, True):
        r = rates(patch, volume, momentum, dissipative=stable)
        mass_error = abs(float(r['volume_rate'].sum()))
        if r['energy_identity_error'] > 1e-9 or mass_error > 1e-10 or r['energy_rate'] > 1e-9:
            raise ValueError('Actual-source mass/energy identity failed')
        cases.append(dict(dissipative=stable, energy_rate=r['energy_rate'],
            expected_energy_rate=r['expected_energy_rate'], energy_identity_error=r['energy_identity_error'],
            volume_rate_sum=float(r['volume_rate'].sum()),
            maximum_volume_rate=float(abs(r['volume_rate']).max()),
            maximum_momentum_rate=float(abs(r['momentum_rate']).max())))
    for path, expected in hashes.items():
        if sha(Path(path)) != expected:
            raise ValueError('Protected source changed during audit')
    result = dict(schema='raftsim.south_fork.subcell_energy_flux.v1', accepted=False,
        instantaneous_mass_pressure_identity_passed=True, cells=256, faces=len(patch.faces),
        original_atlas_time_seconds=atlas['source_time_seconds'], source_origin_m=origin[0].tolist(),
        source_center_error_m=float(abs(source_bed-exact_bed).max()), initial_volume_m3=float(volume.sum()),
        lake_controls=controls, actual_state_cases=cases, source_sha256=hashes,
        scope='Original registered triangles and original atlas volumes/momenta. Closed reflecting patch, '
              'instantaneous nondispersive energy only. No new time history, positivity timestep, two-pole '
              'coupling, internal-basin connectivity, open-river boundary, native budget, material, gameplay '
              'or scene acceptance. Original dry/pressure/energy gates remain unchanged.')
    with a.report.open('x', encoding='utf-8') as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
    print(json.dumps({k: v for k, v in result.items() if k != 'source_sha256'}, indent=2))


if __name__ == '__main__':
    main()
