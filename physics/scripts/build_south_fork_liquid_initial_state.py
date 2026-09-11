"""Seed the registered review's existing wet volume, not an empty flat tank.

Equal nominal-volume particles are apportioned deterministically among wet
columns. This is a quadrature of an existing numerical field, not new measured
bathymetry, a new solve, or a calibration of Niagara particle volume.
"""
import hashlib
import json
from pathlib import Path
import numpy as np
from build_south_fork_liquid_window import bilinear
from south_fork_registered_mesh import RegisteredMeshSampler

ROOT = Path(__file__).resolve().parents[2]


def resolved_wet_depth(stage, exact_bed, native_depth):
    stage,exact_bed,native_depth=(np.asarray(v,dtype=float) for v in (stage,exact_bed,native_depth))
    if stage.shape!=exact_bed.shape or stage.shape!=native_depth.shape or not all(np.isfinite(v).all() for v in (stage,exact_bed,native_depth)) or (native_depth<0).any():
        raise ValueError('Matching finite stage/bed and nonnegative native depth required')
    # eta=bed+h on a dry solver cell is TERRAIN elevation, not a free surface.
    # Different triangle/raster interpolation there cannot create liquid.
    return np.where(native_depth>0,np.maximum(stage-exact_bed,0),0.)


def apportion_columns(volumes, particle_volume):
    volumes = np.asarray(volumes, dtype=float)
    if not np.isfinite(volumes).all() or (volumes < 0).any() or not np.isfinite(particle_volume) or particle_volume <= 0:
        raise ValueError('Finite nonnegative volumes and positive particle volume required')
    target = int(np.floor(volumes.sum()/particle_volume + .5))
    ideal = volumes/particle_volume
    counts = np.floor(ideal).astype(np.int64)
    remainder = target-int(counts.sum())
    order = np.argsort(-(ideal-counts), kind='stable')
    counts[order[:remainder]] += 1
    if counts.sum() != target or np.any(counts[volumes == 0]):
        raise ValueError('Invalid deterministic volume apportionment')
    return counts


