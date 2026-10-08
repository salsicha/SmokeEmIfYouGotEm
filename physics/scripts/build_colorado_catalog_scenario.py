"""Convert a registered construction grid into a real native solver input.

No synthetic class force, current receipt or convergence claim is exported.
The scenario must be cooked, compared to its source profile, and inspected in
the production engine before it can replace any normal-launch content.
"""
import argparse
import copy
import json
from pathlib import Path

import numpy as np
from scipy.interpolate import PchipInterpolator
from scipy.ndimage import map_coordinates
from build_colorado_catalog_evidence import DATA,ROOT,sha
from build_hance_curvilinear_scenario import gauss_smooth
from chilko_native_friction import with_manning_friction

TEMPLATE=DATA/'scenario_hance/low_release_planning/scenario.json'
Q=226.534772736


def frame(profile,step=2.,smoothing_m=60.):
    rows=profile['samples']
    old_s=np.array([r['local_arc_station_m'] for r in rows])
    xy=np.array([[r['easting'],r['northing']] for r in rows])
    if (len(old_s)<2 or not np.isfinite(xy).all() or not np.isfinite(old_s).all() or
        np.any(np.diff(old_s)<=0) or not np.isfinite(step) or step<=0):
        raise ValueError('Invalid source centerline or grid step')
    if old_s[-1]-old_s[0]<4*step:raise ValueError('Insufficient frame length')
    dense_s=np.arange(0,old_s[-1],step)
    dense=PchipInterpolator(old_s,xy,axis=0)(dense_s)
    # This changes only the numerical coordinate chart, NOT the registered
    # bank outline, terrain or surveyed bed. A transect chart following every
    # short survey-line kink folds across a wide river. Resample the original
    # geographic sources on a smooth chart instead of moving the geography.
    if not np.isfinite(smoothing_m) or smoothing_m<0:raise ValueError('Invalid chart smoothing')
    if smoothing_m:
        dense=np.column_stack([gauss_smooth(dense[:,i],smoothing_m/step) for i in range(2)])
    arc=np.r_[0,np.cumsum(np.linalg.norm(np.diff(dense,axis=0),axis=1))]
    if np.any(np.diff(arc)<1e-6):raise ValueError('Degenerate curved grid')
    s=np.arange(0,arc[-1],step)
    x=np.interp(s,arc,dense[:,0]); y=np.interp(s,arc,dense[:,1])
    source_s=np.interp(s,arc,dense_s)
    tangent=np.column_stack([np.gradient(x,step),np.gradient(y,step)])
    tangent/=np.linalg.norm(tangent,axis=1)[:,None]
    normal=np.column_stack([-tangent[:,1],tangent[:,0]])
    curvature=(tangent[:,0]*np.gradient(tangent[:,1],step)-tangent[:,1]*np.gradient(tangent[:,0],step))
    return s,np.column_stack([x,y]),normal,curvature,source_s


def sample_grid(grid,xy,corner,nearest=False):
    rows=corner[1]-xy[...,1]-.5;cols=xy[...,0]-corner[0]-.5
    return map_coordinates(grid.astype(float),[rows,cols],order=0 if nearest else 1,
                           mode='constant',cval=np.nan,prefilter=False)


def checked_roughness(value):
    if not np.isfinite(value) or not .02<=value<=.08:
        raise ValueError('Roughness hypothesis outside bounded sensitivity range')
    return float(value)


def registered_rapid_station(profile, source_s, station):
    value=profile.get('rapid_point_local_station_m')
    if value is None:
        if profile.get('schema')!='raftsim.colorado_continuous_source_window.v1':
            raise ValueError('Named rapid input requires its registered source point')
        return None
    if not np.isfinite(value) or not source_s[0]<=value<=source_s[-1]:
        raise ValueError('Rapid point outside constructed chart; do not clamp its location')
    return float(np.interp(value,source_s,station))


