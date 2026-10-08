"""Inspect source agreement and exact native face fluxes; never grade difficulty."""
import argparse
import json
from pathlib import Path
import numpy as np
from scipy.ndimage import distance_transform_edt
from build_colorado_catalog_evidence import ROOT,sha
from solver_face_discharge import face_discharge
from chilko_native_friction import validate_friction
from native_frame_io import load_frame, native_frame_paths, NativeFrameStore


def compare(reference,final,previous,step):
    wet=final['h']>.05; source=reference['classified_water'].astype(bool)
    both=wet&source; union=wet|source
    if not both.any():raise ValueError('No water in common with classified source')
    surface=np.asarray(reference['reference_surface'])
    if surface.shape==(source.shape[1],):surface=np.broadcast_to(surface[None,:],source.shape)
    if surface.shape!=source.shape or not np.isfinite(surface[both]).all():
        raise ValueError('Reference surface must match physical wet cells or station columns')
    delta=np.where(both,final['eta']-surface,np.nan)
    # Leave empty sections missing, never treat their water-height error as zero.
    med=np.array([np.median(delta[:,i][both[:,i]]) if both[:,i].any() else np.nan
                  for i in range(delta.shape[1])])
    available=med[np.isfinite(med)]
    edge_distance=distance_transform_edt(~source)*step
    changing=wet|(previous['h']>.05)
    return dict(wet_intersection_over_union=float(both.sum()/union.sum()),
        extra_wet_cells=int((wet&~source).sum()),
        extra_wet_cells_over_4m_from_source=int((wet&~source&(edge_distance>4)).sum()),
        missing_source_water_cells=int((source&~wet).sum()),
        surface_sections_sampled=int(len(available)),surface_sections_missing=int((~np.isfinite(med)).sum()),
        surface_error_median_m=float(np.median(available)),
        surface_error_abs_p95_m=float(np.percentile(np.abs(available),95)),
        depth_change_p95_m=float(np.percentile(np.abs(final['h']-previous['h'])[changing],95)),
        depth_change_max_m=float(np.abs(final['h']-previous['h'])[changing].max()),
        maximum_speed_mps=float(np.hypot(final['u'],final['v'])[wet].max()),
        maximum_depth_m=float(final['h'].max()),
        sampled_reference_station_m=reference['station'].tolist(),
        surface_error_per_station_m=[float(v) if np.isfinite(v) else None for v in med])


def screen(stats):
    return dict(surface_abs_p95_below_1m=stats['surface_error_abs_p95_m']<1.,
        wet_iou_at_least_point9=stats['wet_intersection_over_union']>=.9,
        discharge_abs_p95_below_5percent=stats['exact_face_discharge_abs_error_p95_fraction']<.05,
        settling_depth_p95_below_3cm=stats['depth_change_p95_m']<.03)


def core_reviews(reference,current,previous,flux,q,step,intervals):
    """A long joined domain must not average away a failing source core."""
    results=[]
    source=np.asarray(reference['source_station'])
    if (source.ndim!=1 or source.size<2 or not np.isfinite(source).all()
            or np.any(np.diff(source)<=0)):
        raise ValueError('Invalid station coverage for registered core')
    for start,end in intervals:
        # An overlap is not coverage of the whole registered reach. Require
        # source samples bracketing both endpoints before evaluating its cells.
        if (not np.isfinite([start,end]).all() or start>=end
                or start<source[0] or end>source[-1]):
            raise ValueError('Incomplete endpoint coverage for registered core')
        columns=np.flatnonzero((source>=start)&(source<end))
        if len(columns)<2 or np.any(np.diff(columns)!=1):
            raise ValueError('Missing or disconnected registered core')
        sl=slice(columns[0],columns[-1]+1)
        surface=np.asarray(reference['reference_surface'])
        ref=dict(station=reference['station'][sl],reference_surface=surface[:,sl] if surface.ndim==2 else surface[sl],
                 classified_water=reference['classified_water'][:,sl])
        stats=compare(ref,{k:v[:,sl] for k,v in current.items()},
                      {k:v[:,sl] for k,v in previous.items()},step)
        local_flux=flux[columns[0]:columns[-1]+2]
        stats['exact_face_discharge_abs_error_p95_fraction']=float(np.percentile(abs(local_flux-q)/q,95))
        gates=screen(stats)
        results.append(dict(source_core_interval_m=[start,end],construction_screen=gates,
            construction_screen_passed=all(gates.values()),
            statistics={k:v for k,v in stats.items() if k not in
                        ('sampled_reference_station_m','surface_error_per_station_m')}))
    return results


