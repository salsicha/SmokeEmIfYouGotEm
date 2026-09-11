"""Audit actual secondary emission and motion; never a realism acceptance gate."""
import argparse
import json
from pathlib import Path
import numpy as np
from liquid_current_surface_foam import sample
from analyze_liquid_grid_readback import load_fields


def sampled_contact_verified(capture, records, errors):
    """Only sampled contact evidence: missing telemetry must not pass."""
    if (not capture.get('complete') or capture.get('error') or errors or
            not capture.get('secondary_exact_contact_compiled') or
            not any(r.get('count', 0) > 0 for r in records)):
        return False
    for record in records:
        count = record.get('count')
        if count is None or count < 0 or record.get('exact_bed_probe_count') != count:
            return False
        for key in ('below_bed', 'outside_domain', 'missing_exact_bed_probe_count',
                    'nonfinite_positions', 'nonfinite_velocities'):
            if record.get(key) != 0:
                return False
    return True


def particle_rows(emitter):
    count=emitter['position_count']
    rows=np.asarray(emitter.get('particle_rows',[]),dtype=float).reshape(-1,8)
    if len(rows)!=count or not np.isfinite(rows).all():
        raise ValueError('Missing or nonfinite actual secondary state')
    if len(set(rows[:,0]))!=count or (rows[:,1]!=-1).any():
        raise ValueError('Secondary identity must be unique and not a native-face source')
    return rows


def recorded_current_stage_order(report):
    """Dispatch counters alone do not verify every substep or sampled SDF."""
    ticks=report.get('updates_with_simulation_tick',0)
    return bool(report.get('current_surface_before_secondary') and not report.get('error') and
                ticks>0 and report.get('reconstruction_before_secondary_updates')==ticks and
                report.get('secondary_pre_stage_events',0)>=ticks)


def surface_alignment(rows, states, rendered, native, extent, origin):
    """Compare two actual SDFs at local particle positions, not sprite visibility."""
    rows=np.asarray(rows,dtype=float).reshape(-1,8)
    states=np.asarray(states,dtype=float)
    extent=np.asarray(extent,dtype=float);origin=np.asarray(origin,dtype=float)
    if states.shape!=(len(rows),) or not np.isin(states,[0,1,2]).all():
        raise ValueError('Actual foam/spray/bubble state required for each particle')
    if extent.shape!=(3,) or origin.shape!=(3,) or not np.isfinite(extent).all() or (extent<=0).any() or not np.isfinite(origin).all():
        raise ValueError('Finite local origin and positive XYZ extent required')
    for field in (rendered,native):
        if field.ndim!=4 or field.shape[-1]<1 or not np.isfinite(field).all():
            raise ValueError('Finite ZYX signed-distance volume required')
    if not np.isfinite(rows).all():raise ValueError('Finite particle positions required')
    unit=(rows[:,2:5]-origin)/extent
    valid=((unit>=0)&(unit<=1)).all(axis=1)
    r=sample(rendered,unit[valid])[:,0];n=sample(native,unit[valid])[:,0]
    groups={}
    for state,name in enumerate(('foam','spray','bubble')):
        mask=states[valid]==state
        groups[name]=dict(count=int(mask.sum()),
            rendered_inside_count=int((r[mask]<0).sum()),
            rendered_absolute_distance_cm_quantiles=np.quantile(abs(r[mask]),[.5,.95,1]).tolist() if mask.any() else [],
            rendered_distance_cm_quantiles=np.quantile(r[mask],[0,.25,.5,.75,1]).tolist() if mask.any() else [],
            native_distance_cm_quantiles=np.quantile(n[mask],[0,.25,.5,.75,1]).tolist() if mask.any() else [],
            rendered_minus_native_cm_quantiles=np.quantile((r-n)[mask],[0,.25,.5,.75,1]).tolist() if mask.any() else [],
            opposite_surface_sign_count=int(((r<0)!=(n<0))[mask].sum()))
        # Particle rows contain velocity, not sprite size; do not interpret
        # negative SDF or particle state as proof of occlusion or visibility.
    return dict(sampled_count=int(valid.sum()),out_of_volume_count=int((~valid).sum()),
        by_state=groups,rendered_visibility_verified=False,surface_coupling_verified=False)


