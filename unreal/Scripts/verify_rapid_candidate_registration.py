"""Read-only native registration of hash-bound authored rapid candidates.

Uses the shipping adapter's geographic queries. Does not save maps, change
profiles, infer hydraulic acceptance, or load an alternate physics solver.
"""
import hashlib
import json
import math
import os
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]

def sha(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()

def inside(root,name):
    path=(root/name).resolve()
    path.relative_to(root.resolve())
    return path

def finite(values):
    return all(math.isfinite(v) for v in values)

def xyz(v):return [v.x,v.y,v.z]
def dot(a,b):return sum(x*y for x,y in zip(a,b))

def load_candidate(path):
    candidate=json.loads(path.read_text())
    if candidate.get('schema')!='raftsim.rapid_feature_source_candidate.v1':
        raise ValueError('Unsupported source candidate')
    source=inside(ROOT,candidate['source_directory'])
    expected=candidate['source_sha256']
    if set(expected)!={'coordinate_map.json','reference.npz','scenario/bed.npy'}:
        raise ValueError('Bind all geographic source inputs')
    bound={path:sha(path)}
    for name,digest in expected.items():
        file=inside(source,name)
        if sha(file)!=digest:raise ValueError('Changed candidate source: '+name)
        bound[file]=digest
    if not candidate['features']:raise ValueError('Empty candidate')
    for row in candidate['features']:
        if len(row)!=6 or not finite(row):raise ValueError('Six finite feature values required')
        if not (0<row[3]<=1.2 and 2<=row[4]<=7 and 0<=row[5]<=1):
            raise ValueError('Shared feature bounds exceeded')
    return candidate,source,bound

def main():
    import unreal
    request_path=inside(ROOT,os.environ['RAFTSIM_CANDIDATE_REGISTRATION_REQUEST'])
    request=json.loads(request_path.read_text())
    out=inside(ROOT/'tmp',request['output_under_tmp'])
    if out.exists():raise ValueError('Fresh native output directory required')
    target_path=inside(ROOT,request['target_chart'])
    if sha(target_path)!=request['target_chart_sha256']:raise ValueError('Changed target chart')
    target_map=json.loads(target_path.read_text())
    target_origin=target_map['horizontal_origin_epsg6404_m']
    target=unreal.RaftSimWaterRuntimeAdapter()
    if not target.configure_river_coordinate_map(str(target_path)):raise ValueError('Native target chart refused')
    protected={request_path:sha(request_path),target_path:sha(target_path)}
    out.mkdir(parents=True)
    results=[]
    names=set()
    for entry in request['candidates']:
        path=inside(ROOT,entry['path'])
        if sha(path)!=entry['sha256']:raise ValueError('Changed requested candidate')
        candidate,source,bound=load_candidate(path)
        if candidate['rapid'] in names:raise ValueError('Duplicate rapid')
        names.add(candidate['rapid']);protected.update(bound)
        original_map=json.loads((source/'coordinate_map.json').read_text())
        if original_map['world_y_sign']!=-1 or target_map['world_y_sign']!=-1:
            raise ValueError('Unexpected world orientation')
        if original_map['vertical_reference']!=target_map['vertical_reference']:
            raise ValueError('Vertical reference mismatch')
        origin=original_map['horizontal_origin_epsg6404_m']
        delta=[origin[i]-target_origin[i] for i in range(2)]
        rebased=dict(original_map,horizontal_origin_epsg6404_m=target_origin,
                     vertical_datum_m=target_map['vertical_datum_m'])
        rebased['points']=[[p[0],p[1]+delta[0],p[2]+delta[1],p[3],p[4]] for p in original_map['points']]
        rebased_path=out/(source.name+'-rebased.json')
        rebased_path.write_text(json.dumps(rebased)+'\n')
        protected[rebased_path]=sha(rebased_path)
        native_source=unreal.RaftSimWaterRuntimeAdapter()
        original=unreal.RaftSimWaterRuntimeAdapter()
        if not native_source.configure_river_coordinate_map(str(rebased_path)) or not original.configure_river_coordinate_map(str(source/'coordinate_map.json')):
            raise ValueError('Native source chart refused')
        features=[]
        for row in candidate['features']:
            s,y,angle,height,length,spill=row
            position=native_source.river_to_world_position(unreal.Vector2D(s,y),1000.)
            raw=original.river_to_world_position(unreal.Vector2D(s,y),1000.)
            if position is None or raw is None:raise ValueError('Feature outside source chart')
            expected_xy=[raw.x+100*delta[0],raw.y-100*delta[1]]
            rebase_error=math.hypot(position.x-expected_xy[0],position.y-expected_xy[1])
            src=native_source.world_to_river_coordinates(position)
            dst=target.world_to_river_coordinates(position)
            if src is None or dst is None:raise ValueError('Native inverse registration refused')
            sr,st,sl=src;tr,tt,tl=dst
            if math.hypot(sr.x-s,sr.y-y)>1.e-4:raise ValueError('Ambiguous source inverse')
            check=target.river_to_world_position(tr,1000.)
            if check is None:raise ValueError('Target round trip refused')
            error=math.hypot(check.x-position.x,check.y-position.y)
            radians=math.radians(angle)
            direction=[a*math.cos(radians)+b*math.sin(radians) for a,b in zip(xyz(st),xyz(sl))]
            moved_angle=math.atan2(dot(direction,xyz(tl)),dot(direction,xyz(tt)))
            recovered=[a*math.cos(moved_angle)+b*math.sin(moved_angle) for a,b in zip(xyz(tt),xyz(tl))]
            direction_error=math.sqrt(sum((a-b)**2 for a,b in zip(direction,recovered)))
            transformed=[tr.x,tr.y,math.degrees(moved_angle),height,length,spill]
            if not finite(transformed+[error,rebase_error,direction_error]) or error>1 or rebase_error>.01 or direction_error>1.e-6:
                raise ValueError('Native geographic registration exceeds tolerance')
            features.append(dict(source=row,registered=transformed,centre_error_cm=error,rebase_error_cm=rebase_error,direction_vector_error=direction_error))
        results.append(dict(rapid=candidate['rapid'],candidate=str(path.relative_to(ROOT)),rebased_chart=str(rebased_path.relative_to(ROOT)),features=features))
        del original,native_source
    if not all(sha(path)==digest for path,digest in protected.items()):raise ValueError('Input changed during native test')
    report=dict(schema='raftsim.native_candidate_feature_registration.v1',passed=True,target_chart=request['target_chart'],target_chart_sha256=request['target_chart_sha256'],rapids=results,feature_count=sum(len(r['features']) for r in results),protected_sha256={str(p.relative_to(ROOT)):h for p,h in protected.items()},saved_maps=False,rendered_water_validated=False,boat_motion_validated=False,performance_validated=False)
    with (out/'report.json').open('x') as f:json.dump(report,f,indent=2,allow_nan=False)
    del target
    import gc
    gc.collect()
    unreal.SystemLibrary.collect_garbage()
    unreal.log('Read-only native candidate registration passed: '+str(out/'report.json'))

if __name__=='__main__':
    import unreal
    try:main()
    finally:unreal.SystemLibrary.quit_editor()