def validate_native_source(native, validation, scenario):
    friction=scenario.get('metadata',{}).get('provenance',{}).get('friction')
    if friction is not None:validate_friction(scenario,friction['inferred_manning_n'])
    expected=dict(solver_mode='finite_volume',boundary_mode='scenario',flux_scheme='hll',
        spatial_order=2,cfl=.2,feature_strength_scale=0,roughness_scale=1,
        bed_slope_source_scale=1,preserve_initial_mass=False,disable_fixture_calibrations=True,
        experimental_west_discharge_m3s=-1,experimental_west_supercritical_stage=False,
        scenario_id=scenario['metadata']['scenario_id'])
    if any(native.get(k)!=v for k,v in expected.items()):
        raise ValueError('Unreviewed native configuration or scenario')
    if (validation.get('passed') is not True or validation.get('finite_state') is not True
            or validation.get('velocity_limit_reached') is not False):
        raise ValueError('Native validation failed')


def validate_native_frame(frame, bed, grid, initial=None, max_points=262144):
    shape=(grid['ny'],grid['nx'])
    if bed.shape!=shape or min(shape)<=0:
        raise ValueError('Invalid native bed shape or values')
    for key in ('x','y','h','eta','u','v','hu','hv','wet'):
        if frame[key].shape!=shape:
            raise ValueError('Invalid native frame shape or values')
    if type(max_points) is not int or max_points<shape[1]:
        raise ValueError('Invalid native frame validation block budget')
    row_count=max_points//shape[1]
    expected_x=grid['origin_x']+np.arange(shape[1])*grid['dx']
    for start in range(0,shape[0],row_count):
        sl=slice(start,min(shape[0],start+row_count))
        if not np.isfinite(bed[sl]).all():raise ValueError('Invalid native bed shape or values')
        if any(not np.isfinite(frame[key][sl]).all() for key in ('x','y','h','eta','u','v','hu','hv','wet')):
            raise ValueError('Invalid native frame shape or values')
        expected_y=grid['origin_y']+np.arange(sl.start,sl.stop)[:,None]*grid['dy']
        if (np.any(frame['h'][sl]<0) or not np.isin(frame['wet'][sl],[0,1]).all()
                or not np.allclose(frame['x'][sl],expected_x[None,:],atol=1e-7,rtol=0)
                or not np.allclose(frame['y'][sl],expected_y,atol=1e-7,rtol=0)
                or not np.allclose(frame['eta'][sl]-frame['h'][sl],bed[sl],atol=1e-6,rtol=0)):
            raise ValueError('Native frame differs from input grid or bed')
    if initial is not None:
        for field,key in [('h','depth'),('eta','eta'),('u','u'),('v','v'),('hu','hu'),('hv','hv'),('wet','wet')]:
            saved=initial[key]
            if saved.shape!=shape:raise ValueError('Native first frame differs from saved initial state')
            for start in range(0,shape[0],row_count):
                sl=slice(start,start+row_count)
                if not np.allclose(frame[field][sl],saved[sl],atol=1e-6,rtol=0):
                    raise ValueError('Native first frame differs from saved initial state')
            del saved


def review(inputs,cook,solver,out):
    if out.exists():raise ValueError('Fresh review directory required')
    out.parent.mkdir(parents=True,exist_ok=True)
    with NativeFrameStore(out.parent) as store:
        return _review(inputs,cook,solver,out,store.load)


