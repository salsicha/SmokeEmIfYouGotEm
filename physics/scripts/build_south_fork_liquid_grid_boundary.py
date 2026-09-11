"""Native face flux to discrete FLIP ghost-cell normal velocities (review only)."""
from pathlib import Path
import hashlib
import json
import argparse
import numpy as np
from build_south_fork_liquid_window import boundary_profiles
from south_fork_registered_mesh import RegisteredMeshSampler
from liquid_domain import layout

ROOT = Path(__file__).resolve().parents[2]
DRY_FACE_NOISE_M3S = 1e-7


def remap_flux(values, count):
    """Conservative overlap of uniform piecewise-constant face fluxes."""
    values = np.asarray(values, dtype=float)
    if values.ndim != 1 or not len(values) or not np.isfinite(values).all() or count < 1:
        raise ValueError('Finite nonempty flux vector and positive count required')
    old = np.linspace(0, 1, len(values)+1)
    new = np.linspace(0, 1, count+1)
    overlap = np.maximum(0, np.minimum(new[1:, None], old[None, 1:])-
                         np.maximum(new[:-1, None], old[None, :-1]))
    return overlap @ (values*len(values))


def remap_wet_flux(values, areas, unresolved_tolerance=0.):
    """Preserve each native face total using only overlapping resolved wet area."""
    values, areas = np.asarray(values, dtype=float), np.asarray(areas, dtype=float)
    if values.ndim != 1 or areas.ndim != 1 or not len(values) or not len(areas) or not np.isfinite(values).all() or not np.isfinite(areas).all() or (areas < 0).any() or not np.isfinite(unresolved_tolerance) or unresolved_tolerance < 0:
        raise ValueError('Finite flux and nonnegative wet areas required')
    old, new = np.linspace(0, 1, len(values)+1), np.linspace(0, 1, len(areas)+1)
    overlap = np.maximum(0, np.minimum(new[1:, None], old[None, 1:])-
                         np.maximum(new[:-1, None], old[None, :-1]))
    support = overlap*areas[:, None]
    totals = support.sum(axis=0)
    if np.any((totals == 0) & (abs(values) > unresolved_tolerance)):
        missing = np.flatnonzero((totals == 0) & (abs(values) > unresolved_tolerance))
        raise ValueError(f'Native face flux has no overlapping resolved wet support: {missing.tolist()}, flux={values[missing].tolist()}')
    shares = np.divide(support, totals, out=np.zeros_like(support), where=totals > 0)
    return shares@values


def remap_boundary_flux(values, areas):
    """Never drop inflow; retain the existing outgoing dry-noise allowance.

    Outgoing stage is an open-pressure boundary, not an injected velocity.
    The caller records every unresolved signed outgoing residual explicitly.
    """
    values=np.asarray(values,dtype=float)
    return (remap_wet_flux(np.maximum(values,0),areas)+
            remap_wet_flux(np.minimum(values,0),areas,DRY_FACE_NOISE_M3S))


def vector_boundary_velocity(momentum, depth, inward_speed, face_index):
    """Native depth-averaged tangent plus the conservative discrete normal flux.

    Values are local station/lateral m/s, not world-space vectors. This preserves
    normal discharge; the interpolated tangent is not a momentum-flux solve.
    """
    momentum, depth, inward_speed = (np.asarray(a, dtype=float) for a in (momentum, depth, inward_speed))
    if face_index not in range(4) or depth.ndim != 1 or momentum.shape != (len(depth), 2) or inward_speed.shape != depth.shape:
        raise ValueError('Four faces and matching native momentum/depth/speed required')
    if not all(np.isfinite(a).all() for a in (momentum, depth, inward_speed)) or (depth < 0).any():
        raise ValueError('Finite native values and nonnegative depth required')
    if np.any((depth <= 1e-9) & (np.linalg.norm(momentum, axis=1) > 1e-9)):
        raise ValueError('Dry native sample carries momentum')
    result = np.zeros((len(depth), 3))
    result[:, :2] = np.divide(momentum, depth[:, None], out=np.zeros_like(momentum), where=depth[:, None] > 1e-9)
    axis, sign = (0, 1) if face_index == 0 else (0, -1) if face_index == 1 else (1, 1) if face_index == 2 else (1, -1)
    result[:, axis] = sign*inward_speed
    return result


