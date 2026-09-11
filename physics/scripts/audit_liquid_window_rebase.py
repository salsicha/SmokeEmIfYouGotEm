"""Independently verify a coordinate-only recentered terrain/hydraulic package."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[2]


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def audit(work,window):
    g=json.loads((work/'geometry/manifest.json').read_text())
    manifest=json.loads((window/'manifest.json').read_text())
    old=ROOT/g['parent_mesh_path'];new=ROOT/g['mesh_path']
    if sha(old)!=g['parent_mesh_sha256'] or sha(new)!=g['mesh_sha256']:
        raise ValueError('Mesh provenance mismatch')
    offset=np.array(g['parent_frame_offset_east_north_m'])
    errors={};same={}
    with np.load(old) as a,np.load(new) as b:
        if set(a.files)!=set(b.files):raise ValueError('Rebase changed mesh schema')
        coordinate_axes={'east_m':0,'north_m':1,'nominal_east_axis_m':0,'nominal_north_axis_m':1}
        for name in a.files:
            if name in coordinate_axes:errors[name]=float(np.max(abs(a[name]-(b[name]+offset[coordinate_axes[name]]))))
            else:same[name]=bool(np.array_equal(a[name],b[name]))
    flow=json.loads((work/'engine_review/manifest.json').read_text())
    original=ROOT/'tmp/south-fork-survey-hydraulics/1m-mixed-inlet-registered-rock-xy-20260907'
    parent=json.loads((original/'engine_review/manifest.json').read_text())
    arrays={}
    for index,band in enumerate(flow['bands']):
        for name,record in band['arrays'].items():
            previous=parent['bands'][index]['arrays'][name]
            arrays[f'{index}:{name}']=sha(work/'engine_review'/record['file'])==previous['sha256']==sha(original/'engine_review'/previous['file'])
    shift=np.array(flow['review']['parent_frame_offset_station_lateral_m'])
    reg=json.loads((work/'registration.json').read_text());r=np.column_stack([reg['downstream_unit'],reg['left_unit']])
    origin_equal=np.allclose(np.array(g['origin_utm_m'])-offset,json.loads((ROOT/'tmp/south-fork-rock-return-xy-candidate-v2-20260907/manifest.json').read_text())['origin_utm_m'],atol=1e-8,rtol=0)
    grid=flow['grid'];pgrid=parent['grid']
    frame_equal=np.allclose(r@shift,offset,atol=1e-12) and origin_equal and all(
        abs(grid[key]+shift[axis]-pgrid[key])<1e-12 for key,axis in [('origin_x_m',0),('origin_y_m',1)])
    coordinate=json.loads((work/'engine_review/coordinate_map.json').read_text())
    previous=json.loads((original/'engine_review/coordinate_map.json').read_text())
    points=np.array(coordinate['points']);before=np.array(previous['points'])
    points[:,:3]+=np.r_[shift[0],offset]
    coordinate_error=float(np.max(abs(points-before)))
    profile_hashes={name:sha(window/name) for name in ('native_source_profile.json','hydraulic_initial_state.json',
        'triangle_contact_profile.json','grid_boundary_profile.json','grid_vector_boundary_profile.json')}
    source=json.loads((window/'native_source_profile.json').read_text())
    initial=json.loads((window/'hydraulic_initial_state.json').read_text())
    contacts=json.loads((window/'triangle_contact_profile.json').read_text())
    consistent=all(p['source_geometry_sha256']==g['mesh_sha256'] for p in (manifest,source,initial,contacts))
    control=np.array([-9.,1.])@r
    shelf=control+[-2,0];plunge=control+[5,0]
    checks=dict(mesh_xy_restored=max(errors.values())<1e-12,all_other_mesh_arrays_exact=all(same.values()),
        hydraulic_array_bytes_exact=all(arrays.values()),rigid_coordinate_frame_consistent=bool(frame_equal),
        coordinate_map_restored=coordinate_error<1e-12,profile_geometry_consistent=consistent,
        both_control_centres_inside=bool((abs(shelf-shift)<10.5).all() and (abs(plunge-shift)<10.5).all()))
    return dict(checks=checks,coordinate_rebase_verified=all(checks.values()),shift_station_lateral_m=shift.tolist(),
        shift_east_north_m=offset.tolist(),xy_roundtrip_max_errors_m=errors,non_coordinate_arrays_exact=same,
        hydraulic_arrays_exact=arrays,coordinate_map_max_error_m=coordinate_error,
        original_hypothesized_shelf_station_lateral_m=shelf.tolist(),
        original_hypothesized_plunge_station_lateral_m=plunge.tolist(),
        new_hypothesized_shelf_station_lateral_m=(shelf-shift).tolist(),
        new_hypothesized_plunge_station_lateral_m=(plunge-shift).tolist(),
        old_plunge_centre_outside=bool((abs(plunge)>10.5).any()),
        profile_sha256=profile_hashes,physical_domain_size_m=[21,21,8],new_hydraulic_solve=False,
        submerged_control_measured=False,production_promoted=False,
        physics_or_appearance_accepted=False)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--work',type=Path,required=True)
    parser.add_argument('--window',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();result=audit(args.work.resolve(),args.window.resolve())
    with args.output.open('x') as stream:json.dump(result,stream,indent=2);stream.write('\n')
    print(json.dumps(result,indent=2));raise SystemExit(0 if result['coordinate_rebase_verified'] else 1)
