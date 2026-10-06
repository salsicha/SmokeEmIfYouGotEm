"""Export a validated Pinball cook to a fresh staging folder, never live data."""
import argparse
import json
import shutil
import subprocess
from pathlib import Path
import numpy as np
from build_pinball_reference_candidate import ROOT,PACKAGE,TERRAIN,sha
from export_hance_evidence_runtime import read_frame
from export_pacuare_evidence_runtime import write_rsbf
from solver_face_discharge import face_discharge


def export(candidate,run,solver,out,steps=12000,frame_interval=2000):
    if out.exists(): raise ValueError('Fresh export required')
    receipt=json.loads((candidate/'candidate.json').read_text())
    validation=json.loads((run/'validation.json').read_text())
    assert validation['passed'] and validation['finite_state'] and not validation['velocity_limit_reached']
    assert validation['mass_relative_drift']<.002
    assert sha(PACKAGE/'cooked_flow_fields/manifest.json')==receipt['cooked_manifest_sha256']
    assert sha(candidate/'scenario/bed.npy')==receipt['scenario_bed_sha256']
    cm=json.loads((PACKAGE/'cooked_flow_fields/manifest.json').read_text());g=cm['grid'];band=cm['bands'][0]
    frames=sorted((run/'frames').glob('frame_*.csv'))
    scenario=json.loads((candidate/'scenario/scenario.json').read_text())
    dt=scenario['fixed_dt']
    assert steps>0 and frame_interval>0 and steps%frame_interval==0
    assert len(frames)==steps//frame_interval+1,'Frames do not match the declared cook recipe'
    f=read_frame(frames[-1],g['ny'],g['nx']);prev=read_frame(frames[-2],g['ny'],g['nx'])
    bed=np.load(candidate/'scenario/bed.npy');wet=f['h']>1.e-6
    assert np.allclose((f['eta']-f['h'])[wet],bed[wet],atol=1.e-5)
    dh=np.abs(f['h']-prev['h']);assert np.percentile(dh,95)<.002 and dh.max()<.1
    q=face_discharge(solver.resolve(),candidate/'scenario',f)
    target=band['discharge_target_m3s']
    assert np.max(abs(q-target))/target<.025, 'Flow has not settled to target discharge'
    for rec in receipt['rocks']:
        ft=rec['feature'];c=round((ft['station_m']-g['origin_x_m'])/g['dx_m'])
        rows=[round((ft['lateral_m']+d-g['origin_y_m'])/g['dy_m']) for d in (-1,1)]
        if ft['type']=='bed_shelf':
            # The authored shallow bar is allowed to overtop. This is a
            # separate geometry target, not permission to drown either rock.
            assert all(f['h'][r,c]<=.25 for r in rows),'Bypass bar remains too deep for a shallow-water control'
            # A dry/shallow centre does not exclude a deep seam between two
            # rounded footprints. Check the complete bank-to-rock connection.
            seam_col=round((2050-g['origin_x_m'])/g['dx_m'])
            seam_rows=[round((l-g['origin_y_m'])/g['dy_m']) for l in range(-32,-9,2)]
            assert all(f['h'][r,seam_col]<=.25 for r in seam_rows),'Bank-to-rock bar still has a navigable deep seam'
        elif ft['crest_below_ws_m']<0:
            assert all(not wet[r,c] for r in rows),'Named rock drowned in recook'
    out.mkdir(parents=True)
    ck=out/'cooked_flow_fields';shutil.copytree(PACKAGE/'cooked_flow_fields',ck)
    shutil.copytree(candidate/'scenario',out/'scenario')
    arrays=dict(bed=bed,h=f['h'],u=np.where(wet,f['u'],0),v=np.where(wet,f['v'],0),wet_mask=wet)
    for key,array in arrays.items():
        meta=band['arrays'][key];path=ck/meta['file']
        np.save(path,np.asarray(array,dtype=meta['dtype']));meta['sha256']=sha(path)
    speed=np.hypot(f['u'],f['v']);fr=np.where(f['h']>.05,speed/np.sqrt(9.81*np.maximum(f['h'],.05)),0.)
    energy=np.clip(.6*np.clip((speed-.5)/2.5,0,1)+.4*np.clip((fr-.5)/.5,0,1),0,1)
    bwet=wet&(f['h']>.05);base=band['presentation_baseline'];path=ck/base['file']
    write_rsbf(path,g['ny'],g['nx'],g['origin_y_m'],g['dx_m'],np.where(bwet,f['eta'],bed),energy,bwet)
    base['sha256']=sha(path)
    band['convergence']=dict(compared_frames=[x.name for x in frames[-2:]],frame_spacing_s=dt*frame_interval,
                             max_abs_dh_m=float(dh.max()),p95_abs_dh_m=float(np.percentile(dh,95)),
                             note=f'{dt*steps:g} s continuation from committed steady field; local unsteady whitewater remains.')
    band['discharge_steady_m3s']=dict(west=float(q[0]),mid=float(q[len(q)//2]),east=float(q[-1]),
                                    min=float(q.min()),max=float(q.max()),method='exact current-core numerical face mass flux')
    band.pop('discharge_cell_centre_hu_sum_m3s',None)
    band['field_stats']=dict(h_max_m=float(f['h'].max()),h_mean_m=float(f['h'].mean()),wet_fraction=float(wet.mean()),speed_max_m_per_s=float(speed.max()))
    band['scenario_input_sha256']={name:sha(out/'scenario'/name) for name in ('scenario.json','bed.npy','initial_state.npz')}
    cm['generator']='physics/scripts/export_pinball_reference_candidate.py'
    cm['generated_on']='2026-10-05'
    cm['solver'].update(binary_sha256=sha(solver),steps=steps,frame_interval_steps=frame_interval,simulated_seconds=dt*steps,
                        runtime_crop_boundary_mode='cooked_ghost',
                        cook_manifest_sha256=sha(run/'manifest.json'),final_frame_sha256=sha(frames[-1]))
    core_commit=subprocess.check_output(['git','-C',str(ROOT/'unreal/Plugins/SEIYGECore'),'rev-parse','HEAD'],text=True).strip()
    cm['pinball_reference']=receipt | dict(cook_validation=validation,source_core_commit=core_commit,
                                         status='recooked_candidate_requires_native_acceptance')
    (ck/'manifest.json').write_text(json.dumps(cm,indent=2)+'\n')
    stream=json.loads((PACKAGE/'runtime/moving_water_streaming.json').read_text())
    stream['full_reach_transit_seed']['cooked_fields_manifest_sha256']=sha(ck/'manifest.json')
    (out/'moving_water_streaming.json').write_text(json.dumps(stream,indent=2)+'\n')
    tm=json.loads((TERRAIN/'huacas_evidence_terrain_manifest.json').read_text())
    terrain_source=ROOT/tm['outputs']['heightfield']
    assert sha(terrain_source)==receipt['source_heightfield_sha256']
    shutil.copy2(candidate/'huacas_evidence_heightfield_2017.png',out/'huacas_evidence_heightfield_2017.png')
    tm['outputs']['heightfield_sha256']=sha(out/'huacas_evidence_heightfield_2017.png')
    tm['pinball_reference']=dict(catalogue=receipt['catalogue'],catalogue_sha256=receipt['catalogue_sha256'],
                               geometry='two inferred rock crowns and an explicitly authored shallow bypass shelf; same shape as solver bed; not surveyed',
                               source_heightfield_sha256=receipt['source_heightfield_sha256'])
    (out/'huacas_evidence_terrain_manifest.json').write_text(json.dumps(tm,indent=2)+'\n')
    result=dict(status='staged_not_installed',validation=validation,discharge=band['discharge_steady_m3s'],
                convergence=band['convergence'],source_receipt=str(candidate/'candidate.json'))
    (out/'export.json').write_text(json.dumps(result,indent=2)+'\n')
    return result


if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__)
    for name in ('candidate','run','solver','out'):ap.add_argument('--'+name,type=Path,required=True)
    ap.add_argument('--steps',type=int,default=12000);ap.add_argument('--frame-interval',type=int,default=2000)
    a=ap.parse_args();print(json.dumps(export(a.candidate,a.run,a.solver,a.out,a.steps,a.frame_interval),indent=2))
