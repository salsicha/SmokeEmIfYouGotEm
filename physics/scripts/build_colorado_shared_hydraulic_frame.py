"""One numerical river frame for every continuous source window.

Smoothing is performed once on the full captured profile, never independently
at tile edges. Bed, shores and measured rapid coordinates remain geographic.
This removes chart-reset errors; it does not prove a cooked water handoff or
make the native solver's missing curvilinear metric terms disappear.
"""
import argparse
import json
from pathlib import Path

import numpy as np

from build_colorado_catalog_windows import DEFAULT_SOURCE, PROFILE, read_profile
from build_colorado_catalog_evidence import ROOT, sha
from build_colorado_catalog_scenario import frame
from build_colorado_continuous_assembly import native_progress_points


def shared_frame(rows):
    xy=np.array([[r['easting'],r['northing']] for r in rows],dtype=float)
    if len(xy)<2 or not np.isfinite(xy).all():raise ValueError('Invalid source polyline')
    distance=np.linalg.norm(np.diff(xy,axis=0),axis=1)
    if np.any(distance<=0) or np.any(distance>40):raise ValueError('Disconnected source polyline')
    source_station=np.r_[0,np.cumsum(distance)]
    profile=dict(samples=[dict(r,local_arc_station_m=float(s)) for r,s in zip(rows,source_station)])
    station,xy,normal,curvature,source=frame(profile)
    return dict(station_m=station,east_north_m=xy,normal_east_north=normal,
                curvature_per_m=curvature,source_global_station_m=source)


def select_window(arrays,profile):
    if profile.get('schema')!='raftsim.colorado_continuous_source_window.v1':
        raise ValueError('Shared frame requires a continuous source window')
    lo,hi=profile['source_halo_interval_m']
    source=arrays['source_global_station_m']
    select=(source>=lo)&(source<=hi)
    if select.sum()<3:raise ValueError('No complete shared-frame window')
    return (arrays['station_m'][select],arrays['east_north_m'][select],
            arrays['normal_east_north'][select],arrays['curvature_per_m'][select],source[select]-lo)


def load(directory,profile):
    m=json.loads((directory/'manifest.json').read_text())
    if m.get('schema')!='raftsim.colorado_shared_hydraulic_frame.v1':raise ValueError('Unexpected frame')
    for name in ('frame.npz','coordinate_map.json'):
        if sha(directory/name)!=m['files_sha256'][name]:raise ValueError('Changed shared frame')
    original=ROOT/m['source_profile']
    if sha(original)!=m['source_profile_sha256']:raise ValueError('Changed captured source profile')
    arrays=dict(np.load(directory/'frame.npz',allow_pickle=False))
    return select_window(arrays,profile),json.loads((directory/'coordinate_map.json').read_text()),m


def build(source,index_path,route_path,out):
    if out.exists():raise ValueError('Fresh shared-frame output required')
    source=source.resolve();index=json.loads(index_path.read_text());route=json.loads(route_path.read_text())
    if (index['source_profile_sha256']!=sha(source) or index['source_rights']!='CC0 1.0 Universal' or
            route.get('world_y_sign')!=-1 or route.get('vertical_reference')!='NAD83(2011) ellipsoid heights'):
        raise ValueError('Source identity, rights or common world frame mismatch')
    arrays=shared_frame(read_profile(source))
    origin=np.array(route['horizontal_origin_epsg6404_m'])
    mapping=dict(schema='raftsim.curved_river_coordinate_map.v1',river_id='colorado_river',
        section_id='colorado_continuous',world_y_sign=-1,vertical_datum_m=route['vertical_datum_m'],
        horizontal_origin_epsg6404_m=origin.tolist(),vertical_reference=route['vertical_reference'],
        mapping_policy='One full-source 60 m Gaussian numerical chart; all tile queries share its 2 m station lattice',
        points=native_progress_points(arrays['station_m'],arrays['east_north_m'],arrays['normal_east_north'],origin))
    out.mkdir(parents=True)
    np.savez_compressed(out/'frame.npz',**arrays)
    (out/'coordinate_map.json').write_text(json.dumps(mapping,separators=(',',':'),allow_nan=False)+'\n')
    receipt=dict(schema='raftsim.colorado_shared_hydraulic_frame.v1',
        source_profile=source.relative_to(ROOT).as_posix(),source_profile_sha256=sha(source),
        source_index_sha256=sha(index_path),world_route_sha256=sha(route_path),
        grid_step_m=2.,hydraulic_station_range_m=[float(arrays['station_m'][0]),float(arrays['station_m'][-1])],
        source_station_range_m=[float(arrays['source_global_station_m'][0]),float(arrays['source_global_station_m'][-1])],
        files_sha256={name:sha(out/name) for name in ('frame.npz','coordinate_map.json')},
        limitations=['Curvilinear metric terms remain absent from the native solver.',
                    'Each wet window must independently pass the no-folding and geographic coverage checks.',
                    'Neither cooked handoff, terrain collision, normal launch nor boat descent is validated here.'],
        runtime_ready=False)
    (out/'manifest.json').write_text(json.dumps(receipt,indent=2)+'\n')
    return receipt


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',type=Path,default=DEFAULT_SOURCE/PROFILE)
    p.add_argument('--source-index',type=Path,required=True)
    p.add_argument('--world-route',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();print(json.dumps(build(a.source,a.source_index,a.world_route,a.out),indent=2))
