"""Prepare explicit initial interfaces from the actual South Fork wet-stage prior.

The scalar is z-stage in native centimetres, not signed distance. Exact terrain
remains a separate solid constraint. No density threshold, extra water plane,
source-height calibration, particle movement, or runtime promotion is performed.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from liquid_dataset import resolve, ROOT
from build_south_fork_liquid_window import bilinear
from south_fork_registered_mesh import RegisteredMeshSampler
from liquid_volume_interface import sample_centred


def prepare(key, output):
    output = Path(output)
    if output.exists():
        raise FileExistsError(output)
    dataset = resolve(key=key)
    sha = lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    window = json.loads((dataset['parent']/'manifest.json').read_text())
    if sha(dataset['mesh']) != window['source_geometry_sha256']:
        raise ValueError('Registered terrain changed')
    hydraulic = ROOT/window['source_hydraulic_directory']
    if sha(hydraulic/'manifest.json') != window['source_hydraulic_manifest_sha256']:
        raise ValueError('Hydraulic stage source changed')
    flow = json.loads((hydraulic/'manifest.json').read_text())
    registration = json.loads((hydraulic.parent/'registration.json').read_text())
    rotation = np.column_stack((registration['downstream_unit'], registration['left_unit']))
    if not np.allclose(rotation.T@rotation, np.eye(2), atol=1e-9, rtol=0) or np.linalg.det(rotation)<0:
        raise ValueError('Right-handed source registration required')
    arrays = {}
    for name in ('h', 'bed'):
        record = flow['bands'][0]['arrays'][name]
        path = hydraulic/record['file']
        if sha(path) != record['sha256']:
            raise ValueError('Hydraulic array changed: '+name)
        arrays[name] = np.load(path)
    with np.load(dataset['mesh']) as mesh:
        sampler = RegisteredMeshSampler(mesh)
    output.mkdir(parents=True)
    records = []
    for i in range(12):
        region_path = dataset['regions']/f'region-{i:03d}.json'
        r = json.loads(region_path.read_text())
        cells = np.asarray(r['computational_cells'])
        extent = np.asarray(r['computational_extents_m'])*100
        spacing = extent/cells
        ax, ay = np.asarray(r['axis_x_canonical']), np.asarray(r['axis_y_canonical'])
        if not np.allclose(np.column_stack((ax, ay)), rotation, atol=1e-9, rtol=0):
            raise ValueError('Region and hydraulic source registration disagree')
        origin = np.asarray(r['origin_canonical_cm'])
        # Native grid Y reverses canonical left, then world Y reflects north.
        x, y = np.meshgrid((np.arange(cells[0])+.5)*spacing[0]-extent[0]/2,
                           (np.arange(cells[1])+.5)*spacing[1]-extent[1]/2)
        en = (origin[:2]+x[..., None]*ax-y[..., None]*ay)/100
        sl = en@rotation
        stage = bilinear(arrays['bed']+arrays['h'], sl[..., 0], sl[..., 1], flow['grid'])
        depth = bilinear(arrays['h'], sl[..., 0], sl[..., 1], flow['grid'])
        bed = sampler.sample(en[..., 0], en[..., 1])
        # Dry source eta=bed is not water above a differently interpolated
        # exact triangle. Its zero set stays at/below the actual solid.
        stage = np.where(depth>0, stage, np.minimum(stage, bed))
        z = origin[2]+(np.arange(cells[2])+.5)*spacing[2]
        phi = (z[:, None, None]-stage[None, ...]*100).astype('<f4')
        p = np.asarray(r['positions_canonical_cm'], dtype='<f4').reshape(-1, 3).astype(float)
        delta = p-origin
        local = np.column_stack((delta[:, :2]@ax+extent[0]/2, -delta[:, :2]@ay+extent[1]/2, delta[:, 2]))
        sampled, valid = sample_centred(phi, local, spacing)
        path = output/f'interface-{i:03d}.r32f'
        phi.tofile(path)
        records.append(dict(region_id=i, cells=cells.tolist(), spacing_cm=spacing.tolist(),
                            initial_phi=path.name, initial_phi_sha256=sha(path), source_region_sha256=sha(region_path),
                            scalar_range_cm=[float(phi.min()), float(phi.max())], particle_count=len(p),
                            invalid_particle_stencils=int((~valid).sum()), particles_above_sampled_interface=int((valid & (sampled>0)).sum()),
                            maximum_particle_above_interface_cm=float(sampled[valid].max(initial=0))))
    report = dict(schema='raftsim.initial_liquid_interface.v1', native_dataset=key, regions=records,
                  source_geometry_sha256=window['source_geometry_sha256'],
                  source_hydraulic_manifest_sha256=window['source_hydraulic_manifest_sha256'],
                  ownership_manifest_sha256=sha(dataset['regions']/'manifest.json'),
                  particle_count=sum(r['particle_count'] for r in records),
                  particles_above_sampled_interface=sum(r['particles_above_sampled_interface'] for r in records),
                  invalid_particle_stencils=sum(r['invalid_particle_stencils'] for r in records),
                  scalar_units='centimetres', scalar_is_signed_distance=False,
                  physical_liquid='negative scalar intersected with space above the exact registered solid',
                  source_authority='Existing uncalibrated hydraulic prior; not new surveyed bathymetry',
                  runtime_installed=False, physical_visual_or_performance_acceptance=False)
    (output/'manifest.json').write_text(json.dumps(report, indent=2, allow_nan=False)+'\n')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dataset', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = prepare(args.dataset, args.output)
    print(json.dumps({k:v for k,v in result.items() if k!='regions'}, indent=2))
