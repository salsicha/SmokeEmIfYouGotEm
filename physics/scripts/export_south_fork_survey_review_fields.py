"""Export a geographically rigid, complete-grid diagnostic runtime package.

No production route or field is replaced. The current engine must explicitly
replay this MUSCL boundary; falling back to an unrelated initial tank is failure.
"""
from pathlib import Path
import argparse
import hashlib
import json
import sys
import numpy as np

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'physics/src'))
from raftsim.scenario2_5d import read_scenario2_5d_package
from audit_troublemaker_hydraulic_spinup import validated_frame_state
from export_troublemaker_review_fields import validate_solver_manifest
from south_fork_survey_sanity import require_sane_frames


def validate_geometry_source(source, expected_sha, root=ROOT):
    """Accept a diagnostic variant only when its actual geometry matches the cook."""
    from south_fork_geometry_source import geometry_identity
    return geometry_identity(source,root,expected_sha)[0]


def validate_bed_sampling(registration,scenario):
    method=registration.get('bed_sampling','bilinear')
    if method not in ('bilinear','render_triangles','registered_triangles') or method!=scenario.metadata.provenance.get('bed_sampling','bilinear'):
        raise ValueError('Cooked bed sampling metadata disagree')
    return method


def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--run',type=Path,required=True)
    parser.add_argument('--geometry-dir',type=Path,default=ROOT/'physics/data/real_world/south_fork_american_chili_bar/reconstruction_2026_09/troublemaker/geometry_candidate')
    args=parser.parse_args(); work=args.run.resolve()
    if not work.is_relative_to(ROOT/'tmp/south-fork-survey-hydraulics'):
        raise ValueError('Only completed survey diagnostics can be exported')
    registration=json.loads((work/'registration.json').read_text())
    result=json.loads((work/'run_result.json').read_text())
    folder=ROOT/result['output_dir']
    raw_manifest=json.loads((folder/'manifest.json').read_text())
    # Check the whole saved history, not only a final state or a permissive
    # generic native validation flag. A failed half-metre test previously
    # reported "passed" with 3.6 km depth and velocity clamped to 60 m/s.
    sanity=require_sane_frames(folder,raw_manifest)
    frame=folder/raw_manifest['frames'][-1]
    solver=validate_solver_manifest(frame,folder/'manifest.json')
    scenario=read_scenario2_5d_package(next((work/'scenario').iterdir()))
    bed_sampling=validate_bed_sampling(registration,scenario)
    state=validated_frame_state(scenario,np.genfromtxt(frame,delimiter=',',names=True))
    source=args.geometry_dir.resolve()/'manifest.json'
    geometry=validate_geometry_source(source,registration['geometry_sha256'])
    from south_fork_geometry_source import REGISTERED_SCHEMA, require_sampling_kind
    require_sampling_kind(geometry.get('schema')==REGISTERED_SCHEMA,bed_sampling)
    if registration['boundary_mode']!='mixed_characteristic_discharge':
        raise ValueError('Survey replay requires the reviewed prescribed-discharge boundary')
    out=work/'engine_review'; band_dir=out/'median_runnable';band_dir.mkdir(parents=True,exist_ok=True)
    records={}
    for name,array in {'h':state.depth,'u':state.u,'v':state.v,'bed':scenario.bed,'wet_mask':state.wet}.items():
        array=np.ascontiguousarray(array,dtype=np.uint8 if name=='wet_mask' else np.float32)
        path=band_dir/(name+'.npy');np.save(path,array)
        records[name]={'file':path.relative_to(out).as_posix(),'dtype':str(array.dtype),
            'shape':list(array.shape),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
    grid=scenario.grid
    manifest={'schema':'raftsim.cooked_flow_fields.v1','river_id':'south_fork_american_chili_bar',
        'rapid_name':'Troublemaker survey candidate','source_elevation_datum_m':registration['vertical_origin_navd88_m'],
        'all_bands_passed':False,'production_promoted':False,
        'grid':{'nx':grid.nx,'ny':grid.ny,'dx_m':grid.dx,'dy_m':grid.dy,
            'origin_x_m':grid.origin_x,'origin_y_m':grid.origin_y,'layout':'row_major_c_order',
            'crs':'Rigid local Cartesian metres from EPSG:32610; no curved-axis deformation'},
        'bands':[{'band_id':'median_runnable','arrays':records,
            'runtime_boundaries':[b.to_json_dict() for b in scenario.boundaries],
            'validation':{'passed':False,'reason':'engine diagnostic, not full reconstruction acceptance'}}],
        'solver':{key:solver[key] for key in ('solver_mode','flux_scheme','cfl','dry_tolerance',
            'roughness_scale','bed_slope_source_scale','feature_strength_scale','spatial_order',
            'preserve_initial_mass','disable_fixture_calibrations')},
        'review':{'source_geometry_sha256':registration['geometry_sha256'],
            'source_solver_binary_sha256':registration['solver_binary_sha256'],
            'source_bed_sampling':bed_sampling,
            'source_geometry_manifest':source.relative_to(ROOT).as_posix(),
            'frame_sha256':hashlib.sha256(frame.read_bytes()).hexdigest(),
            'source_run':str(work.relative_to(ROOT)),'no_surface_limiter_applied':True,
            'runtime_replays_offline_boundary':True,'photorealism_accepted':False}}
    manifest['review']['saved_frame_sanity']=sanity
    manifest['solver'].update(fixed_dt_s=scenario.fixed_dt,roughness_manning=scenario.roughness,
        runtime_replay_offline_config=True,experimental_west_discharge_m3s=registration['target_discharge_m3s'],
        experimental_west_supercritical_stage=True)
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    direction=np.array(registration['downstream_unit']);left=np.array(registration['left_unit'])
    points=[[float(s),*map(float,direction*s),*map(float,left)] for s in range(-200,201,10)]
    coordinate={'schema':'raftsim.curved_river_coordinate_map.v1',
        'vertical_datum_m':registration['vertical_origin_navd88_m'],'points':points,
        'interpretation':'Rigid rotation only, station is local Cartesian x, not river chainage',
        'origin_utm_m':registration['origin_utm_m'],'production_promoted':False}
    (out/'coordinate_map.json').write_text(json.dumps(coordinate,indent=2),encoding='utf-8')
    x,y=grid.meshgrid()
    # A wet centre is insufficient: the old diagnostic spawn put half the
    # raft on a captured bank. Require navigable depth across a conservative
    # 8-m square enclosing the whole raft, then prefer main-channel discharge.
    radius=int(np.ceil(4/grid.dx))
    minimum=state.depth.copy()
    padded=np.pad(state.depth,radius,mode='constant',constant_values=0)
    for dy in range(2*radius+1):
        for dx in range(2*radius+1):
            minimum=np.minimum(minimum,padded[dy:dy+grid.ny,dx:dx+grid.nx])
    eligible=(minimum>1.0)&(abs(x+60)<12)&(state.u>.5)
    if not eligible.any(): raise ValueError('No full-footprint deep-water start upstream of the review crux')
    score=state.depth*state.u-.1*abs(x+60)
    index=np.argmax(np.where(eligible,score,-np.inf))
    s,l=float(x.ravel()[index]),float(y.ravel()[index]);xy=direction*s+left*l
    start={'cooked_fields_dir':out.relative_to(ROOT).as_posix(),
        'coordinate_map_path':(out/'coordinate_map.json').relative_to(ROOT).as_posix(),
        'location_cm':[float(xy[0]*100),float(xy[1]*100),float((scenario.bed+state.depth).ravel()[index]*100+58)],
        'yaw_degrees':float(np.degrees(np.arctan2(direction[1],direction[0]))),
        'station_lateral_m':[s,l],'window_extent_m':max(grid.nx*grid.dx,grid.ny*grid.dy)+2,
        'minimum_depth_within_4m_square_radius_m':float(minimum.ravel()[index]),
        'source_geometry_sha256':registration['geometry_sha256'],'source_bed_sampling':bed_sampling,'production_promoted':False}
    (out/'engine_start.json').write_text(json.dumps(start,indent=2),encoding='utf-8')
    print(json.dumps(start,indent=2))


if __name__=='__main__':main()
