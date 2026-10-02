"""Audit fresh native closed-water controls without modifying any saved state."""
import argparse
import hashlib
import json
from pathlib import Path
import time
import numpy as np
from water_feature_flat_metrics import closed_box_phi,mesh_metrics,paired_residuals
from water_feature_stage_interfaces import column_interface
from water_feature_cell_volume import reconstructed_volume
from water_feature_temporal_metrics import paired_column_differences


def digest(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def quantiles(values):
    values=list(values)
    return dict(count=len(values),minimum=float(min(values)),median=float(np.median(values)),
        p95=float(np.quantile(values,.95)),maximum=float(max(values))) if values else dict(count=0)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--controls',type=Path,nargs=3,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists():raise FileExistsError(args.output)
    started=time.perf_counter();reports=[json.loads(p.read_text()) for p in args.controls]
    hashes={str(p.resolve()):digest(p) for p in args.controls}
    for report in reports:
        if not all(report[k] for k in ('complete','originals_unchanged','live_engine_fields_unchanged','executed_modules_unchanged')):
            raise ValueError('Complete preserved native controls required')
        for group in ('original_input_sha256','source_code_sha256','arrays','meshes'):
            for path,sha in report[group].items():
                if path in hashes and hashes[path]!=sha:raise ValueError('Conflicting dependency versions')
                hashes[path]=sha
    for name in ('audit_water_feature_flat_equilibrium.py','water_feature_flat_metrics.py',
            'test_water_feature_flat_metrics.py','water_feature_cell_volume.py','water_feature_temporal_metrics.py'):
        path=Path(__file__).with_name(name);hashes[str(path.resolve())]=digest(path)
    if any(digest(p)!=sha for p,sha in hashes.items()):raise ValueError('Input changed before audit')
    common=('shape','cell_m','initial_height_m','initial_particles','original_input_sha256','source_code_sha256','inherited_native_parameters')
    if any(any(r[k]!=reports[0][k] for k in common) for r in reports[1:]):
        raise ValueError('Matched geometry, initial lattice, native parameters and source versions required')
    if [(r['radius_policy'],r['subdivision']) for r in reports]!=[('stock',1),('stock',4),('flat-lattice',1)]:
        raise ValueError('Declared fixed control comparison required')
    controls=[]
    for path,report in zip(args.controls,reports):
        h=report['cell_m'];shape=tuple(report['shape']);reference=report['initial_height_m']
        if [r['frame'] for r in report['frames']]!=list(range(49)) or [r['frame'] for r in report['mesh_frames']]!=list(range(49)):
            raise ValueError('Initial state and all48 evolved states/meshes required')
        if len(report['steps'])!=48*2*report['subdivision'] or any(r['index']!=i for i,r in enumerate(report['steps'])):
            raise ValueError('Incomplete actual liquid-step history')
        expected=0.
        for i,row in enumerate(report['steps']):
            if (row['requested_frame']!=i//(2*report['subdivision'])+1
                    or row['substep']!=i%(2*report['subdivision'])
                    or abs(row['dt_native']/2.5-1/(48*report['subdivision']))>1e-9):
                raise ValueError('Wrong fixed native step time/order')
            expected+=row['dt_native']
            if abs(row['time_native_after']-expected)/2.5>1e-5:raise ValueError('Native clock jump')
        obstacle=np.load(report['obstacle_array'],allow_pickle=False)
        np.testing.assert_array_equal(obstacle,closed_box_phi(shape).astype(np.float32))
        frames=[]
        for state,mesh in zip(report['frames'],report['mesh_frames']):
            phi=np.load(state['fields']['phi'],allow_pickle=False);flags=np.load(state['fields']['flags'],allow_pickle=False)
            columns=[dict(column=c,interface=column_interface(phi,flags,c,h)) for c in report['columns']]
            if columns!=state['columns']:raise ValueError('Saved fields/column observations disagree')
            if not mesh['mapping']['obj_normalization_verified'] or not mesh['mapping']['all_triangle_indices_match']:
                raise ValueError('Unverified native mesh coordinates')
            metrics=mesh_metrics(np.load(mesh['positions'],allow_pickle=False),np.load(mesh['triangles'],allow_pickle=False),
                report['columns'],h,report['mesh_cell_m'],shape)
            paired=paired_residuals(metrics['samples'],columns,reference)
            speeds=np.load(state['fields']['velocity'],allow_pickle=False)
            speed=float(np.linalg.norm(speeds,axis=-1).max())*h*2.5
            if speed!=state['max_grid_speed_mps']:raise ValueError('Actual field speed changed')
            row=dict(frame=state['frame'],time_s=state['frame']/24,columns=columns,mesh=metrics,
                paired_residuals=paired,phi_minus_initial_m=quantiles(p['phi_minus_initial_m'] for p in paired if p['phi_minus_initial_m'] is not None),
                mesh_minus_phi_m=quantiles(p['mesh_minus_phi_m'] for p in paired if p['mesh_minus_phi_m'] is not None),
                max_all_grid_speed_mps=speed,primary_count=state['primary_count'])
            if state['frame'] in (0,1,12,24,48):
                row['reconstructed_liquid_volume']=[reconstructed_volume(phi,obstacle,(h,)*3,subdivisions=n) for n in (4,8)]
            frames.append(row)
        controls.append(dict(receipt=str(path.resolve()),radius_policy=report['radius_policy'],radius_factor=report['radius_factor'],
            subdivision=report['subdivision'],steps=len(report['steps']),frames=frames,
            integrated_duration_s=expected/2.5,native_final_clock_s=report['native_final_clock_s'],
            analytic_first_union=report['analytic_union_verified'],first_join_columns=report['first_join_columns'],
            code_objects=report['exact_liquid_code'],body_cost_s=sum(r['body_and_clock_elapsed_s'] for r in report['steps']),
            mesh_export_cost_s=sum(r['elapsed_s'] for r in report['mesh_frames'])))
    comparison=paired_column_differences(controls[0]['frames'][-1]['columns'],controls[1]['frames'][-1]['columns'])
    if any(digest(p)!=sha for p,sha in hashes.items()):raise ValueError('Input changed during audit')
    report=dict(complete=True,accepted=False,originals_unchanged=True,controls=controls,stock_time_refinement_final_columns=comparison,
        stock_time_refinement_absolute_phi_differences_m=quantiles(abs(p['vertical_difference_m']) for p in comparison if p['supported']),
        dependency_sha256=hashes,elapsed_s=time.perf_counter()-started,
        limitations='Manufactured still-water/regular lattice only, fixed native body steps without host emitters. Radius calibrated analytically for one horizontal grid phase, not a general liquid repair. Native mesh extraction is unchanged and may disagree with phi/walls. Volumes are level-set quadrature and mesh enclosed volumes, not conserved mass. All-grid MAC norm includes ghost/air samples. Competing external Unreal work exists; costs are unisolated offline timings, not gameFPS. No foam, collision, optics or full-river acceptance.')
    with args.output.open('x') as stream:json.dump(report,stream,indent=2)
    print('NATIVE_FLAT_CONTROLS_AUDITED',args.output,len(hashes),report['elapsed_s'],flush=True)


if __name__=='__main__':main()
