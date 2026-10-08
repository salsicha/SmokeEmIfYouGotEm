"""Verify a construction window is an exact slice of complete river inputs."""
import argparse
import json
from pathlib import Path

import numpy as np

from review_chilko_continuous_cook import read_inputs
from audit_chilko_corridor_bed import longest_supported_width
from mosaic_lidarbc_crops import sha


def verify(full,window,out):
    full,window,out=map(Path,(full,window,out))
    if out.exists():raise ValueError('Fresh verification output required')
    b,s,m,_,bed,r,hashes=read_inputs(full)
    wb,ws,wm,_,wbed,wr,whashes=read_inputs(window)
    if not b['full_route_hydraulic_inputs'] or wb['full_route_hydraulic_inputs']:
        raise ValueError('Full-domain input and local construction window required')
    indices=np.searchsorted(r['station'],wr['station'])
    if np.any(indices>=len(r['station'])):raise ValueError('Window exceeds full chart')
    np.testing.assert_array_equal(r['station'][indices],wr['station'])
    if m!=wm:raise ValueError('Full and local numerical charts differ')
    np.testing.assert_array_equal(bed[:,indices],wbed)
    if r.keys()!=wr.keys():raise ValueError('Full and local source fields differ')
    for key,value in r.items():
        if value.shape==bed.shape:expected=value[:,indices]
        elif value.shape==r['station'].shape:expected=value[indices]
        else:expected=value
        np.testing.assert_array_equal(expected,wr[key])
    with np.load(full/'scenario/initial_state.npz',allow_pickle=False) as initial, np.load(window/'scenario/initial_state.npz',allow_pickle=False) as wi:
        if set(initial.files)!=set(wi.files):raise ValueError('Initial state fields differ')
        for key in initial.files:np.testing.assert_array_equal(initial[key][:,indices],wi[key])
        spans=np.array([longest_supported_width(row>=.3) for row in initial['depth'].T])
    deficient=np.flatnonzero(spans<4.)
    clearance=dict(minimum_depth_m=.3,minimum_point_span_m=4.,lateral_spacing_m=2.,
        span_percentiles_m=np.percentile(spans,[0,5,50,95,100]).tolist(),
        deficient_sections=[dict(numerical_station_m=float(r['station'][i]),
            nearest_source_station_m=float(r['evidence_station'][i]),point_span_m=float(spans[i])) for i in deficient],
        scope='Initial per-cell source-stage point clearance only; not boat footprint or solved navigation')
    for folder,expected in ((full,hashes),(window,whashes)):
        if not all(sha(folder/name)==digest for name,digest in expected.items()):
            raise ValueError('Input changed during independent verification')
    result=dict(schema='raftsim.chilko_full_window_verification.v1',full_inputs_sha256=hashes,
        window_inputs_sha256=whashes,terrain_manifest_sha256=b['continuous_terrain']['manifest_sha256'],
        full_grid=s['grid'],window_grid=ws['grid'],source_geometry_independently_verified=True,
        source_masks_and_cell_stages_verified=True,bed_matches_encoded_triangles=True,
        local_initial_state_and_reference_exact_full_slice=True,initial_point_clearance=clearance,
        engine_validated=False,hydraulic_solution=False)
    out.parent.mkdir(parents=True,exist_ok=True)
    with out.open('x',encoding='utf-8') as stream:json.dump(result,stream,indent=2,allow_nan=False)
    print(json.dumps(dict(full_shape=list(bed.shape),window_shape=list(wbed.shape),
        minimum_clearance_span_m=float(spans.min()),deficient_sections=len(deficient),
        source_and_slice_verification_passed=True,initial_point_clearance_passed=len(deficient)==0)))
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('full','window','out'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();verify(a.full,a.window,a.out)
