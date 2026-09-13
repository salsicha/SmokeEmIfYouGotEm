"""Replay selected-step native South Fork particle transport, not stale P2G outputs.

Captures must include the velocity AFTER extrapolation and particles AFTER
FLIP/PIC, BEFORE ownership changes. Derivatives describe instantaneous local
compression; they are not integrated volume loss or physical acceptance.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from audit_liquid_native_interface import audit as audit_interface
from audit_liquid_native_handoff import read
from audit_liquid_affine_transfer import shader_text
from diagnose_liquid_projection_packet import load_field
from liquid_affine_transfer import stencil, to_particles
from liquid_compatible_advection import sample_compact
from liquid_compatible_projection import divergence
from liquid_volume_interface import sample_centred
from liquid_dataset import resolve
from south_fork_registered_mesh import RegisteredMeshSampler


QUANTILES = [0, .01, .1, .5, .9, .99, 1]


def stats(a):
    a = np.asarray(a)
    if not a.size:
        return dict(count=0)
    if not np.isfinite(a).all():
        raise ValueError('Nonfinite diagnostic values')
    return dict(count=int(a.size), rms=float(np.sqrt(np.mean(a*a))),
                mean=float(a.mean()), quantiles=np.quantile(a, QUANTILES).tolist())


def pair_order(before, after):
    """Use the full four-word native identity, reject loss/addition/duplicates."""
    before, after = np.asarray(before), np.asarray(after)
    if before.shape != after.shape or before.ndim != 2 or before.shape[1] != 4:
        raise ValueError('Matching full native identities required')
    b = np.lexsort(before.T[::-1]); a = np.lexsort(after.T[::-1])
    if (not np.array_equal(before[b], after[a]) or
            (len(b)>1 and np.any(np.all(before[b][1:] == before[b][:-1], axis=1)))):
        raise ValueError('Native advection changed or duplicated identities')
    order = np.empty(len(a), int); order[b] = a
    return order


def validate_transport_sources(directory):
    """Require the actual launch's include snapshots, not today's worktree."""
    manifest=json.loads((directory/'transport-sources.json').read_text())
    capture=json.loads((directory/'capture.json').read_text())
    expected={'RaftSimLiquidCompactTransport.ush','RaftSimLiquidPhysicalFrame.ush','RaftSimLiquidInterface.usf'}
    if (manifest.get('schema')!='raftsim.liquid_transport_sources.v1' or
            set(manifest.get('files_sha256',{}))!=expected or not capture.get('transport_sources_unchanged')):
        raise ValueError('Immutable native transport include snapshots required')
    result={}
    for name,digest in manifest['files_sha256'].items():
        data=(directory/name).read_bytes()
        if hashlib.sha256(data).hexdigest()!=digest:raise ValueError('Changed native transport include snapshot')
        result[name]=digest
    source=(directory/'RaftSimLiquidCompactTransport.ush').read_text()
    if 'DFDemote(DFDivide(Numerator,Denominator))' not in source:
        raise ValueError('This replay requires residual-preserving native coordinates; use the earlier reference for older experiments')
    return result


def replay(points, velocity, grid_zyx, types, spacing, axes, origin, dt, native_matrices=None, compact=False, unit_to_world=None):
    """Stock native Euler position branch; preserve ballistic solids/air.

    Native nearest classification is round(unit*size-.5). No boundary clamping
    is introduced. The caller separately retains unsupported samples.
    """
    h = np.asarray(spacing, float); cells = np.array(types.shape[::-1])
    local = (points-origin)@axes.T+cells*h*[.5,.5,0]
    vector_axes = axes
    if native_matrices is not None:
        world_to_unit, local_to_world = (np.asarray(m,dtype='<f4').reshape(4,4) for m in native_matrices)
        if not np.isfinite(world_to_unit).all() or not np.isfinite(local_to_world).all():
            raise ValueError('Finite captured native matrices required')
        homogeneous = np.column_stack((points,np.ones(len(points)))).astype('<f4')
        frame=None if unit_to_world is None else np.asarray(unit_to_world,dtype='<f4').reshape(4,4)
        def query_unit(p):
            if frame is None:
                return (np.column_stack((p,np.ones(len(p),dtype='<f4'))).astype('<f4')@world_to_unit)[:,:3]
            # Shared shader retains DoubleFloat residuals then demotes once.
            # Use the exact captured float inputs, not an idealized survey frame.
            offset=p.astype('<f4').astype(float)-frame[3,:3].astype(float)
            products=offset[:,None,:]*frame[None,:3,:3].astype(float)
            squares=frame[:3,:3].astype(float)**2
            numerator=(products[:,:,0]+products[:,:,1])+products[:,:,2]
            denominator=(squares[:,0]+squares[:,1])+squares[:,2]
            return (numerator/denominator).astype('<f4')
        unit = query_unit(points)
        local = unit.astype(float)*cells*h
        vector_axes = local_to_world[:3,:3].astype(float)
    q = local/h-.5; lo = np.floor(q).astype(int)
    if native_matrices is not None:
        # The native UnitToFloatIndex multiply/subtract are float operations,
        # followed by round-to-even. Keeping double intermediates flips the
        # solid/ballistic branch for exactly representable half-cell queries.
        q = (unit*cells.astype('<f4')-np.float32(.5)).astype(float)
        lo = np.floor(q).astype(int)
    complete = ((lo>=0)&(lo+1<cells)).all(axis=1)
    nearest = np.rint(q).astype(int)
    inside = ((nearest>=0)&(nearest<cells)).all(axis=1)
    phase = np.full(len(points), -1)
    i = nearest[inside]; phase[inside] = np.rint(types[i[:,2],i[:,1],i[:,0]]).astype(int)
    grid_mode = complete & inside & np.isin(phase, [0,3])
    expected = points+dt*velocity
    derivative = np.full((len(points),3,3), np.nan)
    all_fluid = np.zeros(len(points), bool)
    if grid_mode.any():
        p = local[grid_mode]
        sampled,j = to_particles(p, grid_zyx.transpose(2,1,0,3), h)
        expected[grid_mode] = points[grid_mode]+dt*(sampled@vector_axes)
        derivative[grid_mode] = j
        fluid = np.ones(len(p), bool)
        for i,w,g,o in stencil(p,cells,h):
            fluid &= types[i[:,2],i[:,1],i[:,0]] == 0
        all_fluid[grid_mode] = fluid
    # Compare against exactly the projection audit's owned [2, size-2) box.
    # Both corners must be pressure-interior cells, not XY duplicate halos or
    # the provisional two Z-edge layers. Other particles remain in replay and
    # all-grid divergence statistics, not silently dropped from acceptance.
    pressure_interior = all_fluid & ((lo>=2)&(lo+3<cells)).all(axis=1)
    if compact:
        if native_matrices is None:
            raise ValueError('Compact native replay requires actual matrices')
        if unit_to_world is not None:
            # Unsupported/solid/air positions retain the original native motion
            # branch, whose inverse matrix was not changed by this experiment.
            expected=replay(points,velocity,grid_zyx,types,spacing,axes,origin,dt,native_matrices)[0]
        indices=np.flatnonzero(grid_mode & ((lo-1>=0)&(lo+2<cells)).all(axis=1))
        local_start=(q[indices]+.5)*h
        first,first_j=sample_compact(local_start,grid_zyx.transpose(2,1,0,3),h,True)
        middle=(points[indices]+.5*dt*(first@vector_axes)).astype('<f4')
        mid_unit=query_unit(middle)
        mid_q=(mid_unit*cells.astype('<f4')-np.float32(.5)).astype(float)
        mid_lo=np.floor(mid_q).astype(int)-1
        supported=((mid_lo>=0)&(mid_lo+3<cells)).all(axis=1)
        second=sample_compact((mid_q[supported]+.5)*h,grid_zyx.transpose(2,1,0,3),h)
        selected=indices[supported]
        expected[selected]=points[selected]+dt*(second@vector_axes)
        derivative[selected]=first_j[supported]
        # This is the instantaneous start derivative, not the full RK2-map
        # determinant or a claim of exact finite-time volume preservation.
        local[selected]=local_start[supported]
    return expected, grid_mode, complete, derivative, pressure_interior, local, phase


def diagnose(directory):
    directory = Path(directory).resolve()
    validation = audit_interface(directory)
    report = json.loads((directory/'stages.json').read_text())
    log_path=directory.with_suffix('.log')
    log=log_path.read_text(errors='replace')
    rhi_clean='-RHIValidation' in log and not any(s in log for s in ('LogRHI: Error','Fatal error:','GPU Crashed'))
    if not report.get('native_advection_packet_requested'):
        raise ValueError('A same-step post-advection capture is required; P2G contact outputs are stale')
    records = report['native_transfer_packet']
    compact=report.get('native_compatible_transport_requested',False)
    unified=report.get('native_unified_transport_requested',False)
    transport_sources=validate_transport_sources(directory) if unified else {}
    shader_path=directory/'region-004-native.hlsl'
    shader=shader_text(shader_path.read_bytes())
    if ('RiverCompactCompatibleTransport:' in shader)!=compact:
        raise ValueError('Captured native compiled transport differs from requested mode')
    if ('RiverUnifiedTransport:' in shader)!=unified or unified!=validation['compact_transport']:
        raise ValueError('Particle and interface unified transport modes disagree')
    if [r['region_id'] for r in records] != list(range(12)):
        raise ValueError('All twelve actual river owners required')
    with np.load(resolve(report)['mesh']) as mesh:
        sampler = RegisteredMeshSampler(mesh)
    summaries, sources = [], {p.name:hashlib.sha256(p.read_bytes()).hexdigest()
        for p in (directory/'stages.json',directory/'capture.json',shader_path,log_path)}
    errors, all_errors, traces, discrete, contact_moves = [], [], [], [], []
    for r in records:
        if (r.get('advection_native_step') != report['native_transfer_packet_step'] or
                r.get('advection_velocity_stage') != 'Extrapolate Velocities Again: after stage' or
                r.get('advection_particle_stage') != 'FLIP / PIC force: after stage, before owner handoff'):
            raise ValueError('Particle/velocity snapshot stage mismatch')
        n = r['particle_count']
        if r['advection_particle_count'] != n:
            raise ValueError('Transport changed particle count before handoff')
        ids = read(directory,r,'identities',(n,4))
        order = pair_order(ids,read(directory,r,'advection_identities',(n,4)))
        vectors = {}
        for key in ('positions','velocities','advection_raw_positions','advection_positions',
                    'advection_raw_velocities','advection_velocities'):
            a = read(directory,r,key,(n,4)).view('<f4')[:,:3].astype(float)
            vectors[key] = a[order] if key.startswith('advection_') else a
        if any(not np.isfinite(v).all() for v in vectors.values()):
            raise ValueError('Nonfinite particle state')
        grid = load_field(directory,r,'advection_velocity',4)[...,:3]
        types = load_field(directory,r,'projection_boundary',4)[...,3]
        axes = np.array([r['world_axis_x'],r['world_axis_y'],[0,0,1]])
        if not np.allclose(axes@axes.T,np.eye(3),atol=1e-9,rtol=0):
            raise ValueError('Orthonormal native coordinates required')
        h = np.asarray(r['extent_cm'])/r['cells']; dt = r['advection_engine_delta_seconds']
        if dt<=0 or dt!=report['native_interface_transport']['engine_delta_seconds'][-1]:
            raise ValueError('Matched positive actual native timestep required')
        p = vectors['positions']
        if 'advection_world_to_unit' not in r or 'advection_local_to_world' not in r:
            raise ValueError('Immutable native matrices required; idealized survey frame does not establish branch selection')
        expected,mode,complete,j,interior,local,phase = replay(p,vectors['velocities'],grid,types,h,axes,np.array(r['world_origin_cm']),dt,
            (r['advection_world_to_unit'],r['advection_local_to_world']),compact,r['advection_unit_to_world'] if unified else None)
        error = np.max(abs(expected-vectors['advection_raw_positions']),axis=1)
        contact = np.linalg.norm(vectors['advection_positions']-vectors['advection_raw_positions'],axis=1)
        tr = np.trace(j[interior],axis1=1,axis2=2)
        d,valid = sample_centred(divergence(grid,h),local[interior],h)
        if not valid.all():
            raise ValueError('Incomplete centered divergence stencil')
        errors.extend(error[mode]); traces.extend(tr); discrete.extend(d); contact_moves.extend(contact)
        all_errors.extend(error)
        total_path = (directory/r['total']).resolve()
        if total_path.parent != directory:
            raise ValueError('Total field escapes capture')
        mass = np.fromfile(total_path,dtype='<f4').reshape(*r['cells'][::-1],4)[...,3].astype(float)
        density = mass/np.prod(h/100)
        physical = np.zeros(types.shape,bool); physical[:,2:-2,2:-2] = True
        peak = np.unravel_index(np.argmax(np.where(physical,density,-1)),types.shape)
        world = ((np.array(peak[::-1])+.5)*h-np.array(r['extent_cm'])*[.5,.5,0])@axes+np.array(r['world_origin_cm'])
        nearby = np.linalg.norm(p-world,axis=1)<100
        bed,normals=sampler.sample(p[:,0]/100,-p[:,1]/100,with_normals=True)
        normals[:,1]*=-1  # canonical ENU to the actual engine world frame
        clearance = p[:,2]/100-bed
        bed_near=clearance<=.025
        raw_motion=(vectors['advection_raw_positions']-p)/dt
        motion=(vectors['advection_positions']-p)/dt
        normal_raw=np.sum(raw_motion*normals,axis=1)
        normal_after=np.sum(motion*normals,axis=1)
        mismatches=np.flatnonzero(error>.02)
        worst=mismatches[np.argsort(error[mismatches])[::-1]][:8]
        summaries.append(dict(region_id=r['region_id'],particles=n,grid_advected_particles=int(mode.sum()),
            replay_mismatches=[dict(index=int(k),identity=ids[k].tolist(),error_cm=float(error[k]),
                nearest_phase=int(phase[k]),position_cm=p[k].tolist(),expected_cm=expected[k].tolist(),
                actual_raw_cm=vectors['advection_raw_positions'][k].tolist(),
                local_start_cm=local[k].tolist()) for k in worst],
            replay_mismatch_count=int(len(mismatches)),
            nearest_phase_counts={str(t):int((phase==t).sum()) for t in (-1,0,1,2,3)},
            particles_within_2_5cm_of_exact_bed=int((clearance<=.025).sum()),
            bed_near_solid_phase_particles=int(((clearance<=.025)&(phase==1)).sum()),
            bed_near_raw_inward_particles=int((bed_near&(normal_raw<0)).sum()),
            bed_near_raw_normal_speed_cm_s=stats(normal_raw[bed_near]),
            bed_near_final_normal_speed_cm_s=stats(normal_after[bed_near]),
            bed_near_contact_displacement_cm=stats(contact[bed_near]),
            bed_near_interpolated_divergence_per_s=stats(np.trace(j[bed_near&mode],axis1=1,axis2=2)),
            peak_neighborhood_raw_normal_speed_cm_s=stats(normal_raw[nearby]),
            incomplete_stencils=int((~complete).sum()),interior_particles=int(interior.sum()),
            grid_position_replay_error_cm=stats(error[mode]),ballistic_position_replay_error_cm=stats(error[~mode]),
            interpolated_divergence_per_s=stats(tr),centered_grid_divergence_sampled_per_s=stats(d),
            all_grid_mode_interpolated_divergence_per_s=stats(np.trace(j[mode],axis1=1,axis2=2)),
            local_first_order_volume_ratio_not_rk2_determinant=stats(np.linalg.det(np.eye(3)+dt*j[interior])),
            contact_or_inlet_displacement_cm=stats(contact),maximum_density=float(density[peak]),
            peak_world_cm=world.tolist(),particles_within_1m_of_peak=int(nearby.sum()),
            peak_neighborhood_phase_counts={str(t):int((nearby&(phase==t)).sum()) for t in (-1,0,1,2,3)},
            peak_neighborhood_bed_clearance_m=stats(clearance[nearby]),
            peak_neighborhood_precontact_speed_cm_s=stats(np.linalg.norm((vectors['advection_raw_positions']-p)[nearby]/dt,axis=1))))
        keys=('positions','velocities','identities','total','projection_boundary','advection_velocity',
              'advection_raw_positions','advection_positions','advection_raw_velocities','advection_velocities','advection_identities')
        for key in keys:
            path=(directory/r[key]).resolve()
            if path.parent!=directory:raise ValueError('Input escapes capture')
            sources[r[key]]=hashlib.sha256(path.read_bytes()).hexdigest()
    maximum = max(errors,default=0.)
    return dict(native_step=report['native_transfer_packet_step'],particles=sum(r['particles'] for r in summaries),
        native_compatible_particle_transport=compact,interface_transport_still_trilinear=not unified,
        shared_particle_interface_transport=unified,
        coordinate_contract='double-float-demote-v1' if unified else 'native-world-to-unit-v1',
        transport_include_sha256=transport_sources,
        rhi_validation_clean=rhi_clean,
        actual_native_transport_pair=True,pressure_coupled=validation['pressure_coupled'],quantiles=QUANTILES,
        interface_transport_validation=validation,
        grid_position_replay_error_cm=stats(errors),position_replay_tolerance_cm=.02,
        grid_position_replay_verified=bool(errors and maximum<=.02),
        all_position_replay_error_cm=stats(all_errors),
        all_position_replay_verified=bool(all_errors and max(all_errors)<=.02),
        interpolated_divergence_per_s=stats(traces),centered_grid_divergence_sampled_per_s=stats(discrete),
        contact_or_inlet_displacement_cm=stats(contact_moves),regions=summaries,source_files_sha256=sources,
        derivatives_are_instantaneous_not_measured_volume_loss=True,physical_visual_or_performance_acceptance=False)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory',type=Path);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists():raise FileExistsError(args.output)
    result=diagnose(args.directory)
    args.output.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('regions','source_files_sha256','interface_transport_validation')},indent=2))