def covered_source_slice(inside, source_station, core=None):
    """Trim exterior halo only; never export a gap or a truncated required core."""
    inside=np.asarray(inside,dtype=bool);source_station=np.asarray(source_station,dtype=float)
    if (inside.ndim!=1 or inside.shape!=source_station.shape or len(inside)<2 or
            not np.isfinite(source_station).all() or np.any(np.diff(source_station)<=0)):
        raise ValueError('Invalid source coverage axis')
    idx=np.flatnonzero(inside)
    if not len(idx):raise ValueError('No completely source-backed cross-sections')
    if core is not None:
        core=np.asarray(core,dtype=float)
        if core.shape!=(2,) or not np.isfinite(core).all() or core[0]>=core[1]:
            raise ValueError('Invalid required source core')
        # A detached valid island beyond a missing EXTERIOR halo is not part
        # of the required run. Select one contiguous complete component that
        # brackets the entire core; never bridge a gap or discard core cells.
        groups=np.split(idx,np.flatnonzero(np.diff(idx)>1)+1)
        complete=[g for g in groups if source_station[g[0]]<=core[0] and source_station[g[-1]]>=core[1]]
        if len(complete)==1:
            return slice(int(complete[0][0]),int(complete[0][-1])+1)
    gaps=np.flatnonzero(~inside[idx[0]:idx[-1]+1])+idx[0]
    if len(gaps):
        raise ValueError(f'Curved strip has missing source/terrain coverage between '
                         f'{source_station[gaps[0]]:.3f} and {source_station[gaps[-1]]:.3f} m; '
                         'expand the registered capture or split the construction window, never fill the gap')
    if core is not None:
        if source_station[idx[0]]>core[0] or source_station[idx[-1]]<core[1]:
            raise ValueError('Source coverage does not bracket the complete required core; do not cook partial coverage')
    return slice(int(idx[0]),int(idx[-1])+1)


def checked_terrain_snapshot(folder,snapshot=None):
    """Borrow a fixed terrain snapshot; batch callers must close with verify_unchanged.

    Candidate receipts always bind the loaded manifest, never a newer on-disk
    manifest. Native export still independently validates every heightfield.
    """
    from export_colorado_continuous_terrain import LandscapeTriangles
    if snapshot is None:return LandscapeTriangles(folder)
    if (not isinstance(snapshot,LandscapeTriangles) or
            snapshot.folder!=Path(folder).resolve() or
            sha(snapshot.folder/'manifest.json')!=snapshot.manifest_sha256):
        raise ValueError('Wrong or changed terrain snapshot')
    return snapshot