def _review(inputs,cook,solver,out,frame_loader):
    if out.exists():raise ValueError('Fresh review directory required')
    build=json.loads((inputs/'build_report.json').read_text())
    for name,digest in build['files_sha256'].items():
        if sha(inputs/name)!=digest:raise ValueError('Solver input changed')
    reference=dict(np.load(inputs/'reference.npz'))
    native=json.loads((cook/'manifest.json').read_text())
    frames=native_frame_paths(cook,native,minimum=3)
    validation=json.loads((cook/'validation.json').read_text())
    scenario=json.loads((inputs/'scenario/scenario.json').read_text())
    validate_native_source(native,validation,scenario)
    shape=reference['classified_water'].shape
    reviewed_paths=(frames[0],frames[-2],frames[-1])
    frame_hashes={p.name:sha(p) for p in reviewed_paths}
    current=frame_loader(frames[-1],shape); previous=frame_loader(frames[-2],shape)
    bed=np.load(inputs/'scenario/bed.npy',allow_pickle=False,mmap_mode='r')
    first=frame_loader(frames[0],shape)
    with np.load(inputs/'scenario/initial_state.npz',allow_pickle=False) as initial:
        validate_native_frame(first,bed,scenario['grid'],initial)
    for frame in (current,previous):validate_native_frame(frame,bed,scenario['grid'])
    dx=scenario['grid']['dx'];dy=scenario['grid']['dy']
    expected_x=np.arange(shape[1])*dx+scenario['grid']['origin_x']
    expected_y=np.arange(shape[0])*dy+scenario['grid']['origin_y']
    if not np.allclose(current['x'],expected_x[None,:]) or not np.allclose(current['y'],expected_y[:,None]):
        raise ValueError('Native frame is in a different grid')
    stats=compare(reference,current,previous,dy)
    flux=face_discharge(solver,inputs/'scenario',current,scratch_parent=out.parent)
    q=scenario['boundaries'][0]['metadata']['target_discharge_m3s']
    stats.update(exact_face_discharge_target_m3s=q,
        exact_face_discharge_inlet_m3s=float(flux[0]),exact_face_discharge_outlet_m3s=float(flux[-1]),
        exact_face_discharge_range_m3s=[float(flux.min()),float(flux.max())],
        exact_face_discharge_abs_error_p95_fraction=float(np.percentile(abs(flux-q)/q,95)))
    gates=screen(stats)
    intervals=[]
    for item in build.get('source_inputs',[]):
        path=ROOT/item['path']/'build_report.json'
        if sha(path)!=item['sha256']:raise ValueError('Changed registered source core')
        intervals.append(json.loads(path.read_text())['source_core_interval_m'])
    cores=core_reviews(reference,current,previous,flux,q,dy,intervals) if intervals else []
    if cores:gates['all_registered_cores_pass']=all(c['construction_screen_passed'] for c in cores)
    report=dict(schema='raftsim.colorado_catalog_cook_review.v1',name=build['name'],
        scope='Construction-screen thresholds only; not engine, boat, rapid-specific, visual, or FPS acceptance.',
        source_profile_flow_cfs_approx=8400,target_flow_cfs=8000,
        comparison_frames=[p.name for p in frames[-2:]],
        frame_sha256=frame_hashes,solver_sha256=sha(solver),
        native_manifest=native,native_validation=validation,statistics=stats,
        registered_core_reviews=cores,
        construction_screen=gates,construction_screen_passed=all(gates.values()),
        engine_validated=False,class_match='not_established')
    for name,digest in build['files_sha256'].items():
        if sha(inputs/name)!=digest:raise ValueError('Solver input changed during review')
    if any(sha(p)!=frame_hashes[p.name] for p in reviewed_paths):
        raise ValueError('Native frame changed during review')
    out.mkdir(parents=True)
    (out/'review.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(name=build['name'],construction_screen=gates,
        statistics={k:v for k,v in stats.items() if not k.endswith('per_station_m') and k!='sampled_reference_station_m'}),indent=2))
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('inputs','cook','solver','out'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();review(a.inputs.resolve(),a.cook.resolve(),a.solver.resolve(),a.out.resolve())
