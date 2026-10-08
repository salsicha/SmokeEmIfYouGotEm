"""Prepare one explicit inflow sensitivity from a verified saved native state.

Changing flow must not silently reconstruct different bathymetry. Keep all
terrain, comparison references, friction, outlet and saved state unchanged.
This is a diagnostic change of boundary condition, not exact continuation,
measured local flow, or a new gameplay setting.
"""
import argparse
import copy
import json
import shutil
from pathlib import Path

import numpy as np

from continue_chilko_corridor_cook import validate_parent
from continue_colorado_catalog_cook import restart_state
from review_chilko_continuous_cook import read_inputs, validate_frame
from review_colorado_catalog_cook import load_frame
from mosaic_lidarbc_crops import sha


def change_inflow(scenario, discharge, name):
    if (not np.isfinite(discharge) or not 0 < discharge <= 500 or
            not isinstance(name, str) or not name or
            name == scenario['metadata']['scenario_id']):
        raise ValueError('Bounded discharge and distinct diagnostic name required')
    if scenario.get('feature_count') != 0 or scenario.get('cascading'):
        raise ValueError('Only unforced constant-flow construction inputs are eligible')
    boundaries = scenario['boundaries']
    if (len(boundaries) != 4 or {b['edge'] for b in boundaries} != {'west','east','north','south'} or
            any(set(b)-{'edge','kind','ghost_cells','metadata','stage'} for b in boundaries)):
        raise ValueError('Four explicit constant boundaries required')
    by_edge = {b['edge']: b for b in boundaries}
    if (by_edge['west']['kind'] != 'discharge_profile' or by_edge['east']['kind'] != 'outflow' or
            any(by_edge[k]['kind'] not in ('bank','wall') for k in ('north','south'))):
        raise ValueError('Single west inflow and east outflow required')
    original = by_edge['west']['metadata']['target_discharge_m3s']
    ghost = np.asarray(by_edge['west']['ghost_cells'],dtype=float)
    ny, spacing = scenario['grid']['ny'], scenario['grid']['dy']
    if (not np.isfinite(original) or not 0 < original <= 500 or discharge == original or
            ghost.shape != (2*ny,4) or not np.isfinite(ghost).all() or
            not np.isfinite(spacing) or spacing <= 0 or np.any(ghost[:,1:3] < 0) or
            np.any(ghost[:,3] != 0) or not np.array_equal(ghost[:ny],ghost[ny:])):
        raise ValueError('Finite identical ghost rows with nonnegative depth and longitudinal flow required')
    actual = float(np.sum(ghost[:ny,1]*ghost[:ny,2])*spacing)
    if not np.isclose(actual,original,atol=1e-8,rtol=1e-10):
        raise ValueError('Original inlet profile disagrees with declared discharge')
    result = copy.deepcopy(scenario)
    inlet = next(b for b in result['boundaries'] if b['edge']=='west')
    changed = ghost.copy(); changed[:,2] *= discharge/original
    inlet['ghost_cells'] = changed.tolist()
    inlet['metadata']['target_discharge_m3s'] = discharge
    result['metadata']['scenario_id'] = name
    result['metadata']['flow_band'] = f'diagnostic_fixed_bed_{discharge:g}m3s'
    provenance = result['metadata']['provenance']
    provenance['target_discharge_m3s'] = discharge
    provenance['flow_source'] = f'{discharge:g} m3/s diagnostic inlet hypothesis; not measured local instantaneous flow'
    receipt = dict(original_inflow_m3s=original,candidate_inflow_m3s=discharge,
        original_scenario_id=scenario['metadata']['scenario_id'],candidate_scenario_id=name,
        terrain_inference_discharge_m3s=provenance['continuous_terrain']['discharge_m3s'],
        scope='Only west ghost longitudinal velocity and its metadata change; same bed, source references, friction, outlet and saved native initial state',
        runtime_promotion_authorized=False,requires_fresh_native_review=True)
    provenance['fixed_bed_flow_sensitivity'] = receipt
    return result,receipt


def prepare(inputs,cook,review,out,discharge):
    inputs,cook,review,out=map(lambda p:Path(p).resolve(),(inputs,cook,review,out))
    if out.exists():raise ValueError('Fresh fixed-bed flow comparison directory required')
    protected={p:sha(p) for p in (review,cook/'manifest.json',cook/'validation.json')}
    build,scenario,_,_,bed,_,hashes=read_inputs(inputs)
    reviewed=json.loads(review.read_text())
    native=json.loads((cook/'manifest.json').read_text())
    validation=json.loads((cook/'validation.json').read_text())
    relative=Path(native['frames'][-1])
    if relative.parent != Path('frames') or relative.suffix != '.csv':raise ValueError('Invalid final frame path')
    frame_path=cook/relative;protected[frame_path]=sha(frame_path)
    validate_parent(reviewed,hashes,scenario,native,validation,relative.name,protected[frame_path])
    frame=load_frame(frame_path,bed.shape);validate_frame(frame,bed,scenario['grid'])
    state=restart_state(frame,bed,scenario['grid'])
    changed,sensitivity=change_inflow(scenario,discharge,out.name.replace('-','_'))
    result=copy.deepcopy(build)
    result['fixed_bed_flow_sensitivity']=dict(sensitivity,source_inputs=str(inputs),
        source_inputs_sha256=hashes,source_review=str(review),source_review_sha256=protected[review],
        frame=str(frame_path),frame_sha256=protected[frame_path],
        source_construction_screen_passed=reviewed['construction_screen_passed'],
        original_initial_diagnostics_are_not_restart_diagnostics=True,
        saved_depth_surface_velocity_momentum_and_wetness_preserved_exactly=True)
    if (any(sha(inputs/name)!=digest for name,digest in hashes.items()) or
            any(sha(path)!=digest for path,digest in protected.items())):
        raise ValueError('Source changed during flow comparison preparation')
    out.mkdir(parents=True)
    unchanged=[]
    for name in hashes:
        if name in ('build_report.json','scenario/scenario.json','scenario/initial_state.npz'):continue
        target=out/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(inputs/name,target)
        if sha(target)!=hashes[name]:raise ValueError('Copied source changed')
        unchanged.append(name)
    np.savez_compressed(out/'scenario/initial_state.npz',**state)
    with np.load(out/'scenario/initial_state.npz',allow_pickle=False) as written:
        for key,value in state.items():np.testing.assert_array_equal(written[key],value)
    result['fixed_bed_flow_sensitivity']['byte_identical_input_files']=unchanged
    (out/'scenario/scenario.json').write_text(json.dumps(changed,indent=2,allow_nan=False)+'\n')
    (out/'build_report.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    return result['fixed_bed_flow_sensitivity']


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for key in ('inputs','cook','review','out'):parser.add_argument('--'+key,type=Path,required=True)
    parser.add_argument('--discharge-m3s',type=float,required=True)
    a=parser.parse_args()
    print(json.dumps(prepare(a.inputs,a.cook,a.review,a.out,a.discharge_m3s),indent=2))
