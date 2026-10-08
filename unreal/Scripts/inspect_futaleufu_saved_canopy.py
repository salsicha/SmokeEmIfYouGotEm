"""Read-only saved-foliage transform precision audit; never modifies assets."""
import json,math,os,sys,traceback
from pathlib import Path
import unreal
sys.path.insert(0,str(Path(__file__).resolve().parent))
from install_futaleufu_continuous_canopy import ROOT,PLAN,MAP,load_world,foliage_components,sha,original_files,verify
OUT=Path(os.environ.get('RAFTSIM_CANOPY_AUDIT_OUT',str(ROOT/'tmp/futaleufu-saved-canopy-audit-v1')))


def main():
    if OUT.exists():raise RuntimeError('Fresh audit output required')
    OUT.mkdir();plan=json.loads(PLAN.read_text())
    pins={str(p):sha(p) for p in original_files()}
    buckets={}
    for chunk in plan['chunks']:
        for row in chunk['instances']:
            x,y,_=row['location_cm'];key=(row['mesh'],math.floor(x/100),math.floor(y/100))
            buckets.setdefault(key,[]).append(row)
    levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actors=load_world(levels);counts=[0,0,0];maximum=[0.,0.,0.,0.];failures=[];unmatched=0;outside=0
    components=[]
    for actor,c,mesh in foliage_components(actors,[r['asset'] for r in plan['meshes']]):
        components.append(dict(actor=actor.get_path_name(),component=c.get_path_name(),mesh=mesh,count=c.get_instance_count(),
            collision=str(c.get_collision_enabled()),start_cull=c.get_editor_property('instance_start_cull_distance'),
            end_cull=c.get_editor_property('instance_end_cull_distance')))
        for i in range(c.get_instance_count()):
            t=c.get_instance_transform(i,True);v=t.translation;s=t.scale3d;q=t.rotation
            actual=[float(v.x),float(v.y),float(v.z)];scale=[float(s.x),float(s.y),float(s.z)]
            yaw=math.degrees(math.atan2(2*(q.w*q.z+q.x*q.y),1-2*(q.y*q.y+q.z*q.z)))
            nearest=None
            for dx in (-1,0,1):
                for dy in (-1,0,1):
                    key=(mesh,math.floor(v.x/100)+dx,math.floor(v.y/100)+dy)
                    for j,row in enumerate(buckets.get(key,())):
                        error=max(abs(a-b) for a,b in zip(actual,row['location_cm']))
                        if nearest is None or error<nearest[0]:nearest=(error,key,j,row)
            counts[mesh]+=1
            if nearest is None:
                unmatched+=1
                if len(failures)<20:failures.append(dict(actual=actual,mesh=mesh,error='No expected neighbour'))
                continue
            error,key,j,row=nearest;buckets[key].pop(j)
            errors=[error,max(abs(a-b) for a,b in zip(scale,row['scale_xyz'])),
                abs((yaw-row['yaw_deg']+180)%360-180),max(abs(q.x),abs(q.y))]
            maximum=[max(a,b) for a,b in zip(maximum,errors)]
            if any(not math.isfinite(e) or e>limit for e,limit in zip(errors,[1.,1e-5,.001,1e-6])):
                outside+=1
                if len(failures)<20:failures.append(dict(mesh=mesh,actual_location=actual,actual_scale=scale,actual_yaw=yaw,
                    expected=row,errors=errors,component=c.get_path_name(),index=i))
    strict,packages=verify(actors,plan)
    backup=ROOT/'tmp/futaleufu-continuous-canopy-install-v1/backup'
    originals=[p for p in backup.rglob('*') if p.is_file()]
    terrain_stable=bool(originals) and all(sha(p)==sha(ROOT/'unreal/Content'/p.relative_to(backup)) for p in originals)
    result=dict(strict_verification=strict,original_terrain_backup_files=len(originals),original_terrain_matches_backup=terrain_stable,
        instance_counts=counts,maximum_errors=dict(zip(['position_cm','scale','yaw_degrees','tilt_quaternion'],maximum)),
        unmatched=unmatched,outside_original_tolerances=outside,remaining_expected=sum(map(len,buckets.values())),
        examples=failures,components=components,plan_sha256=sha(PLAN),saved_assets=False,
        original_packages_unchanged=all(sha(Path(p))==h for p,h in pins.items()))
    (OUT/'audit.json').write_text(json.dumps(result,indent=2,allow_nan=False))
    if unmatched or outside or result['remaining_expected'] or not terrain_stable or not result['original_packages_unchanged']:
        raise RuntimeError('Saved canopy audit failed; inspect receipt')
    unreal.log('Saved canopy transform audit: '+json.dumps({k:v for k,v in result.items() if k not in ('examples','components')}))
    # No save or world transition is needed for this read-only process. Keep
    # inspected actor/component/package wrappers in their owning world until
    # Python releases them; tearing that world down here is unnecessary.


if OUT.exists():raise RuntimeError('Fresh audit output required; preserve earlier evidence')
try:main()
except Exception:
    OUT.mkdir(parents=True,exist_ok=True);(OUT/'failure.txt').write_text(traceback.format_exc());raise
finally:unreal.SystemLibrary.quit_editor()
