"""Screen an exact-terrain Chilko cook before native integration, not acceptance.

Reuse the Colorado construction thresholds unchanged. Source water extent and
stage remain inferred references; this is not a bathymetric-survey comparison.
"""
import argparse
import json
from pathlib import Path

import numpy as np
import shapely
from scipy.ndimage import label

from build_colorado_catalog_evidence import sha
from export_colorado_continuous_terrain import LandscapeTriangles
from export_colorado_continuous_runtime import registered_queries
from review_colorado_catalog_cook import compare, load_frame, screen
from native_frame_io import native_frame_paths
from solver_face_discharge import face_discharge
from chilko_native_friction import validate_friction


INPUT_FILES=('build_report.json','coordinate_map.json','reference.npz','scenario/scenario.json',
             'scenario/bed.npy','scenario/initial_state.npz','scenario/features.json','scenario/probes.json')


def validate_source_reference(reference, queries, model):
    """A comparison mask cannot legitimize flooding by changing its own inputs.

    Independently resample the hash-verified source in bounded batches. The
    historic dem2021 key is a storage name, not a claim about acquisition date.
    """
    shape=queries.shape[:-1]
    fields=dict(river='mapped_water',dem2021='source_height_m',source_kind='source_kind',
                ownership_reference='ownership_reference_m',ws_reference_grid='reference_m')
    for key in (*fields,'channel'):
        if key not in reference or reference[key].shape!=shape:
            raise ValueError('Missing or misaligned geographic source reference')
    if any(reference[key].dtype.kind!='b' for key in ('river','channel')):
        raise ValueError('Boolean geographic source masks required')
    # Stored grids are lateral-major. Flattening before batching revisits the
    # entire 56 km source mosaic for each lateral row and thrashes its tile LRU.
    # Keep neighbouring longitudinal columns together without changing queries.
    if queries.ndim==3 and 0<shape[0]<=65536:
        columns=max(1,65536//shape[0])
        selections=((slice(None),slice(start,start+columns)) for start in range(0,shape[1],columns))
    else:
        queries=queries.reshape(-1,2)
        reference={key:reference[key].reshape(-1) for key in (*fields,'channel')}
        selections=(slice(start,start+65536) for start in range(0,len(queries),65536))
    for sl in selections:
        source=model.sample(queries[sl].reshape(-1,2))
        for key,source_key in fields.items():
            if not np.allclose(reference[key][sl].reshape(-1),source[source_key],
                               atol=1e-8,rtol=0,equal_nan=True):
                raise ValueError(f'Geographic source reference changed: {key}')
        channel=source['mapped_water']&(source['source_height_m']<=source['ownership_reference_m']+.25)
        if not np.array_equal(reference['channel'][sl].reshape(-1),channel):
            raise ValueError('Geographic source reference changed: channel')


def verify_terrain_sources(source):
    if 'profile_manifest' in source:
        from chilko_corridor_bed import CorridorBed
        profile = Path(source['profile_manifest'])
        if sha(profile) != source['profile_manifest_sha256']:
            raise ValueError('Changed full-corridor profile')
        manifest = json.loads(profile.read_text())
        depth_spec=source.get('available_channel_depth')
        model = CorridorBed(Path(manifest['source_terrain']['manifest']).parent, profile.parent,
                            source['discharge_m3s'], source['manning_n'],
                            depth_profile=Path(depth_spec['manifest']).parent if depth_spec else None)
        if depth_spec!=model.receipt.get('available_channel_depth'):
            raise ValueError('Changed available-channel depth source')
        if source.get('planform_policy')!=model.receipt.get('planform_policy'):
            raise ValueError('Changed inferred branch planform policy')
        for key in ('profile_manifest_sha256', 'profile_sha256', 'terrain_manifest_sha256',
                    'route_sha256', 'planform_sha256', 'ownership_policy'):
            if source.get(key) != model.receipt[key]:
                raise ValueError('Changed full-corridor source or ownership policy')
        return model
    else:
        for key in ('manifest','grid'):
            if sha(Path(source[key]))!=source[key+'_sha256']:
                raise ValueError('Changed terrain source evidence')


def read_inputs(inputs):
    inputs=Path(inputs).resolve()
    hashes={name:sha(inputs/name) for name in INPUT_FILES}
    build=json.loads((inputs/'build_report.json').read_text())
    scenario=json.loads((inputs/'scenario/scenario.json').read_text())
    mapping=json.loads((inputs/'coordinate_map.json').read_text())
    if scenario['metadata']['river_id']!='chilko_river_bc' or scenario['feature_count']!=0:
        raise ValueError('Expected unforced Chilko construction inputs')
    spec=build['continuous_terrain'];path=Path(spec['manifest'])
    if sha(path)!=spec['manifest_sha256']:raise ValueError('Changed canonical terrain')
    triangles=LandscapeTriangles(path.parent)
    source=triangles.manifest['evidence_source']
    source_model=verify_terrain_sources(source)
    if source_model is not None and source_model.receipt.get('planform_policy'):
        from chilko_corridor_chart import hydraulic_frame
        frame,policy=hydraulic_frame(source_model.line,source_model.receipt['planform_policy'])
        expected=np.c_[frame['station'],frame['xy']-np.asarray(mapping['horizontal_origin_m']),frame['normal']]
        actual=np.asarray(mapping['points'],dtype=float)
        if (build.get('numerical_chart_policy')!=policy or mapping.get('numerical_chart_policy')!=policy or
                actual.shape!=expected.shape or not np.allclose(actual,expected,atol=1e-8,rtol=0)):
            raise ValueError('Corrected geographic source and retained numerical chart disagree')
    station,queries=registered_queries(mapping,triangles.manifest,scenario['grid'])
    bed=np.load(inputs/'scenario/bed.npy',allow_pickle=False)
    native_bed=triangles.sample(queries)
    if not np.isfinite(native_bed).all() or not np.allclose(bed,native_bed,atol=1e-8,rtol=0):
        raise ValueError('Hydraulic bed does not match native terrain triangles')
    with np.load(inputs/'reference.npz',allow_pickle=False) as arrays:ref=dict(arrays)
    if (not np.array_equal(station,ref['station']) or
            not np.allclose(queries,np.stack((ref['world_x'],ref['world_y']),axis=-1),atol=1e-8,rtol=0)):
        raise ValueError('Reference and native geographic positions disagree')
    if build.get('stage_sampling')=='per_cell_exact_source_route_projection_v1':
        if source_model is None or 'ws_reference_grid' not in ref:
            raise ValueError('Missing geographic cell-stage source/reference')
        validate_source_reference(ref,queries,source_model)
        channel=ref['channel']
        expected=np.interp(shapely.line_locate_point(source_model.line,shapely.points(queries[channel])),
                           source_model.station,source_model.surface)
        if (ref['ws_reference_grid'].shape!=bed.shape or
                not np.allclose(ref['ws_reference_grid'][channel],expected,atol=1e-8,rtol=0)):
            raise ValueError('Cell-stage reference differs from its geographic source projection')
    return build,scenario,mapping,triangles,bed,ref,hashes


def validate_native(native,validation,scenario):
    if scenario.get('metadata',{}).get('generator')=='build_chilko_corridor_scenario.py':
        provenance=scenario['metadata']['provenance']
        validate_friction(scenario,provenance['continuous_terrain']['manning_n'])
    expected=dict(solver_mode='finite_volume',boundary_mode='scenario',flux_scheme='hll',spatial_order=2,
        cfl=.2,feature_strength_scale=0,roughness_scale=1,bed_slope_source_scale=1,
        preserve_initial_mass=False,disable_fixture_calibrations=True,experimental_west_discharge_m3s=-1,
        experimental_west_supercritical_stage=False,scenario_id=scenario['metadata']['scenario_id'])
    if any(native.get(k)!=v for k,v in expected.items()):
        raise ValueError('Unreviewed native solver configuration or scenario')
    if (validation.get('passed') is not True or validation.get('finite_state') is not True or
            validation.get('velocity_limit_reached') is not False):
        raise ValueError('Native validation failed')


def validate_frame(frame,bed,grid):
    rows,cols=np.indices(bed.shape)
    if (not np.allclose(frame['x'],grid['origin_x']+cols*grid['dx'],atol=1e-7,rtol=0) or
            not np.allclose(frame['y'],grid['origin_y']+rows*grid['dy'],atol=1e-7,rtol=0) or
            not np.allclose(frame['eta']-frame['h'],bed,atol=1e-6,rtol=0)):
        raise ValueError('Native frame does not match the input grid and bed')


def validate_initial_frame(frame, initial):
    """Bind every state field, including momentum, to the recorded restart."""
    for field,key in [('h','depth'),('eta','eta'),('u','u'),('v','v'),
                      ('hu','hu'),('hv','hv'),('wet','wet')]:
        expected=np.asarray(initial[key]); actual=np.asarray(frame[field])
        if (expected.shape!=actual.shape or not np.isfinite(expected).all()
                or not np.isfinite(actual).all()
                or not np.allclose(actual,expected,atol=1e-6,rtol=0)):
            raise ValueError('Native first frame does not match initial inputs: '+key)


def wet_chart_metric(frame, reference):
    h=np.asarray(frame['h']);k=np.asarray(reference['curvature']);lateral=np.asarray(reference['lateral'])
    if (h.ndim!=2 or k.shape!=(h.shape[1],) or lateral.shape!=(h.shape[0],) or
            not all(np.isfinite(a).all() for a in (h,k,lateral)) or not (h>.05).any()):
        raise ValueError('Finite nonempty hydraulic chart required')
    ratio=1-lateral[:,None]*k[None,:]
    return float(ratio[h>.05].min())


def inlet_outlet_wet_path(frame):
    """Wet columns alone do not establish one uninterrupted water corridor.

    Use face connectivity, matching the native finite-volume grid; diagonally
    touching puddles are not a continuous path. This still is not hull clearance.
    """
    h=np.asarray(frame['h'])
    if h.ndim!=2 or not h.size or not np.isfinite(h).all():
        raise ValueError('Finite nonempty depth grid required for connectivity')
    components,_=label(h>.05)
    shared=np.intersect1d(components[:,0],components[:,-1])
    return bool((shared>0).any())


def review(inputs,cook,solver,out):
    if out.exists():raise ValueError('Fresh review directory required')
    build,scenario,mapping,triangles,bed,ref,hashes=read_inputs(inputs)
    native=json.loads((cook/'manifest.json').read_text())
    validation=json.loads((cook/'validation.json').read_text())
    validate_native(native,validation,scenario)
    # Buffered (.csv) or streamed lossless (.csv.gz) native frames, strictly registered.
    frames=native_frame_paths(cook,native,minimum=3)
    first,current,previous=(load_frame(p,bed.shape) for p in (frames[0],frames[-1],frames[-2]))
    for f in (first,current,previous):validate_frame(f,bed,scenario['grid'])
    with np.load(inputs/'scenario/initial_state.npz',allow_pickle=False) as initial:
        validate_initial_frame(first,initial)
    reference=dict(classified_water=ref['channel'],reference_surface=ref.get('ws_reference_grid',ref['ws_reference']),station=ref['station'])
    stats=compare(reference,current,previous,scenario['grid']['dy'])
    flux=face_discharge(solver,inputs/'scenario',current)
    q=scenario['boundaries'][0]['metadata']['target_discharge_m3s']
    if not np.isfinite(q) or q<=0 or not np.isfinite(flux).all():raise ValueError('Invalid discharge')
    stats.update(exact_face_discharge_target_m3s=q,exact_face_discharge_inlet_m3s=float(flux[0]),
        exact_face_discharge_outlet_m3s=float(flux[-1]),exact_face_discharge_range_m3s=[float(flux.min()),float(flux.max())],
        exact_face_discharge_abs_error_p95_fraction=float(np.percentile(abs(flux-q)/q,95)))
    gates=screen(stats)
    gates['continuous_wet_corridor']=bool((current['h']>.05).any(axis=0).all())
    gates['inlet_to_outlet_wet_path']=inlet_outlet_wet_path(current)
    gates['all_surface_sections_sampled']=stats['surface_sections_missing']==0
    stats['minimum_solved_wet_chart_metric']=wet_chart_metric(current,ref)
    gates['solved_wet_chart_nonfolding']=stats['minimum_solved_wet_chart_metric']>.1
    report=dict(schema='raftsim.chilko_continuous_cook_review.v1',name=scenario['metadata']['scenario_id'],
        scope='Construction screen, not measured-stage, boat, visuals, rapid identity or packaged performance acceptance',
        reference_kind='inferred_dem_surface_and_source_supported_channel',input_files_sha256=hashes,
        comparison_frames=[p.name for p in frames[-2:]],
        frame_sha256={p.name:sha(p) for p in (frames[0],frames[-2],frames[-1])},
        solver_sha256=sha(solver),native_manifest=native,native_validation=validation,
        terrain_manifest_sha256=build['continuous_terrain']['manifest_sha256'],statistics=stats,
        construction_screen=gates,construction_screen_passed=all(gates.values()),
        engine_validated=False,class_match='not_established')
    if any(sha(inputs/name)!=digest for name,digest in hashes.items()):raise ValueError('Inputs changed during review')
    out.mkdir(parents=True)
    (out/'review.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    return report


def checked_cook(inputs,cook,review_path):
    build,scenario,mapping,triangles,bed,ref,hashes=read_inputs(inputs)
    if ('fixed_bed_flow_sensitivity' in build or
            'fixed_bed_flow_sensitivity' in scenario.get('metadata',{}).get('provenance',{})):
        raise ValueError('Diagnostic fixed-bed flow comparison is not a production runtime source')
    receipt=json.loads(review_path.read_text())
    if (receipt.get('schema')!='raftsim.chilko_continuous_cook_review.v1' or
            receipt['name']!=scenario['metadata']['scenario_id'] or receipt['input_files_sha256']!=hashes or
            receipt['terrain_manifest_sha256']!=build['continuous_terrain']['manifest_sha256']):
        raise ValueError('Changed or unrelated reviewed inputs')
    gates=screen(receipt['statistics'])
    if (not receipt.get('construction_screen_passed') or
            not all(receipt['construction_screen'].values()) or
            receipt['construction_screen'].get('continuous_wet_corridor') is not True or
            receipt['construction_screen'].get('all_surface_sections_sampled') is not True or
            receipt['statistics']['surface_sections_missing']!=0 or
            any(receipt['construction_screen'].get(k)!=v for k,v in gates.items()) or not all(gates.values())):
        raise ValueError('Cook did not pass its construction screen')
    native=json.loads((cook/'manifest.json').read_text());validation=json.loads((cook/'validation.json').read_text())
    validate_native(native,validation,scenario)
    if native!=receipt['native_manifest'] or validation!=receipt['native_validation']:
        raise ValueError('Different native cook')
    for name,digest in receipt['frame_sha256'].items():
        if Path(name).name!=name or sha(cook/'frames'/name)!=digest:raise ValueError('Changed reviewed frame')
    frame=load_frame(cook/'frames'/receipt['comparison_frames'][-1],bed.shape)
    validate_frame(frame,bed,scenario['grid'])
    if wet_chart_metric(frame,ref)<=.1:
        raise ValueError('Solved water enters folded numerical coordinates')
    if not (frame['h']>.05).any(axis=0).all():raise ValueError('Dry cross-section interrupts the water corridor')
    if not inlet_outlet_wet_path(frame):raise ValueError('Disconnected wet components interrupt the water corridor')
    return build,receipt,native,scenario,frame,bed


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('inputs','cook','solver','out'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();r=review(*(getattr(a,k).resolve() for k in ('inputs','cook','solver','out')))
    print(json.dumps(dict(construction_screen=r['construction_screen'],statistics={k:v for k,v in r['statistics'].items()
        if k not in ('sampled_reference_station_m','surface_error_per_station_m')}),indent=2))
