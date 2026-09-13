"""Read-only analysis of paired native South Fork P2G/pressure fields.

Predicts the installed D M G operator from the actual captured pressure; does
not call a replacement solver or mistake predicted velocity for a GPU readback.
"""
import argparse
import json
from pathlib import Path
import numpy as np
from liquid_compatible_projection import constrain_velocity, gradient, divergence, surface_gradient_weights


def load_field(directory, record, name, channels):
    path=(directory/record[name]).resolve()
    if path.parent!=directory.resolve():
        raise ValueError('Projection field path leaves the native capture')
    fmt=record[name+'_format']
    if (channels==4 and fmt!='rgba16f') or (channels==1 and fmt not in ('r16f','r32f')):
        raise ValueError('Unexpected native field format')
    cells=tuple(record['cells'][::-1]);dtype='<f4' if fmt=='r32f' else '<f2'
    data=np.fromfile(path,dtype=dtype).astype(float)
    if data.size!=int(np.prod(cells))*channels or not np.isfinite(data).all():
        raise ValueError('Incomplete or nonfinite native projection field')
    return data.reshape((*cells,channels) if channels>1 else cells)


def analyze(directory,dt):
    directory=Path(directory).resolve()
    report=json.loads((directory/'stages.json').read_text())
    if (not report.get('native_projection_packet_requested') or report['exchange_error'] or
            not report['native_transfer_packet_saved'] or not report['scheduler_alignment_observed'] or
            not np.isfinite(dt) or dt<=0):
        raise ValueError('Complete aligned paired projection packet and positive time step required')
    records=report['native_transfer_packet'];step=report['native_transfer_packet_step']
    interface=report.get('native_interface_transport', {})
    coupled=interface.get('pressure_coupled', False)
    requested_dt=dt
    if coupled:
        # Validates provenance, complete per-step transport and the paired scalar.
        # Import here avoids a module cycle through the shared field reader.
        from audit_liquid_native_interface import audit
        audit(directory)
        dt=interface['fluid_delta_seconds'][-1]
        if dt<=0:raise ValueError('Positive actual pressure timestep required')
    surface_weights=[]
    if sorted(r['region_id'] for r in records)!=list(range(12)):
        raise ValueError('All twelve owners required')
    results=[];div_errors=[];before_all=[];after_all=[];pressures=[];ratios=[]
    native_after_all=[];velocity_errors=[]
    for r in records:
        if (r.get('projection_native_step')!=step or
                r.get('projection_input_stage')!='Compute Divergence: after stage' or
                r.get('projection_pressure_stage')!='Solve Pressure: after final iteration and halo exchange'):
            raise ValueError('Unpaired native projection stages')
        b=load_field(directory,r,'projection_boundary',4)
        v=load_field(directory,r,'projection_velocity_before',4)[...,:3]
        native_div=load_field(directory,r,'projection_divergence',1)
        p=load_field(directory,r,'projection_pressure',1)
        spacing=np.asarray(r['extent_cm'])/np.asarray(r['cells']);cell_volume=float(np.prod(spacing/100))
        fixed,mobility,fluid=constrain_velocity(v,b)
        # +/-2 composed stencil must be completely represented. XY halos are
        # duplicate owners; there are no Z halos in this native layout.
        physical=np.zeros(fluid.shape,dtype=bool);physical[2:-2,2:-2,2:-2]=True
        selected=fluid & physical
        computed_before=divergence(fixed,spacing)
        weights=np.ones_like(mobility)
        if coupled:
            pair=interface['regions'][r['region_id']]
            path=(directory/pair['before']).resolve()
            if path.parent!=directory:raise ValueError('Pressure interface leaves capture')
            phi=np.fromfile(path,dtype='<f4').astype(float).reshape(fluid.shape)
            # Every captured fluid/air cell must agree, not merely a sampled
            # subset. Solids and prescribed boundary types retain their identity.
            weights=surface_gradient_weights(b,phi)
            if np.any((np.rint(b[...,3])==3)&(phi>=0)&(p!=0)):
                raise ValueError('External air has nonzero gauge pressure')
            surface_weights.append(float(weights[physical].max(initial=1)))
        predicted_v=fixed-dt*mobility*weights*gradient(p,spacing)
        predicted_after=divergence(predicted_v,spacing)
        if r.get('projection_output_stage')=='Project Pressure: after stage':
            after_v=load_field(directory,r,'projection_velocity_after',4)[...,:3]
            native_after_all.extend(divergence(after_v,spacing)[selected])
            velocity_errors.extend((after_v-predicted_v)[selected].ravel())
        total_path=(directory/r['total']).resolve()
        if total_path.parent!=directory:raise ValueError('P2G field leaves capture')
        total=np.fromfile(total_path,dtype='<f4')
        if total.size!=fluid.size*4 or not np.isfinite(total).all():raise ValueError('Invalid P2G total')
        density=total.reshape((*fluid.shape,4))[...,3].astype(float)/cell_volume
        div_errors.extend((computed_before-native_div)[selected]);before_all.extend(native_div[selected])
        after_all.extend(predicted_after[selected]);pressures.extend(p[selected]);ratios.extend(density[selected])
        results.append(dict(region_id=r['region_id'],interior_fluid_cells=int(selected.sum()),
                            excluded_z_edge_fluid_cells=int((fluid & ~physical)[:,2:-2,2:-2].sum()),
                            nonpositive_mass_fluid_cells=int((selected & (density<=0)).sum()),
                            low_mass_fluid_cells=int((selected & (density>0) & (density<=.1)).sum()),
                            max_predicted_pressure_velocity_change_cm_s=float(abs(predicted_v-fixed)[selected].max(initial=0))))
    quantiles=[0,.1,.5,.9,.99,1]
    rms=lambda x:float(np.sqrt(np.mean(np.square(x)))) if len(x) else 0.
    return dict(source_directory=str(directory),native_p2g_step=step,requested_step_seconds=requested_dt,
                actual_pressure_step_seconds=dt if coupled else None,
                regions=results,interior_fluid_cells=len(ratios),
                divergence_input_reconstruction_rms_error_per_s=rms(div_errors),
                divergence_input_reconstruction_max_error_per_s=float(np.max(np.abs(div_errors),initial=0)),
                native_divergence_before_rms_per_s=rms(before_all),
                predicted_divergence_after_rms_per_s=rms(after_all),
                predicted_after_over_before_rms=rms(after_all)/rms(before_all) if rms(before_all) else None,
                native_divergence_after_rms_per_s=rms(native_after_all) if len(native_after_all)==len(before_all) else None,
                post_velocity_reconstruction_rms_error_cm_s=rms(velocity_errors) if velocity_errors else None,
                post_velocity_reconstruction_max_error_cm_s=float(np.max(np.abs(velocity_errors))) if velocity_errors else None,
                pressure_quantiles_cm2_s2=np.quantile(pressures,quantiles).tolist() if pressures else [],
                deposited_volume_over_cell_volume_quantiles=np.quantile(ratios,quantiles).tolist() if ratios else [],
                quantiles=quantiles,zero_mass_fluid_cells=sum(r['nonpositive_mass_fluid_cells'] for r in results),
                low_mass_fluid_cells=sum(r['low_mass_fluid_cells'] for r in results),
                predicted_velocity_is_not_native_post_projection_readback=True,
                native_post_projection_velocity_available=len(native_after_all)==len(before_all),
                pressure_relaxation_model=report.get('pressure_relaxation_model','inherited-native-box'),
                pressure_relaxation_omegas=report.get('pressure_relaxation_omegas'),
                reconstructed_free_surface=coupled,
                maximum_surface_gradient_weight=max(surface_weights,default=1),
                native_pressure_relaxation_changed='pressure_relaxation_model' in report,
                production_scene_promoted=False,
                physical_visual_or_performance_acceptance=False)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory',type=Path);parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--requested-step-seconds',type=float,required=True)
    args=parser.parse_args()
    if args.output.exists():raise FileExistsError(args.output)
    result=analyze(args.directory,args.requested_step_seconds)
    args.output.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='regions'},indent=2))