def audit(directory):
    capture=json.loads((directory/'capture.json').read_text())
    log=(directory.parent/(directory.name+'.log')).read_text(errors='replace')
    records=[];previous=None;previous_frame=None;tracks=[]
    for path in sorted(directory.glob('terrain_*_particles.json')):
        frame=int(path.name.split('_')[1]);data=json.loads(path.read_text())
        emitters=[e for e in data['emitters'] if e['emitter']=='Grid3D_FLIP_Secondary_Emitter']
        if len(emitters)!=1:raise ValueError('Exactly one initialized secondary emitter required')
        emitter=emitters[0];rows=particle_rows(emitter)
        records.append(dict(frame=frame,count=len(rows),
            below_bed=emitter['below_exact_bed_over_1mm_count'],
            below_bed_one_cell=emitter['below_exact_bed_over_one_cell_count'],
            max_bed_penetration_cm=emitter['maximum_exact_bed_penetration_cm'],
            outside_domain=emitter['outside_fixture_domain_count'],
            exact_bed_probe_count=emitter['exact_bed_probe_count'],
            missing_exact_bed_probe_count=emitter['missing_exact_bed_probe_count'],
            nonfinite_positions=emitter['nonfinite_positions'],
            nonfinite_velocities=emitter['nonfinite_velocities']))
        if 'secondary_render_rows' in emitter:
            render=np.asarray(emitter['secondary_render_rows'],dtype=float).reshape(-1,8)
            if render.shape!=(len(rows),8) or not np.isfinite(render).all() or not np.array_equal(render[:,0],rows[:,0]):
                raise ValueError('Secondary rendering state does not match particle identities')
            records[-1]['render_state']=dict(
                state_counts={str(int(state)):int((render[:,1]==state).sum()) for state in np.unique(render[:,1])},
                width_cm_quantiles=np.quantile(render[:,2],[0,.5,.95,1]).tolist() if len(render) else [],
                height_cm_quantiles=np.quantile(render[:,3],[0,.5,.95,1]).tolist() if len(render) else [],
                nonpositive_size_count=int((render[:,2:4]<=0).any(axis=1).sum()),
                material_parameter_ranges=np.stack((render[:,4:].min(axis=0),render[:,4:].max(axis=0))).tolist() if len(render) else [])
        if 'secondary_surface_rows' in emitter:
            samples=np.asarray(emitter['secondary_surface_rows'],dtype=float).reshape(-1,3)
            if samples.shape!=(len(rows),3) or not np.isfinite(samples).all() or not np.array_equal(samples[:,0],rows[:,0]):
                raise ValueError('Shared-surface sample telemetry does not match particle identities')
            updated=samples[:,1]>0
            records[-1]['shared_surface_samples']=dict(updated_particles=int(updated.sum()),
                newly_spawned_without_update=int((~updated).sum()),
                age_seconds_quantiles=np.quantile(samples[updated,1],[0,.5,1]).tolist() if updated.any() else [],
                sampled_distance_cm_quantiles=np.quantile(samples[updated,2],[0,.5,1]).tolist() if updated.any() else [])
        if previous is not None:
            ids,a,b=np.intersect1d(previous[:,0],rows[:,0],return_indices=True)
            movement=np.linalg.norm(rows[b,2:5]-previous[a,2:5],axis=1)
            tracks.append(dict(from_frame=previous_frame,to_frame=frame,tracked=len(ids),
                moving=int((movement>1e-3).sum()),
                displacement_cm_quantiles=np.quantile(movement,[0,.5,.95,1]).tolist() if len(ids) else []))
        previous=rows;previous_frame=frame
    paused=[]
    for name in ('optics_00_particles.json','optics_08_particles.json'):
        emitters=json.loads((directory/name).read_text())['emitters']
        rows=particle_rows(next(e for e in emitters if e['emitter']=='Grid3D_FLIP_Secondary_Emitter'))
        paused.append(rows[np.argsort(rows[:,0])])
    errors=[line for line in log.splitlines() if 'Error:' in line or 'Fatal error:' in line]
    rejected=log.count('execeed max GPU per frame spawn')
    alignment=None
    if (directory/'live_density/surface.rgba16f').is_file() and (directory/'optics_08_grids/grids.json').is_file():
        final=json.loads((directory/'optics_08_particles.json').read_text())
        emitter=next(e for e in final['emitters'] if e['emitter']=='Grid3D_FLIP_Secondary_Emitter')
        if 'secondary_render_rows' in emitter:
            if final.get('computational_grid_extents_cm')!='X=2231.250 Y=2231.250 Z=800.000':
                raise ValueError('Unsupported captured surface-alignment domain')
            rows=particle_rows(emitter);render=np.asarray(emitter['secondary_render_rows']).reshape(-1,8)
            if not np.array_equal(rows[:,0],render[:,0]):raise ValueError('Mismatched final particle identities')
            rendered=np.fromfile(directory/'live_density/surface.rgba16f',dtype='<f2').reshape(48,136,136,4).astype(float)
            native=load_fields(directory/'optics_08_grids')['SDF']
            clock=np.fromfile(directory/'live_density/clock.rgba32f',dtype='<f4').reshape(-1,4)[-1]
            if clock[1]!=0 or not np.array_equal(*paused):
                raise ValueError('Surface comparison requires the same paused particle state')
            alignment=surface_alignment(rows,render[:,1],rendered,native,[2231.25,2231.25,800],[-1115.625,-1115.625,0])
            alignment['snapshot']='paused optics_08 particles/native SDF and live_density rendered SDF'
    cache_report=None
    if capture.get('secondary_shared_surface_requested'):
        cache_report={}
        for name in ('live_foam_active','live_density'):
            path=directory/name
            report=json.loads((path/'report.json').read_text())
            rendered=np.fromfile(path/'surface.rgba16f',dtype='<f2')
            shared=np.fromfile(path/'secondary_surface.rgba16f',dtype='<f2')
            exact=rendered.size==136*136*48*4 and np.isfinite(rendered).all() and np.array_equal(rendered,shared)
            cache_report[name]=dict(exact_completed_surface_copy=bool(exact),
                publishes=report['secondary_surface_publishes'],updates=report['gpu_update_count'],
                current_stage_requested=bool(report.get('current_surface_before_secondary')),
                recorded_current_stage_order=recorded_current_stage_order(report),
                verified=bool(exact and report['secondary_shared_render_surface'] and not report['error'] and report['secondary_surface_publishes']==report['gpu_update_count']))
        cache_report['timing']=('Current reconstructed surface published before secondary stages; dispatch counters and final samples audited separately'
            if capture.get('secondary_current_surface_compiled') else 'Previous completed rendered surface consumed by next Niagara step')
        cache_report['sampled_by_gpu']=any(r.get('shared_surface_samples',{}).get('updated_particles',0)>0 for r in records)
        cache_report['same_step_alignment_verified']=False
        cache_report['all_simulation_substeps_verified']=False
    sampled_contact=sampled_contact_verified(capture,records,errors)
    return dict(capture_complete=capture['complete'],capture_error=capture['error'],
        records=records,tracked_motion=tracks,engine_errors=errors,rejected_spawn_batches=rejected,
        emitted_and_moved=bool(any(r['count'] for r in records) and any(t['moving'] for t in tracks)),
        paused_state_exact=np.array_equal(*paused),
        sampled_particles_below_bed=sum(r['below_bed'] for r in records),
        rendered_surface_alignment=alignment,shared_surface_cache=cache_report,
        endpoint_phase_prediction=bool(capture.get('secondary_endpoint_prediction_compiled')),
        sampled_secondary_contact_verified=sampled_contact,secondary_terrain_contact_verified=False,
        contact_scope='Exact current-mesh probes at captured times; not exhaustive trajectory or full-scene validation',
        physical_visual_or_performance_acceptance=False)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory',type=Path)
    parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    output=args.output or args.directory/'secondary_audit.json'
    if output.exists():raise FileExistsError(output)
    result=audit(args.directory)
    output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
