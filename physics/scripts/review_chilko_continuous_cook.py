"""Screen an exact-terrain Chilko cook before native integration, not acceptance.

Reuse the Colorado construction thresholds unchanged. Source water extent and
stage remain inferred references; this is not a bathymetric-survey comparison.
"""
import argparse
import json
from pathlib import Path

import numpy as np

from build_colorado_catalog_evidence import sha
from export_colorado_continuous_terrain import LandscapeTriangles
from export_colorado_continuous_runtime import registered_queries
from review_colorado_catalog_cook import compare, load_frame, screen
from solver_face_discharge import face_discharge


INPUT_FILES=('build_report.json','coordinate_map.json','reference.npz','scenario/scenario.json',
             'scenario/bed.npy','scenario/initial_state.npz','scenario/features.json','scenario/probes.json')


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
    for key in ('manifest','grid'):
        if sha(Path(source[key]))!=source[key+'_sha256']:
            raise ValueError('Changed terrain source evidence')
    station,queries=registered_queries(mapping,triangles.manifest,scenario['grid'])
    bed=np.load(inputs/'scenario/bed.npy',allow_pickle=False)
    native_bed=triangles.sample(queries)
    if not np.isfinite(native_bed).all() or not np.allclose(bed,native_bed,atol=1e-8,rtol=0):
        raise ValueError('Hydraulic bed does not match native terrain triangles')
    with np.load(inputs/'reference.npz',allow_pickle=False) as arrays:ref=dict(arrays)
    if (not np.array_equal(station,ref['station']) or
            not np.allclose(queries,np.stack((ref['world_x'],ref['world_y']),axis=-1),atol=1e-8,rtol=0)):
        raise ValueError('Reference and native geographic positions disagree')
    return build,scenario,mapping,triangles,bed,ref,hashes


def validate_native(native,validation,scenario):
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


def review(inputs,cook,solver,out):
    if out.exists():raise ValueError('Fresh review directory required')
    build,scenario,mapping,triangles,bed,ref,hashes=read_inputs(inputs)
    native=json.loads((cook/'manifest.json').read_text())
    validation=json.loads((cook/'validation.json').read_text())
    validate_native(native,validation,scenario)
    frames=sorted((cook/'frames').glob('frame_*.csv'))
    if len(frames)<3 or native['frames']!=['frames/'+p.name for p in frames]:
        raise ValueError('Incomplete native frame collection')
    first,current,previous=(load_frame(p,bed.shape) for p in (frames[0],frames[-1],frames[-2]))
    for f in (first,current,previous):validate_frame(f,bed,scenario['grid'])
    with np.load(inputs/'scenario/initial_state.npz',allow_pickle=False) as initial:
        for field,key in [('h','depth'),('u','u'),('v','v')]:
            if not np.allclose(first[field],initial[key],atol=1e-6,rtol=0):
                raise ValueError('Native first frame does not match initial inputs')
    reference=dict(classified_water=ref['channel'],reference_surface=ref['ws_reference'],station=ref['station'])
    stats=compare(reference,current,previous,scenario['grid']['dy'])
    flux=face_discharge(solver,inputs/'scenario',current)
    q=scenario['boundaries'][0]['metadata']['target_discharge_m3s']
    if not np.isfinite(q) or q<=0 or not np.isfinite(flux).all():raise ValueError('Invalid discharge')
    stats.update(exact_face_discharge_target_m3s=q,exact_face_discharge_inlet_m3s=float(flux[0]),
        exact_face_discharge_outlet_m3s=float(flux[-1]),exact_face_discharge_range_m3s=[float(flux.min()),float(flux.max())],
        exact_face_discharge_abs_error_p95_fraction=float(np.percentile(abs(flux-q)/q,95)))
    gates=screen(stats)
    gates['continuous_wet_corridor']=bool((current['h']>.05).any(axis=0).all())
    gates['all_surface_sections_sampled']=stats['surface_sections_missing']==0
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
    if not (frame['h']>.05).any(axis=0).all():raise ValueError('Dry cross-section interrupts the water corridor')
    return build,receipt,native,scenario,frame,bed


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('inputs','cook','solver','out'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();r=review(*(getattr(a,k).resolve() for k in ('inputs','cook','solver','out')))
    print(json.dumps(dict(construction_screen=r['construction_screen'],statistics={k:v for k,v in r['statistics'].items()
        if k not in ('sampled_reference_station_m','surface_error_per_station_m')}),indent=2))