def main(directory=None):
    directory = Path(directory) if directory is not None else ROOT/'unreal/SourceArt/RaftSim/SouthForkLiquidWindow20260908'
    output = directory/'hydraulic_initial_state.json'
    if output.exists():
        raise FileExistsError('Retain the previous initial-state evidence')
    window = json.loads((directory/'manifest.json').read_text())
    geometry = json.loads((ROOT/window['source_geometry_manifest']).read_text())
    mesh_path = ROOT/geometry['mesh_path']
    sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    if sha(mesh_path) != window['source_geometry_sha256']:
        raise ValueError('Registered mesh identity changed')
    hydraulic = ROOT/window['source_hydraulic_directory']
    if sha(hydraulic/'manifest.json') != window['source_hydraulic_manifest_sha256']:
        raise ValueError('Hydraulic identity changed')
    flow = json.loads((hydraulic/'manifest.json').read_text())
    coordinate = json.loads((hydraulic/'coordinate_map.json').read_text())
    if coordinate['vertical_datum_m'] != geometry['vertical_origin_navd88_m']:
        raise ValueError('Vertical datum mismatch')
    registration = json.loads((hydraulic.parent/'registration.json').read_text())
    rotation = np.column_stack([registration['downstream_unit'], registration['left_unit']])
    if not np.allclose(rotation.T@rotation, np.eye(2), atol=1e-9) or np.linalg.det(rotation) < 0:
        raise ValueError('Rigid right-handed source frame required')
    sampler = RegisteredMeshSampler(np.load(mesh_path))
    fields = {}
    for name, record in flow['bands'][0]['arrays'].items():
        path = hydraulic/record['file']
        if sha(path) != record['sha256']:
            raise ValueError('Hydraulic array changed: '+name)
        fields[name] = np.load(path)
    # Same nominal particle volume as the conservative face-source profile.
    source_path = directory/'native_source_profile.json'
    source = json.loads(source_path.read_text())
    domain=source.get('domain')
    if domain and not domain['legacy_fixture']:
        from liquid_domain import layout
        audit=json.loads((ROOT/window['native_flux_audit_path']).read_text())
        expected=layout(window,audit,domain['physical_cells'][:2],domain['physical_cells'][2])
        if domain!=expected:
            raise ValueError('Source domain disagrees with window/native audit')
        particle_volume=domain['nominal_particle_volume_m3']
        extent=np.asarray(domain['physical_extents_m'][:2])
        centre=np.asarray(domain['centre_station_lateral_m'])
        column_counts=2*np.asarray(domain['physical_cells'][:2])
    else:
        particle_volume=(21/64)**3/4
        extent=np.array([21.,21.]);centre=np.zeros(2);column_counts=np.array([128,128])
    if source['source_geometry_sha256'] != window['source_geometry_sha256'] or not np.isclose(source['nominal_particle_volume_m3'], particle_volume, atol=1e-12, rtol=0):
        raise ValueError('Inlet and initial-volume particle conventions disagree')
    interval=extent/column_counts
    axes=[(np.arange(count)+.5)*step-length/2 for count,step,length in zip(column_counts,interval,extent)]
    x,y=np.meshgrid(*axes)
    sl = np.column_stack((x.ravel(), y.ravel()))+centre
    en = sl@rotation.T
    explicit_float_positions=bool(domain and not domain['legacy_fixture'])
    if explicit_float_positions:
        # These are quadrature sites, not captured terrain vertices. Evaluate
        # the column at the position the float32 GPU will actually receive,
        # rather than validating a nearby double site on a steep rock face.
        en=(en*100).astype(np.float32).astype(float)/100
        sl=en@rotation
    bed = sampler.sample(en[:, 0], en[:, 1])
    h, u, v, coarse_bed = (fields[k] for k in ('h', 'u', 'v', 'bed'))
    stage = bilinear(coarse_bed+h, sl[:, 0], sl[:, 1], flow['grid'])
    source_depth = bilinear(h, sl[:, 0], sl[:, 1], flow['grid'])
    depth = resolved_wet_depth(stage,bed,source_depth)
    momentum = np.column_stack([bilinear(h*u, sl[:, 0], sl[:, 1], flow['grid']),
                                bilinear(h*v, sl[:, 0], sl[:, 1], flow['grid'])])
    velocity = np.divide(momentum, source_depth[:, None], out=np.zeros_like(momentum),
                         where=source_depth[:, None] > 1e-9)@rotation.T
    volumes = depth*float(np.prod(interval))
    counts = apportion_columns(volumes, particle_volume)
    if counts.sum()>5000000:
        raise ValueError('Prepared state exceeds five-million-particle export safety bound; choose an explicit bounded layout')
    columns = np.repeat(np.arange(len(counts)), counts)
    offsets = np.repeat(np.cumsum(counts)-counts, counts)
    fractions = (np.arange(len(columns))-offsets+.5)/counts[columns]
    z = bed[columns]+depth[columns]*fractions
    positions = np.column_stack((en[columns], z))*100
    if explicit_float_positions:
        positions=positions.astype(np.float32).astype(float)
        z=positions[:,2]/100
    velocities = np.column_stack((velocity[columns], np.zeros(len(columns))))*100
    floor = window['local_origin_engine_cm'][2]/100
    if not len(columns) or not np.isfinite(positions).all() or not np.isfinite(velocities).all():
        raise ValueError('Empty or nonfinite wet-state samples')
    if np.any(z <= bed[columns]) or np.any(z >= stage[columns]) or np.any(z <= floor) or np.any(z >= floor+8):
        invalid=(z<=bed[columns])|(z>=stage[columns])|(z<=floor)|(z>=floor+8)
        examples=[dict(station_lateral=sl[columns[i]].tolist(),z=float(z[i]),bed=float(bed[columns[i]]),
                       stage=float(stage[columns[i]]),native_depth=float(source_depth[columns[i]]))
                  for i in np.flatnonzero(invalid)[:5]]
        raise ValueError(f'Wet-state sample outside actual column/domain: count={int(invalid.sum())}, floor={floor}, examples={examples}')
    report = {
        'schema': 'raftsim.registered_liquid_initial_state.v2' if domain and not domain['legacy_fixture'] else 'raftsim.registered_liquid_initial_state.v1',
        'source_geometry_sha256': window['source_geometry_sha256'],
        'source_hydraulic_manifest_sha256': window['source_hydraulic_manifest_sha256'],
        'native_source_profile_sha256': sha(source_path),
        'registered_rapid_identity_verified': False,
        'submerged_bed_authority': window['submerged_bed_authority'],
        'production_promoted': False, 'engine_particle_volume_calibrated': False,
        'positions_world_cm': positions.tolist(), 'velocities_world_cm_per_s': velocities.tolist(),
        'particle_count': len(columns), 'nominal_particle_volume_m3': particle_volume,
        'column_interval_m': float(interval[0]) if interval[0]==interval[1] else interval.tolist(),
        'column_counts_xy':column_counts.tolist(),
        'domain':domain,'column_quadrature_wet_volume_m3': float(volumes.sum()),
        'position_encoding':'explicit-float32-world-centimetres' if explicit_float_positions else 'legacy-double-quadrature-sites',
        'represented_nominal_volume_m3': float(len(columns)*particle_volume),
        'volume_quantization_error_m3': float(len(columns)*particle_volume-volumes.sum()),
        'minimum_exact_bed_clearance_m': float(np.min(z-bed[columns])),
        'vertical_velocity_authority': 'Zero: the source field is depth-averaged 2D, not measured 3D velocity',
        'columns_with_subparticle_wet_volume_omitted': int(np.sum((depth > 0)&(counts == 0))),
        'dry_native_columns_excluded':int(np.sum((source_depth==0)&(stage>bed))),
        'dry_terrain_interpolation_false_volume_excluded_m3':float(np.sum(np.where(source_depth==0,np.maximum(stage-bed,0),0))*np.prod(interval)),
    }
    with output.open('x') as stream:
        json.dump(report, stream, separators=(',', ':'))
    print({k: report[k] for k in ('particle_count', 'column_quadrature_wet_volume_m3',
                                 'represented_nominal_volume_m3', 'volume_quantization_error_m3',
                                 'minimum_exact_bed_clearance_m')})


if __name__ == '__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--directory',type=Path)
    main(parser.parse_args().directory)
