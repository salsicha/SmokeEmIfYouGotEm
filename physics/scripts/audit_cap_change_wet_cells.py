"""Check whether a cap revision changes wet hydraulic cells; never transfer state."""
import argparse
import json
from pathlib import Path
import numpy as np
from south_fork_rock_union import SourceRockUnion,sha
from prepare_south_fork_rock_union_geometry import union_fields,FIELDS,ROOT


def impact(old_bed,new_bed,depth):
    old_bed,new_bed,depth=(np.asarray(a) for a in (old_bed,new_bed,depth))
    if old_bed.shape!=new_bed.shape or depth.shape!=old_bed.shape or not all(np.isfinite(a).all() for a in (old_bed,new_bed,depth)) or np.any(depth<0):
        raise ValueError('Finite matching beds and nonnegative depth required')
    delta=new_bed-old_bed;changed=delta!=0
    return dict(changed_cells=int(changed.sum()),changed_wet_cells=int((changed&(depth>1e-6)).sum()),
        changed_positive_depth_cells=int((changed&(depth>0)).sum()),
        bed_delta_min_max_m=[float(delta.min()),float(delta.max())],
        changed_cell_depth_min_max_m=[float(depth[changed].min()),float(depth[changed].max())] if changed.any() else None)


def run(cook,step,candidate_manifest,output):
    if output.exists():raise ValueError('Fresh report required')
    flow_path=Path((cook/'input_manifest_path.txt').read_text().strip())
    if not flow_path.is_absolute():flow_path=ROOT/flow_path
    if sha(flow_path)!=sha(cook/'input_manifest.json'):raise ValueError('Cook input changed')
    flow=json.loads(flow_path.read_text());geometry_path=ROOT/flow['geometry_manifest']
    if sha(geometry_path)!=flow['geometry_manifest_sha256']:raise ValueError('Cook geometry changed')
    geometry=json.loads(geometry_path.read_text())
    if flow['packages']!=[r['name'] for r in geometry['regions']]:raise ValueError('Core order changed')
    frame=cook/f'frame_{step:06d}'
    complete=json.loads((frame/'complete.json').read_text())
    if complete['step']!=step or complete['snapshot'] is not True:raise ValueError('Completed snapshot required')
    h=np.load(frame/'h.npy',mmap_mode='r',allow_pickle=False)
    if h.shape!=(80*len(flow['packages']),80) or not np.isfinite(h).all() or np.any(h<0):raise ValueError('Invalid hydraulic depth')
    cap_paths=[ROOT/geometry['rock_cap_manifest'],candidate_manifest.resolve()]
    unions=[]
    for path in cap_paths:
        cap=json.loads(path.read_text());origin=cap['origin_utm_and_vertical_datum_m']
        unions.append(SourceRockUnion(path,ROOT,ROOT/cap['source_mesh_path'],origin[:2],origin[2],ROOT/geometry['terrain_revision_manifest']))
    if unions[0].identity!=geometry['terrain_union']:raise ValueError('Current hydraulic union differs')
    cap_xyz=np.concatenate([u.xyz[:,:2]+u.origin[:2] for u in unions])
    lower,upper=cap_xyz.min(0),cap_xyz.max(0)
    rows=[]
    for index,record in enumerate(geometry['regions']):
        center=np.asarray(record['center_utm_m'])
        if np.any(center+39<lower) or np.any(center-40>upper):continue
        source_path=ROOT/record['source_geometry_file'];actual_path=ROOT/record['geometry_file']
        if sha(source_path)!=record['source_geometry_sha256'] or sha(actual_path)!=record['geometry_sha256']:raise ValueError('Hydraulic source packet changed')
        row,col=record['source_slice_row_column']
        with np.load(source_path,allow_pickle=False) as data:
            fields={key:data[key][row:row+80,col:col+80] for key in FIELDS}
        old,new=[union_fields(fields,center,u)[0] for u in unions]
        with np.load(actual_path,allow_pickle=False) as data:
            if any(not np.array_equal(data[key],old[key]) for key in FIELDS):raise ValueError('Independent union does not reproduce existing bed')
        rows.append(dict(core=record['name'],**impact(old['bed_navd88_m'],new['bed_navd88_m'],h[index*80:(index+1)*80])))
    report=dict(schema='raftsim.cap_change_wet_cells.v1',input_manifest_sha256=sha(flow_path),
        geometry_manifest_sha256=sha(geometry_path),candidate_manifest_sha256=sha(candidate_manifest),
        snapshot_step=step,time_seconds=complete['time_seconds'],h_sha256=sha(frame/'h.npy'),
        complete_sha256=sha(frame/'complete.json'),all_intersecting_cores=rows,
        changed_wet_cells=sum(r['changed_wet_cells'] for r in rows),
        changed_positive_depth_cells=sum(r['changed_positive_depth_cells'] for r in rows),
        state_transfer_permitted=False,normal_play_changed=False,visual_or_physical_accepted=False)
    output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('cook',type=Path);p.add_argument('step',type=int)
    p.add_argument('--candidate',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();run(a.cook,a.step,a.candidate,a.output)
