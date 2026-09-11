"""Verify actual live particle input and rendered volume, not visual realism."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from PIL import Image
from liquid_reconstruction_layout import from_report


def audit(directory,log):
    capture=json.loads((directory/'capture.json').read_text())
    steps=capture['simulation_steps']
    if not isinstance(steps,int) or not 720<=steps<=3600:
        raise ValueError('Bounded actual simulation-step count required')
    report=json.loads((directory/'live_density/report.json').read_text())
    layout=from_report(report)
    count=report['last_gpu_particle_count']
    packed=np.fromfile(directory/'live_density/positions.rgba32f',dtype='<f4').reshape(count,4)[:,:3]
    last=max(directory.glob('optics_*_particles.json'))
    actual=json.loads(last.read_text())
    emitters=[e for e in actual['emitters'] if e['emitter']=='Grid3D_FLIP_FluidControl_Emitter' and e.get('position_count',0)]
    if len(emitters)!=1:
        raise ValueError('Expected one actual primary fluid particle population')
    secondary=[e for e in actual['emitters'] if e.get('position_count',0) and e not in emitters]
    if secondary and (not capture.get('native_secondary_foam_requested') or
                      any(e['emitter']!='Grid3D_FLIP_Secondary_Emitter' for e in secondary)):
        raise ValueError('Unexpected additional particle population')
    expected=np.asarray(emitters[0]['particle_rows'])[:,2:5]/100
    if expected.shape!=packed.shape:
        raise ValueError('Live GPU count differs from actual final simulation count')
    position_error=abs(expected-packed)
    surface=np.fromfile(directory/'live_density/surface.rgba16f',dtype='<f2').reshape(*layout['render'][::-1],4).astype(float)
    finite=bool(np.isfinite(packed).all() and np.isfinite(surface).all())
    valid_field=bool(abs(surface[...,0]).max()<=50.01 and
                     surface[...,1].min()>=0 and surface[...,1].max()<=1 and
                     (surface[...,0]<0).any() and (surface[...,0]>0).any())
    frames=sorted(directory.glob('motion_*.png'))
    images=[np.asarray(Image.open(p).convert('RGB')) for p in frames]
    hashes=[hashlib.sha256(i.tobytes()).hexdigest() for i in images]
    changes=[float(np.mean(abs(a.astype(float)-b))) for a,b in zip(images,images[1:])]
    errors=[line for line in log.read_text(errors='replace').splitlines() if 'Error:' in line or 'Fatal error:' in line]
    rejected_spawns=[line for line in log.read_text(errors='replace').splitlines() if 'execeed max GPU per frame spawn' in line]
    result=dict(capture_complete=capture['complete'],capture_error=capture['error'],reconstruction_layout=layout,
                secondary_particle_count=sum(e['position_count'] for e in secondary),secondary_motion_verified=False,
                secondary_rejected_spawn_batches=len(rejected_spawns),
                gpu_updates=report['gpu_update_count'],simulation_steps_requested=steps,particle_count=count,diagnostics=report['diagnostics'],
                position_max_error_m=float(position_error.max()),position_rms_error_m=float(np.sqrt(np.mean(position_error**2))),
                finite=finite,valid_distance_and_coverage_ranges=valid_field,engine_error_lines=errors,
                motion_frame_count=len(frames),unique_decoded_motion_frames=len(set(hashes)),
                adjacent_frame_mean_rgb_changes=changes,final_simulation_capture=last.name,
                blocking_capture_wall_seconds=capture['wall_seconds'],not_a_frame_rate_measurement=True,
                occupancy_reconciliation_on_gpu=report.get('live_solver_occupancy_support',False),photoreal_or_physical_acceptance=False)
    result['live_pipeline_verified']=bool(capture['complete'] and capture['error'] is None and not report['error'] and
        report['gpu_update_count']>=steps-6 and report['diagnostics']==[0,0,0,0] and finite and valid_field and
        position_error.max()<=1e-4 and not errors and len(frames)==30 and len(set(hashes))>=25)
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory',type=Path)
    parser.add_argument('--log',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    result=audit(args.directory,args.log)
    args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
    raise SystemExit(0 if result['live_pipeline_verified'] else 1)