def build(evidence,profile_path,water_dir,out,match_landscape=False,roughness=.04,terrain_chunks=None,shared_frame=None,terrain_snapshot=None,reviewed_lateral_interval=None):
    roughness=checked_roughness(roughness)
    if match_landscape and terrain_chunks is not None:
        raise ValueError('Choose legacy Landscape or continuous chunks, not both')
    if terrain_snapshot is not None and terrain_chunks is None:
        raise ValueError('Terrain snapshot requires its registered directory')
    if reviewed_lateral_interval is not None and (shared_frame is None or terrain_chunks is None):
        raise ValueError('Reviewed lateral domains require a shared chart and registered terrain')
    if out.exists():raise ValueError('Fresh solver-input directory required')
    manifest=json.loads((evidence/'manifest.json').read_text())
    if sha(evidence/'evidence_grid.npz')!=manifest['evidence_grid_sha256']:
        raise ValueError('Construction grid changed after composition')
    profile=json.loads(profile_path.read_text())
    if profile['name']!=manifest['name']:raise ValueError('Wrong rapid profile')
    if manifest['source_files_sha256'].get(str(profile_path.relative_to(ROOT)))!=sha(profile_path):
        raise ValueError('Profile changed after composition')
    wm=json.loads((water_dir/'manifest.json').read_text())
    width=next(r for r in wm['windows'] if r['name']==profile['name'])
    if reviewed_lateral_interval is None:
        intervals=[a for row in width['widths'] for a in row['classified_water_intervals_lateral_m']]
        if not intervals or any(w['transect_truncated'] for w in width['widths']):
            raise ValueError('Unbounded or missing water transects')
        half=float(np.ceil((max(abs(v) for a in intervals for v in a)+20)/2)*2)
        if half>250:raise ValueError('Curved strip wider than reviewed 500 m limit')
        lateral=np.arange(-half,half+2.,2.)
    else:
        if profile.get('source_core_interval_m') is None:
            raise ValueError('Reviewed lateral domain requires its complete registered source core')
        from review_colorado_hydraulic_domain import construction_lateral_axis
        lateral=construction_lateral_axis(width,reviewed_lateral_interval)
    g=dict(np.load(evidence/'evidence_grid.npz')); step=2.
    shared_mapping=None;shared_receipt=None;source_caps=None
    if shared_frame is not None:
        if terrain_chunks is None:raise ValueError('Shared hydraulic frame requires common terrain chunks')
        from build_colorado_shared_hydraulic_frame import load
        (station,xy,normal,curvature,source_s),shared_mapping,frame_manifest=load(shared_frame.resolve(),profile)
        if 'source_endpoint_anchor' in frame_manifest:
            source_caps=frame_manifest['source_endpoint_anchor']['source_end_caps']
        shared_receipt=dict(manifest=shared_frame.resolve().relative_to(ROOT).as_posix()+'/manifest.json',
                            sha256=sha(shared_frame/'manifest.json'))
    else:
        station,xy,normal,curvature,source_s=frame(profile,step)
    queries=xy[:,None,:]+normal[:,None,:]*lateral[None,:,None]
    bed=sample_grid(g['bed_ellipsoid_m'],queries,g['corner_east_north_m'])
    terrain_receipt=None
    if terrain_chunks is not None:
        triangles=checked_terrain_snapshot(terrain_chunks,terrain_snapshot)
        source_match=any(
            row['evidence']==evidence.relative_to(ROOT).as_posix() and
            row['evidence_manifest_sha256']==sha(evidence/'manifest.json') and
            row['profile']==profile_path.relative_to(ROOT).as_posix() and
            row['profile_sha256']==sha(profile_path)
            for row in triangles.manifest['source_inputs'])
        if not source_match:raise ValueError('Terrain chunks do not contain this registered construction input')
        bed=np.where(np.isfinite(bed),triangles.sample(queries),np.nan)
        terrain_receipt=dict(manifest=triangles.folder.relative_to(ROOT).as_posix()+'/manifest.json',
                             sha256=triangles.manifest_sha256)
    if match_landscape:
        # Close the geometry handoff: the export's 2017-height Landscape is
        # interpolated once here and the native solver cooks THAT bed. Keeping
        # a separately resampled 1 m bed created isolated 0.98 m disagreements
        # at sharp shores despite a reassuring 1.6 cm p95 error.
        from export_colorado_catalog_runtime import landscape_grid,landscape_sample
        _,rendered,_,_=landscape_grid(g['bed_ellipsoid_m'])
        sy,sx=g['bed_ellipsoid_m'].shape;corner=g['corner_east_north_m']
        ry=(corner[1]-queries[...,1])/sy*2016
        rx=(queries[...,0]-corner[0])/sx*2016
        compatible=landscape_sample(rendered,ry,rx)
        bed=np.where(np.isfinite(bed),compatible,np.nan)
    inside=np.isfinite(bed).all(axis=1)
    source_origin=profile['source_halo_interval_m'][0] if profile.get('source_core_interval_m') is not None else 0.
    take=covered_source_slice(inside,source_s+source_origin,profile.get('source_core_interval_m'))
    queries,bed,xy,normal,curvature,source_s=queries[take],bed[take],xy[take],normal[take],curvature[take],source_s[take]
    station=station[take] if shared_mapping is not None else np.arange(len(xy))*step
    ws=np.interp(source_s,[r['local_arc_station_m'] for r in profile['samples']],
                 [r['ws_nonincreasing'] for r in profile['samples']])
    classified=sample_grid(g['classified_water_mask'],queries,g['corner_east_north_m'],True)>.5
    wet=classified&(ws[:,None]-bed>.02)
    ratio=1-curvature[:,None]*lateral[None,:]
    if not wet.any() or ratio[wet].min()<=.1:
        raise ValueError('Curved wet strip folds or is empty; needs a different registered frame')
    if wet[:,0].any() or wet[:,-1].any():raise ValueError('Water clipped at lateral domain boundary')
    domain_coverage=None
    if reviewed_lateral_interval is not None or (shared_mapping is not None and profile.get('source_core_interval_m') is not None):
        from review_colorado_hydraulic_domain import source_footprint_coverage
        domain_coverage=source_footprint_coverage(g,profile,xy,normal,lateral,end_caps=source_caps)
        if not domain_coverage['complete_classified_core_coverage']:
            raise ValueError('Reviewed chart omits '+str(domain_coverage['uncovered_classified_source_core_cells'])+
                             ' classified source-core water cells; never remove an off-chart channel')
    depth=np.where(wet,ws[:,None]-bed,0.)
    conveyance=(depth**(5/3)).sum(axis=1)*step
    if np.any(conveyance<=0):raise ValueError('Dry cross-section disconnects the hydraulic domain')
    velocity=np.where(wet,Q*depth**(2/3)/conveyance[:,None],0.)
    if not np.isfinite(velocity).all():raise ValueError('Nonfinite initial state')
    B=np.ascontiguousarray(bed.T);h=np.ascontiguousarray(depth.T);u=np.ascontiguousarray(velocity.T)
    v=np.zeros_like(u)
    initial_q=(h*u).sum(axis=0)*step
    if not np.allclose(initial_q,Q):raise ValueError('Initial discharge does not match requested flow')
    inlet=h[:,0];active=inlet>=.15
    if not active.any():raise ValueError('No resolved inflow channel')
    inlet_u=np.where(active,Q*inlet**(2/3)/(np.where(active,inlet,0)**(5/3)).sum()/step,0.)
    ghost=np.column_stack([B[:,0],inlet,inlet_u,np.zeros_like(inlet)])
    scenario=copy.deepcopy(json.loads(TEMPLATE.read_text()))
    scenario.update(grid=dict(nx=len(station),ny=len(lateral),dx=step,dy=step,origin_x=float(station[0]),origin_y=float(lateral[0])),
        roughness=roughness,fixed_dt=.05,duration=600.,feature_count=0,probe_count=0)
    scenario['boundaries']=[dict(edge='west',kind='discharge_profile',ghost_cells=np.tile(ghost,(2,1)).tolist(),
        metadata=dict(target_discharge_m3s=Q,distribution='h^(5/3) initial conveyance hypothesis')),
        dict(edge='east',kind='outflow',stage=float(ws[-1])),dict(edge='south',kind='bank'),dict(edge='north',kind='bank')]
    key=profile_path.stem
    scenario['metadata']=dict(scenario_id='colorado_catalog_'+key,scenario_type='real_world',fixture_kind=None,
        river_id='colorado_river_grand_canyon_rowing',flow_band='steady_8000cfs_2021',seed=1,
        generator='build_colorado_catalog_scenario.py',generator_version='20261006-v1',
        description='Registered source terrain and water outline; surveyed pool bed; labelled inferred rapid bed. Pending cook and engine calibration.',
        confidence_score=.25,coordinate_reference_system='curved station/river-left grid in EPSG:6404; ellipsoid metres',
        provenance=dict(construction_manifest_sha256=sha(evidence/'manifest.json'),profile_sha256=sha(profile_path),
            target_discharge_m3s=Q,measured_velocity=False,rapid_obstacles_validated=False))
    # New continuous-corridor resistance is inferred Manning n. The native
    # damping field is g*n*n, not n. Leave existing standalone legacy builds
    # and already cooked packages unchanged; never convert at runtime twice.
    if shared_mapping is not None:
        scenario=with_manning_friction(scenario,roughness)
    datum=float(np.floor(ws.min()/10)*10)
    origin=[float(g['corner_east_north_m'][0]),float(g['corner_east_north_m'][1]-g['bed_ellipsoid_m'].shape[0]/2)]
    mapping=dict(schema='raftsim.curved_river_coordinate_map.v1',river_id='colorado_river',section_id='catalog_'+key,
        world_y_sign=-1,vertical_datum_m=datum,horizontal_origin_epsg6404_m=origin,
        vertical_reference='NAD83(2011) ellipsoid heights',
        mapping_policy='60 m Gaussian-smoothed numerical chart, reparameterised at 2 m arc; geographic terrain and banks resampled unchanged',
        points=np.column_stack([station,xy-np.array(origin),normal]).tolist())
    if shared_mapping is not None:mapping=shared_mapping
    out.mkdir(parents=True);pkg=out/'scenario';pkg.mkdir()
    np.save(pkg/'bed.npy',B)
    np.savez_compressed(pkg/'initial_state.npz',depth=h,eta=B+h,u=u,v=v,hu=h*u,hv=h*v,wet=h>1e-6)
    for name in ('features','probes'):(pkg/(name+'.json')).write_text(json.dumps({name:[]})+'\n')
    (pkg/'scenario.json').write_text(json.dumps(scenario,indent=2)+'\n')
    # The complete shared river chart is large and repeated in each standalone
    # input. Compact JSON retains every coordinate without hundreds of copies
    # of presentation whitespace or mutable cross-package hardlinks.
    (out/'coordinate_map.json').write_text(json.dumps(mapping,separators=(',',':'))+'\n')
    np.savez_compressed(out/'reference.npz',station=station,lateral=lateral,source_station=source_s,
        reference_surface=ws,classified_water=classified.T,metric_ratio=ratio.T,
        class_code=sample_grid(g['class_code'],queries,g['corner_east_north_m'],True).T.astype('uint8'))
    receipt=dict(schema='raftsim.colorado_catalog_solver_input.v1',name=profile['name'],grid=scenario['grid'],
        construction_directory=str(evidence.relative_to(ROOT)),source_profile=str(profile_path.relative_to(ROOT)),
        source_station_range_m=[float(source_s[0]),float(source_s[-1])],
        rapid_point_station_m=registered_rapid_station(profile,source_s,station),
        source_core_interval_m=profile.get('source_core_interval_m'),
        source_halo_interval_m=profile.get('source_halo_interval_m'),
        initial_discharge_range_m3s=[float(initial_q.min()),float(initial_q.max())],
        wet_metric_ratio_range=[float(ratio[wet].min()),float(ratio[wet].max())],
        metric_warning='Native solver has no curvilinear metric terms; inspect physical-space current continuity on bends.',
        maximum_initial_speed_mps=float(u.max()),minimum_reference_surface_m=float(ws.min()),
        bed_sampling_policy=('common geographic 2 m Landscape Chaos triangle reference' if terrain_chunks is not None
                             else '2017 quantized Landscape Chaos triangle reference' if match_landscape
                             else '1 m construction grid bilinear reference'),
        continuous_terrain=terrain_receipt,
        shared_hydraulic_frame=shared_receipt,
        roughness_hypothesis=roughness,
        roughness_scope='Uniform modelling parameter, not a measured resistance; compare discharge, settling, stage and wet footprint after every cook.',
        landscape_collision_triangles_validated=False,
        files_sha256={str(p.relative_to(out)):sha(p) for p in out.rglob('*') if p.is_file()},
        solved=False,playable_map_created=False,accepted=False)
    if shared_mapping is not None:
        receipt['friction']=scenario['metadata']['provenance']['friction']
        receipt['roughness_scope']='Inferred Manning n; scenario stores g*n*n. Not measured; requires fresh native and engine validation.'
    if domain_coverage is not None:receipt['source_core_coverage']=domain_coverage
    if reviewed_lateral_interval is not None:
        receipt['reviewed_lateral_domain']=dict(lateral_interval_m=[float(lateral[0]),float(lateral[-1])],
            original_symmetric_transects_truncated=any(w['transect_truncated'] for w in width['widths']),
            source_coverage=domain_coverage,wet_edges_dry=True,wet_folding_gate_passed=True,
            policy='Explicit bounded domain; unchanged 500 m total-width, full source-core, terrain, wet-edge and wet-folding gates')
    (out/'build_report.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps({k:v for k,v in receipt.items() if k!='files_sha256'},indent=2),flush=True)
    return receipt


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--evidence',type=Path,required=True);p.add_argument('--profile',type=Path,required=True)
    p.add_argument('--water',type=Path,default=DATA/'catalog_water_windows_2026_10_v2')
    p.add_argument('--out',type=Path,required=True)
    terrain_group=p.add_mutually_exclusive_group()
    terrain_group.add_argument('--match-landscape',action='store_true')
    terrain_group.add_argument('--terrain-chunks',type=Path)
    p.add_argument('--shared-frame',type=Path)
    p.add_argument('--roughness',type=float,default=.04)
    p.add_argument('--reviewed-lateral-interval',type=float,nargs=2,metavar=('MIN','MAX'))
    a=p.parse_args();build(a.evidence.resolve(),a.profile.resolve(),a.water.resolve(),a.out.resolve(),a.match_landscape,a.roughness,a.terrain_chunks,a.shared_frame,reviewed_lateral_interval=a.reviewed_lateral_interval)