def main(with_tangent=False,directory=None,audit_path=None,physical_cells=None):
    directory = Path(directory) if directory is not None else ROOT/'unreal/SourceArt/RaftSim/SouthForkLiquidWindow20260908'
    output = directory/('grid_vector_boundary_profile.json' if with_tangent else 'grid_boundary_profile.json')
    if output.exists():
        raise FileExistsError(output)
    solid = json.loads((directory/'manifest.json').read_text())
    geometry = json.loads((ROOT/solid['source_geometry_manifest']).read_text())
    mesh_path = ROOT/geometry['mesh_path']
    if hashlib.sha256(mesh_path.read_bytes()).hexdigest() != geometry['mesh_sha256']:
        raise ValueError('Registered geometry changed')
    sampler = RegisteredMeshSampler(np.load(mesh_path))
    hydraulic = ROOT/solid['source_hydraulic_directory']
    flow = json.loads((hydraulic/'manifest.json').read_text())
    registration = json.loads((hydraulic.parent/'registration.json').read_text())
    audit_path = Path(audit_path) if audit_path is not None else ROOT/'docs/reconstruction-review-2026-09-07/liquid-native-face-flux/report.json'
    audit = json.loads(audit_path.read_text())
    if not audit['passed'] or audit['source_geometry_sha256'] != geometry['mesh_sha256']:
        raise ValueError('Native audit geometry mismatch')
    if audit['source_hydraulic_manifest_sha256'] != hashlib.sha256((hydraulic/'manifest.json').read_bytes()).hexdigest():
        raise ValueError('Native audit hydraulics mismatch')
    fields = {}
    for name, record in flow['bands'][0]['arrays'].items():
        path = hydraulic/record['file']
        if hashlib.sha256(path.read_bytes()).hexdigest() != record['sha256']:
            raise ValueError('Hydraulic field changed')
        fields[name] = np.load(path)
    downstream, left = (np.asarray(registration[k]) for k in ('downstream_unit', 'left_unit'))
    domain=layout(solid,audit,physical_cells)
    legacy=domain['legacy_fixture']
    spacing=np.asarray(domain['cell_size_m']);extent=np.asarray(domain['physical_extents_m'])
    centre=np.asarray(domain['centre_station_lateral_m']);centre_en=centre[0]*downstream+centre[1]*left
    dz=spacing[2];nz=domain['physical_cells'][2]
    floor = solid['local_origin_engine_cm'][2]/100
    profiles = boundary_profiles(fields, flow['grid'], centre, extent[:2], spacing[:2],
                                 sampler, downstream, left)
    packed = ([[*downstream, 0], [*left, 0], [spacing[0]*100, 1050, floor*100], [dz*100, 64, nz]] if legacy else
              [[*downstream,0],[*left,0],[*(centre_en*100).tolist(),floor*100],
               (extent*100).tolist(),(spacing*100).tolist(),domain['physical_cells'],
               domain['computational_cells'],(np.asarray(domain['computational_extents_m'])*100).tolist()])
    reports, vector_rows, face_offsets = [], [], []
    for face_index, (name, profile) in enumerate(zip(('west', 'east', 'south', 'north'), profiles)):
        # Ghosts represent the native face, not terrain one half-cell outside
        # it. Use captured bed at the actual exchange plane.
        bed = np.asarray([p['bed_relative_datum_m'] for p in profile['samples']])
        stage = np.asarray([p['stage_relative_datum_m'] for p in profile['samples']])
        face_step=profile['sample_width_m']
        z = floor+(np.arange(nz)+.5)*dz
        wet = (z[None, :] > bed[:, None]) & (z[None, :] < stage[:, None])
        if not legacy:
            wet &= np.asarray([p['source_depth_m'] for p in profile['samples']])[:,None]>0
        area = wet.sum(axis=1)*face_step*dz
        try:
            # Below one float32 epsilon of 1 m3/s. Report the residual, never
            # silently invent a wet cell for this numerical dry-face noise.
            q = (remap_wet_flux(audit['face_discharge_m3_per_s'][name], area, DRY_FACE_NOISE_M3S) if legacy else
                 remap_boundary_flux(audit['face_discharge_m3_per_s'][name],area))
        except ValueError as exc:
            raise ValueError(f'{name}: {exc}') from exc
        if np.any((area == 0) & (abs(q) > 1e-10)):
            raise ValueError(f'{name}: native flux lacks a resolved wet ghost cell')
        speed = np.divide(q, area, out=np.zeros_like(q), where=area > 0)
        face_offsets.append(len(packed))
        packed.extend(np.column_stack((bed*100, stage*100, speed*100)).tolist())
        if with_tangent:
            velocity = vector_boundary_velocity([p['momentum_m2_per_s'] for p in profile['samples']],
                [p['source_depth_m'] for p in profile['samples']], speed, face_index)
            vector_rows.extend((velocity*100).tolist())
        reports.append(dict(face=name, inward_flux_m3s=q.tolist(), wet_area_m2=area.tolist(),
                            unresolved_native_flux_m3s=float(sum(audit['face_discharge_m3_per_s'][name])-q.sum()),
                            reconstructed_flux_m3s=(speed*area).tolist(),
                            max_abs_velocity_mps=float(abs(speed).max())))
    if with_tangent:
        baseline = json.loads((directory/'grid_boundary_profile.json').read_text())
        if not np.array_equal(np.asarray(packed), np.asarray(baseline['packed_vectors'])):
            raise ValueError('Vector candidate changed the existing bed/stage/normal-flux profile')
        packed.extend(vector_rows)
    vector_offset=len(packed)-len(vector_rows) if with_tangent else None
    report = dict(schema=('raftsim.liquid_grid_boundary.v2' if with_tangent else 'raftsim.liquid_grid_boundary.v1') if legacy else 'raftsim.liquid_grid_boundary.v3', packed_vectors=packed,
                  source_geometry_sha256=geometry['mesh_sha256'],
                  native_flux_report_sha256=hashlib.sha256(audit_path.read_bytes()).hexdigest(),
                  faces=reports, computational_cells=domain['computational_cells'],
                  computational_extents_cm=(np.asarray(domain['computational_extents_m'])*100).tolist(),
                  physical_extents_cm=(extent*100).tolist(),domain=domain,
                  boundary_type='prescribed normal flux at wet ghost cells; not outgoing pressure-stage coupling',
                  submerged_bed_inferred=True, engine_flux_verified=False, production_promoted=False)
    if with_tangent:
        report.update(vector_rows_offset=vector_offset, vector_frame='local station/lateral/up cm/s',
            vector_boundary_applies_to_inflow_only=True,
            tangent_method='native bilinearly interpolated momentum / interpolated depth',
            tangential_momentum_flux_conserved=False,
            baseline_profile_sha256=hashlib.sha256((directory/'grid_boundary_profile.json').read_bytes()).hexdigest())
    if not legacy:
        report.update(face_rows_offsets=face_offsets,face_row_counts=[len(p['samples']) for p in profiles],
                      header_layout=['source_axis_x','source_axis_y','source_world_bottom_origin_cm',
                                     'physical_extents_cm','cell_size_cm','physical_cells','computational_cells','computational_extents_cm'],
                      runtime_support_verified=False,
                      unresolved_outgoing_noise_allowance_m3s=DRY_FACE_NOISE_M3S,
                      inflow_unresolved_tolerance_m3s=0.)
    output.write_text(json.dumps(report, separators=(',', ':'))+'\n')
    print(json.dumps(dict(path=str(output), faces=[dict(face=f['face'], flux=sum(f['inward_flux_m3s']),
                    max_speed=f['max_abs_velocity_mps']) for f in reports]), indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--with-tangent', action='store_true')
    parser.add_argument('--directory',type=Path);parser.add_argument('--audit',type=Path)
    parser.add_argument('--physical-cells',type=int,nargs=2)
    args=parser.parse_args();main(args.with_tangent,args.directory,args.audit,args.physical_cells)
